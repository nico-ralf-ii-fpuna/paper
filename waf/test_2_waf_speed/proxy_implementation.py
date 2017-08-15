# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Nico Epp and Ralf Funk
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pickle
import requests
import time
import sys
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline, make_union
from sklearn.svm import OneClassSVM
from typing import List
from .base import TEST_CONFIG
from .proxy import CherryProxy
from .. import data_sets, feature_extraction


TF_LIST = tuple(
    tf
    for tf in feature_extraction.NUMBERS_TF_LIST
    if issubclass(tf, feature_extraction.base.KeyTransformer))      # only key-tf, original_str is difficult to get
RANDOM_STATE = 2
TRAIN_SIZE = 500
NU = 0.01
GAMMA = 0.01


class FilteringProxy(CherryProxy):

    def __init__(self, do_detection, do_blocking, **kwargs):
        super().__init__(**kwargs)
        self._do_detection = do_detection
        self._do_blocking = do_blocking
        self._detection_models = {}

    def _get_from_data_server(self, ds_url: str, req_class: str) -> List[data_sets.Request]:
        self.log_debug('_get_from_data_server', 'ds_url {} | req_class {}'.format(
            ds_url, req_class))

        t_start = time.perf_counter()

        try:
            resp = requests.get(
                'http://{}:{}/{}/{}/all'.format(
                    TEST_CONFIG['DATA_SERVER_ADDRESS'],
                    TEST_CONFIG['DATA_SERVER_PORT'],
                    ds_url,
                    req_class),
                timeout=TEST_CONFIG['REQ_TIMEOUT'])
        except (requests.ConnectionError, requests.Timeout) as err:
            raise ValueError(err)

        t_end = time.perf_counter()

        self.log_debug('_get_from_data_server', 'response code {} in {:5.3f} seconds'.format(
            resp.status_code, t_end - t_start))

        if not resp.ok:
            raise ValueError('status_code {}'.format(resp.status_code))

        req_list = pickle.loads(resp.content)
        if not isinstance(req_list, [].__class__):
            raise ValueError('pickled content is of class {}'.format(req_list.__class__))

        return req_list

    def _load_detection_models(self):
        self._detection_models = {}

        for ds_url in data_sets.DS_URL_LIST[TEST_CONFIG['DS_URL_SLICE']]:
            try:
                normal_list = self._get_from_data_server(ds_url, 'n')
            except ValueError as err:
                self.log_debug('_load_detection_models', 'could not get req_list "{}": {}'.format(
                    ds_url, err))
                return

            train_list, _ = train_test_split(
                normal_list,
                random_state=RANDOM_STATE,
                train_size=TRAIN_SIZE)

            clf = make_pipeline(
                make_union(*[class_() for class_ in TF_LIST]),
                OneClassSVM(random_state=0, nu=NU, gamma=GAMMA))
            clf.fit(train_list)

            key = str(normal_list[0])
            self._detection_models[key] = clf
            self.log_debug('_load_detection_models', 'loaded "{}"'.format(key))

    def start(self):
        if self._do_detection:
            self.log('Loading {} detection models ...'.format(
                len(data_sets.DS_URL_LIST[TEST_CONFIG['DS_URL_SLICE']])))
            self._load_detection_models()
            self.log('{} detection models loaded.'.format(len(self._detection_models)))
        else:
            self.log('Filtering is OFF.')

        super().start()

    def filter_request(self):
        if not self._do_detection:
            self.log_debug('filter_request', 'filtering is OFF')
            return

        # build obtained Request object
        obt_req = data_sets.Request(method=self.req.method, url=self.req.path)
        obt_req._headers = dict(self.req.headers)
        obt_req.query_params = self.req.query
        if self.req.data:
            obt_req.body_params = self.req.data.decode()

        # remove headers that are there only for this test
        obt_req.headers.pop('x-proxy-test-ds-url', None)
        obt_req.headers.pop('x-proxy-test-req-class', None)
        obt_req.headers.pop('x-proxy-test-req-n', None)

        key = str(obt_req)
        self.log_debug('filter_request', 'do filtering for key "{}"'.format(key))

        if key not in self._detection_models:
            # let the request pass, no blocking because there is no detection model
            self.log_debug('filter_request', 'no detection model found')
            return

        clf = self._detection_models[key]
        y = clf.predict(obt_req)
        self.log_debug('filter_request', 'prediction {}'.format(y))

        if y[0] == -1:
            if self._do_blocking:
                self.log_debug('filter_request', 'request blocked')
                self.set_response_forbidden()
            else:
                self.log_debug('filter_request', 'blocking is OFF')


def run():
    proxy_options = {
        'listen_address': TEST_CONFIG['PROXY_ADDRESS'],
        'listen_port': TEST_CONFIG['PROXY_PORT'],
        'redirect_address': TEST_CONFIG['DESTINATION_ADDRESS'],
        'redirect_port': TEST_CONFIG['DESTINATION_PORT'],
        'verbosity': TEST_CONFIG['PROXY_VERBOSITY'],
        'do_detection': TEST_CONFIG['DO_DETECTION'],
        'do_blocking': TEST_CONFIG['DO_BLOCKING'],
    }
    proxy = FilteringProxy(**proxy_options)

    while True:
        try:
            proxy.start()
        except KeyboardInterrupt:
            proxy.stop()
            sys.exit()
