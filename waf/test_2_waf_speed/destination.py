# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Nico Epp and Ralf Funk
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pickle
import requests
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import List
from .base import TEST_CONFIG
from ..data_sets.base import Request


def _str(req: Request, dict_name: str) -> List[str]:
    d = getattr(req, dict_name)
    return [
        '{}: {}'.format(k, v)
        for k, v in sorted(d.items())]


class RequestHandler(BaseHTTPRequestHandler):

    def _get_from_data_server(self, ds_url: str, req_class: str, req_n: int) -> Request:
        self.log_message('{:25s} | ds_url {} | req_class {} | req_n {}'.format(
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

        self.log_message('{:25s} | response code {} in {:5.3f} seconds'.format(
            '_get_from_data_server',
            resp.status_code,
            t_end - t_start))

        if not resp.ok:
            raise ValueError('status_code {}'.format(resp.status_code))

        req = pickle.loads(resp.content)
        if not isinstance(req, Request):
            raise ValueError('pickled content is of class {}'.format(req.__class__))

        return req

    def _process_req(self):
        self.log_message('{:25s} | START {}'.format('_process_req', '-' * 10))

        # build obtained Request object
        parts = self.path.split('?', maxsplit=1)
        obt_req = Request(method=self.command, url=parts[0])
        obt_req.headers = self.headers.as_string()
        if len(parts) > 1:
            obt_req.query_params = parts[1]
        if self.command == 'POST':
            try:
                body_bytes = self.rfile.read(
                    int(self.headers.get('content-length', 0)))
                obt_req.body_params = body_bytes.decode()
            except ValueError as err:
                self.log_message('{:25s} | {}'.format('_process_req', err))
                self.send_response(400)     # 400: bad request
                self.end_headers()
                return

        # get expected Request object
        try:
            ds_url = obt_req.headers.pop('x-proxy-test-ds-url')
            req_class = obt_req.headers.pop('x-proxy-test-req-class')
            req_n = int(obt_req.headers.pop('x-proxy-test-req-n'))
            exp_req = self._get_from_data_server(ds_url, req_class, req_n)
        except (KeyError, IndexError, ValueError) as err:
            self.log_message('{:25s} | {}'.format('_process_req', err))
            self.send_response(404)
            self.end_headers()
            return

        # this header gives differences
        obt_req.headers.pop('content-length', None)
        exp_req.headers.pop('content-length', None)

        # compare Request objects
        if obt_req == exp_req:
            self.log_message('{:25s} | requests are equal'.format('_process_req'))
        else:
            self.log_message('{:25s} | ERROR requests not equal'.format('_process_req'))

            if obt_req.method != exp_req.method:
                self.log_message('{:25s} | diff method'.format('_process_req'))
                self.log_message('{:25s} | obtained {}'.format('_process_req', obt_req.method))
                self.log_message('{:25s} | expected {}'.format('_process_req', exp_req.method))
            if obt_req.url != exp_req.url:
                self.log_message('{:25s} | diff url'.format('_process_req'))
                self.log_message('{:25s} | obtained {}'.format('_process_req', obt_req.url))
                self.log_message('{:25s} | expected {}'.format('_process_req', exp_req.url))
            if obt_req.headers != exp_req.headers:
                self.log_message('{:25s} | diff headers'.format('_process_req'))
                self.log_message('{:25s} | obtained {:3d} {}'.format(
                    '_process_req', len(obt_req.headers), _str(obt_req, 'headers')))
                self.log_message('{:25s} | expected {:3d} {}'.format(
                    '_process_req', len(exp_req.headers), _str(exp_req, 'headers')))
            if obt_req.query_params != exp_req.query_params:
                self.log_message('{:25s} | diff query_params'.format('_process_req'))
                self.log_message('{:25s} | obtained {:3d} {}'.format(
                    '_process_req', len(obt_req.query_params), _str(obt_req, 'query_params')))
                self.log_message('{:25s} | expected {:3d} {}'.format(
                    '_process_req', len(exp_req.query_params), _str(exp_req, 'query_params')))
            if obt_req.body_params != exp_req.body_params:
                self.log_message('{:25s} | diff body_params'.format('_process_req'))
                self.log_message('{:25s} | obtained {:3d} {}'.format(
                    '_process_req', len(obt_req.body_params), _str(obt_req, 'body_params')))
                self.log_message('{:25s} | expected {:3d} {}'.format(
                    '_process_req', len(exp_req.body_params), _str(exp_req, 'body_params')))

            self.send_response(400)     # 400: bad request
            self.end_headers()
            return

        self.log_message('{:25s} | END {}'.format('_process_req', '-' * 10))
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        self._process_req()

    def do_POST(self):
        self._process_req()


def run():
    httpd = HTTPServer(
        (TEST_CONFIG['DESTINATION_ADDRESS'], TEST_CONFIG['DESTINATION_PORT']),
        RequestHandler)

    print('starting server on {} ...'.format(httpd.server_address))
    httpd.serve_forever()
