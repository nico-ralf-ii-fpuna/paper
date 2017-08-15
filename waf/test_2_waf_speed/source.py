# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Nico Epp and Ralf Funk
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pandas as pd
import pickle
import requests
import time
from .base import TEST_CONFIG
from .. import data_sets


def _get_from_data_server(ds_url: str, req_class: str, req_n: int) -> data_sets.Request:
    print('{:25s} | ds_url {} | req_class {} | req_n {}'.format(
        '_get_from_data_server', ds_url, req_class, req_n))

    t_start = time.perf_counter()

    try:
        resp = requests.get(
            'http://{}:{}/{}/{}/{}'.format(
                TEST_CONFIG['DATA_SERVER_ADDRESS'],
                TEST_CONFIG['DATA_SERVER_PORT'],
                ds_url,
                req_class,
                req_n),
            timeout=TEST_CONFIG['REQ_TIMEOUT'])
    except (requests.ConnectionError, requests.Timeout) as err:
        raise ValueError(err)

    t_end = time.perf_counter()

    print('{:25s} | response code {} in {:5.3f} seconds'.format(
        '_get_from_data_server', resp.status_code, t_end - t_start))

    if not resp.ok:
        raise ValueError('status_code {}'.format(resp.status_code))

    req = pickle.loads(resp.content)
    if not isinstance(req, data_sets.Request):
        raise ValueError('pickled content is of class {}'.format(req.__class__))

    # for use in the destination process
    req.headers['x-proxy-test-ds-url'] = ds_url
    req.headers['x-proxy-test-req-class'] = req_class
    req.headers['x-proxy-test-req-n'] = str(req_n)

    return req


def _send(req: data_sets.Request, address, port) -> int:
    t_start = time.perf_counter()

    try:
        options = {
            'url': 'http://{}:{}{}'.format(address, port, req.url),
            'headers': dict(req.headers),
            'timeout': TEST_CONFIG['REQ_TIMEOUT'],
        }

        if req.method == 'GET':
            options['params'] = dict(req.query_params)
            resp = requests.get(**options)
        else:
            options['data'] = dict(req.body_params)
            resp = requests.post(**options)
    except (requests.ConnectionError, requests.Timeout) as err:
        raise ValueError(err)

    t_end = time.perf_counter()

    print('{:25s} | response code {} in {:5.3f} seconds'.format(
        '_send', resp.status_code, t_end - t_start))

    return resp.status_code


def run_once(address, port) -> pd.DataFrame:
    result_list = []

    for ds_url in data_sets.DS_URL_LIST[TEST_CONFIG['DS_URL_SLICE']]:
        for req_class, req_n_range in TEST_CONFIG['REQ_RANGES']:
            for req_n in req_n_range:
                try:
                    req = _get_from_data_server(ds_url, req_class, req_n)

                    t_start = time.perf_counter()
                    status_code = _send(req, address, port)
                    t_end = time.perf_counter()
                    t = t_end - t_start

                    if status_code == 200:
                        res = 'passed'
                    elif status_code == 403:
                        res = 'blocked'
                    else:
                        raise ValueError('unexpected status_code {}'.format(status_code))
                except ValueError as err:
                    t = 0
                    res = 'with errors'
                    print('{:25s} | {}'.format('run', err))

                result_list.append([ds_url, req_class, req_n, t, res])

    return pd.DataFrame(data=result_list, columns=['ds_url', 'req_class', 'req_n', 't', 'res'])


def run():
    print()
    print('START - no WAF')
    df1 = run_once(TEST_CONFIG['DESTINATION_ADDRESS'], TEST_CONFIG['DESTINATION_PORT'])

    print()
    print('START - with WAF')
    df2 = run_once(TEST_CONFIG['PROXY_ADDRESS'], TEST_CONFIG['PROXY_PORT'])

    for label, df in zip(
            ('no WAF', 'with WAF'),
            (df1, df2),
    ):
        print()
        print('| {:10s} | {:5s} | {:19s} | {:19s} | {:19s} | {:5s} |'.format(
            'label', 'class', 'passed', 'blocked', 'with errors', 'total'))
        for req_class, sub_df in df.groupby('req_class'):
            print('| {:10s} | {:5s} | {} | {} | {} | {:5,d} |'.format(
                label,
                req_class,
                '{:5,d} - {:5.3f} s/req'.format(
                    sub_df.loc[sub_df['res'] == 'passed', :].shape[0],
                    sub_df.loc[sub_df['res'] == 'passed', 't'].mean()),
                '{:5,d} - {:5.3f} s/req'.format(
                    sub_df.loc[sub_df['res'] == 'blocked', :].shape[0],
                    sub_df.loc[sub_df['res'] == 'blocked', 't'].mean()),
                '{:5,d} - {:5.3f} s/req'.format(
                    sub_df.loc[sub_df['res'] == 'with errors', :].shape[0],
                    sub_df.loc[sub_df['res'] == 'with errors', 't'].mean()),
                sub_df.shape[0]))
