# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Nico Epp and Ralf Funk
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pickle
import re
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from .base import TEST_CONFIG
from .. import data_sets


RE_GET_ALL = '/(c|t)([0-9]{2})/(n|a)/all$'
RE_GET_ONE = '/(c|t)([0-9]{2})/(n|a)/([0-9]*)$'


_in_memory_cache = {}


def _get_request_list(ds_url: str, req_class: str):
    if ds_url not in _in_memory_cache:
        _in_memory_cache[ds_url] = data_sets.get(ds_url)

    normal_list, anomalous_list = _in_memory_cache[ds_url]
    if req_class == 'n':
        req_list = normal_list
    else:
        req_list = anomalous_list

    return req_list


class RequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        match_all = re.match(RE_GET_ALL, self.path)
        match_one = re.match(RE_GET_ONE, self.path)

        if not (match_all or match_one):
            self.send_error(404)
            self.end_headers()
            return

        ds_url = self.path[1:4]
        if ds_url not in data_sets.DS_URL_LIST:
            self.send_error(404)
            self.end_headers()
            return

        req_class = self.path[5:6]
        req_list = _get_request_list(ds_url, req_class)

        if match_all:
            bytes_obj_to_send = pickle.dumps(req_list)
        else:
            try:
                req_n = int(self.path[7:])
                req = req_list[req_n]
                bytes_obj_to_send = pickle.dumps(req)
            except (ValueError, KeyError):
                self.send_error(404)
                self.end_headers()
                return

        self.send_response(200)
        self.end_headers()
        self.wfile.write(bytes_obj_to_send)


def run():
    httpd = HTTPServer(
        (TEST_CONFIG['DATA_SERVER_ADDRESS'], TEST_CONFIG['DATA_SERVER_PORT']),
        RequestHandler)

    print('loading data sets from files ...')
    t_start = time.perf_counter()
    for ds_url in data_sets.DS_URL_LIST:
        _ = _get_request_list(ds_url, 'n')
    t_end = time.perf_counter()
    print('finished loading in {:3.1f} seconds'.format(t_end - t_start))

    print()
    print('starting server on {} ...'.format(httpd.server_address))
    httpd.serve_forever()
