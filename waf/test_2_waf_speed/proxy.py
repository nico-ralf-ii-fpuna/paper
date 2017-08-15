# -*- coding: utf-8 -*-
"""
CherryProxy

a lightweight HTTP proxy based on the CherryPy WSGI server and httplib,
extensible for content analysis and filtering.

ORIGINAL AUTHOR: Philippe Lagadec (decalage at laposte dot net)
MODIFIED BY: Nico Epp and Ralf Funk

PROJECT WEBSITE: http://www.decalage.info/python/cherryproxy

LICENSE:

Copyright (c) 2008-2011, Philippe Lagadec (decalage at laposte dot net)
Copyright (C) 2017 Nico Epp and Ralf Funk

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above copyright
notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.
"""

# Copyright (C) 2017 Nico Epp and Ralf Funk
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import threading
import time
import sys
from http import client
from urllib import parse
from cherrypy.wsgiserver import CherryPyWSGIServer


# supported methods and schemes
ALLOWED_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD']
ALLOWED_SCHEMES = ['http']


class CherryProxy:
    """
    CherryProxy: a filtering HTTP proxy.
    """

    # class variables: unique id for each request
    _req_id = 0
    _lock_req_id = threading.Lock()

    def __init__(self, listen_address, listen_port, redirect_address, redirect_port, verbosity,
                 log_stream=sys.stdout):
        self.listen_address = listen_address
        self.listen_port = listen_port
        self.redirect_address = redirect_address
        self.redirect_port = redirect_port
        self._verbosity = verbosity
        self._log_stream = log_stream

        # thread local variables to store request/response data per thread:
        self.req = threading.local()
        self.resp = threading.local()

        self.server = CherryPyWSGIServer(
            (self.listen_address, self.listen_port), self._proxy_app)
        self.log_debug('__init__', 'server.bind_addr: {}'.format(self.server.bind_addr))

    def log(self, s, prefix='### ', req_id=None):
        if self._verbosity > 0:
            if req_id:
                prefix += '{:06} | '.format(req_id)
            self._log_stream.write('{}{}\n'.format(prefix, s))

    def log_debug(self, method_name, s):
        if self._verbosity > 1:
            options = {
                's': '{:25s} | {}'.format(method_name, s),
                'prefix': '*** ',
            }
            if hasattr(self.req, 'id'):
                options['req_id'] = self.req.id
            self.log(**options)

    def start(self):
        self.log('Starting proxy to listen on {} and redirect to {}'.format(
            self.server.bind_addr, (self.redirect_address, self.redirect_port)))
        self.log('Proxy listening ... (press Ctrl+C to stop)'.format(self.server.bind_addr))
        self.server.start()

    def stop(self):
        self.server.stop()
        self.log('Proxy stopped.')

    def set_response(self, status, reason=None, data=None, content_type='text/plain'):
        """
        Set a HTTP response to be sent to the client instead of the one from the server.
        :param status: int, HTTP status code (see RFC 2616)
        :param reason: str, optional text for the response line, standard text by default
        :param data: str, optional body for the response, default="status reason"
        :param content_type: str, content-type corresponding to data
        :return:
        """
        self.resp.status = status

        if not reason:
            reason = client.responses[status]       # get standard text corresponding to status
        self.resp.reason = reason

        if not data:
            data = '{} {}'.format(status, reason)
        self.resp.data = data

        # reset all headers
        self.resp.headers = []
        self.resp.headers.append(('content-type', content_type))
        # self.resp.headers.append(('content-length', str(len(data))))

    def set_response_forbidden(self):
        self.set_response(403, reason='Forbidden')

    def filter_request_headers(self):
        """
        Method to be overridden:
        Called to analyse/filter/modify the request received from the client,
        before reading the full request with its body if there is one,
        before it is sent to the server.

        This method may call set_response() if the request needs to be blocked
        before being sent to the server.

        The following attributes can be read and MODIFIED:
            self.req.headers: dictionary of HTTP headers, with lowercase names
            self.req.method: HTTP method, e.g. 'GET', 'POST', etc
            self.req.scheme: protocol from URL, e.g. 'http' or 'https'
            self.req.path: path in URL, for example '/folder/index.html'
            self.req.query: query string, found after question mark in URL

        The following attributes can be READ only:
            self.req.environ: dictionary of request attributes following WSGI format (PEP 333)
            self.req.url: partial URL containing 'path?query'
            self.req.content_type: content-type, for example 'text/html'
            self.req.charset: charset, for example 'UTF-8'
            self.req.length: length of request data in bytes, 0 if none
        """
        pass

    def filter_request(self):
        """
        Method to be overridden:
        Called to analyse/filter/modify the request received from the client,
        after reading the full request with its body if there is one,
        before it is sent to the server.

        This method may call set_response() if the request needs to be blocked
        before being sent to the server.

        The same attributes as in filter_request_headers are available:

        The following attributes can also be read and MODIFIED:
            self.req.data: data sent with the request (POST or PUT)
        """
        pass

    def filter_response_headers(self):
        """
        Method to be overridden:
        Called to analyse/filter/modify the response received from the server,
        before reading the full response with its body if there is one,
        before it is sent back to the client.

        This method may call set_response() if the response needs to be blocked
        (e.g. replaced by a simple response) before being sent to the client.

        The following attributes can be read and MODIFIED:
            self.resp.status: int, HTTP status of response, e.g. 200, 404, etc
            self.resp.reason: reason string, e.g. 'OK', 'Not Found', etc
            self.resp.headers: response headers, list of (header, value) tuples

        The following attributes can be READ only:
            self.resp.httpconn: httplib.HTTPConnection object
            self.resp.response: httplib.HTTPResponse object
            self.resp.content_type: content-type of response
        """
        pass

    def filter_response(self):
        """
        Method to be overridden:
        Called to analyse/filter/modify the response received from the server,
        after reading the full response with its body if there is one,
        before it is sent back to the client.

        This method may call set_response() if the response needs to be blocked
        (e.g. replaced by a simple response) before being sent to the client.

        The same attributes as in filter_response_headers are available:

        The following attributes can be read and MODIFIED:
            self.resp.data: data sent with the response
        """
        pass

    def _proxy_app(self, environ, f_start_response):
        """
        Main method called when a request is received from a client (WSGI application).
        :param environ:
        :param f_start_response:
        :return:
        """
        t_start = time.perf_counter()
        self._init_request_response()
        self.log('START', req_id=self.req.id)

        self._parse_request(environ)

        # method to be overridden by subclass: filter request headers before reading the body
        self.filter_request_headers()

        if not self.resp.status:
            self._read_request_body()

            # method to be overridden by subclass: filter request before sending it to the server
            self.filter_request()

        self.log('request {} {}'.format(self.req.method, self.req.url), req_id=self.req.id)

        if not self.resp.status:
            self._send_request()
            self._parse_response()

            # method to be overridden by subclass: filter response headers before reading the body
            self.filter_response_headers()

        if not self.resp.data:          # here we need to check resp.data
            self._read_response_body()

            # method to be overridden by subclass: filter request before sending it to the client
            self.filter_response()

        # for now we always close the connection, even if the client sends several requests;
        # this is not optimal performance-wise, but simpler to code
        if self.resp.httpconn:
            self.resp.httpconn.close()

        self._send_response(f_start_response)

        t_end = time.perf_counter()
        self.log('response {} {} in {:5.3f} seconds'.format(
            self.resp.status, self.resp.reason, t_end - t_start), req_id=self.req.id)
        return [self.resp.data]

    def _init_request_response(self):
        # set request id (simply increase number at each request)
        with self._lock_req_id:
            self._req_id += 1
            self.req.id = self._req_id

        # request variables
        self.req.environ = {}
        self.req.headers = {}
        self.req.method = None
        self.req.scheme = None
        self.req.path = None
        self.req.query = None
        self.req.url = None
        self.req.content_type = None
        self.req.charset = None
        self.req.length = 0
        self.req.data = None

        # response variables
        self.resp.httpconn = None
        self.resp.response = None
        self.resp.status = None
        self.resp.reason = None
        self.resp.headers = []          # http.client headers is a list of (header, value) tuples
        self.resp.content_type = None
        self.resp.data = None

    def _parse_request(self, environ):
        self.req.environ = environ
        self.log_debug('_parse_request', 'req.environ:')
        for k, v in sorted(environ.items(), key=lambda x: x[0]):
            self.log_debug('_parse_request', '   {}: {}'.format(k, v))

        # convert WSGI environ to a dict of HTTP headers:
        self.req.headers = {}
        for h in environ:
            if h.startswith('HTTP_'):
                self.req.headers[h[5:].replace('_', '-').lower()] = environ[h]

        # content-type is stored without 'HTTP_'
        # see RFC 2616: http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.17
        content_type = environ.get('CONTENT_TYPE', None)
        if content_type:
            if ';' in content_type:
                content_type, charset = content_type.split(';', 1)
                self.req.content_type = content_type.strip()
                self.req.charset = charset.strip()
                ct = '{};{}'.format(self.req.content_type, self.req.charset)
            else:
                self.req.content_type = content_type.strip()
                ct = self.req.content_type
            self.req.headers['content-type'] = ct
        self.log_debug('_parse_request', 'req.content_type: {}'.format(self.req.content_type))
        self.log_debug('_parse_request', 'req.charset: {}'.format(self.req.charset))

        # content-length is also stored without 'HTTP_'
        self.req.headers['content-length'] = environ.get('CONTENT_LENGTH', 0)
        self.log_debug('_parse_request', 'req.headers:')
        for k, v in sorted(self.req.headers.items(), key=lambda x: x[0]):
            self.log_debug('_parse_request', '   {}: {}'.format(k, v))

        self.req.method = environ.get('REQUEST_METHOD', None)
        self.req.scheme = environ.get('wsgi.url_scheme', None)      # http
        self.req.path = environ.get('PATH_INFO', None)
        self.req.query = environ.get('QUERY_STRING', None)
        self.req.url = parse.urlunsplit(('', '', self.req.path, self.req.query, ''))
        self.log_debug('_parse_request', 'req.method: {}'.format(self.req.method))
        self.log_debug('_parse_request', 'req.scheme: {}'.format(self.req.scheme))
        self.log_debug('_parse_request', 'req.path: {}'.format(self.req.path))
        self.log_debug('_parse_request', 'req.query: {}'.format(self.req.query))
        self.log_debug('_parse_request', 'req.url: {}'.format(self.req.url))

        if self.req.method not in ALLOWED_METHODS:
            # here I use 501 "not implemented" rather than 405 or 401, because it seems to be the
            # most appropriate response according to RFC 2616.
            # see http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
            msg = 'Method "{}" not supported.'.format(self.req.method)
            self.set_response(501, reason=msg)
            self.log_debug('_parse_request', msg)

        if self.req.scheme not in ALLOWED_SCHEMES:
            msg = 'Scheme "{}" not supported.'.format(self.req.scheme)
            self.set_response(501, reason=msg)
            self.log_debug('_parse_request', msg)

    def _read_request_body(self):
        try:
            length = int(self.req.environ.get('CONTENT_LENGTH', 0))
        except ValueError:
            length = 0

        if length > 0:
            self.req.length = length
            input_ = self.req.environ.get('wsgi.input')
            if input_:
                self.req.data = input_.read(self.req.length)
                self.log_debug('_read_request_body', 'req.length: {}'.format(self.req.length))
                self.log_debug('_read_request_body', 'req.data: {} b'.format(len(self.req.data)))
                return

        self.log_debug('_read_request_body', 'No request body')

    def _send_request(self):
        self.log_debug('_send_request', 'starting')

        # forward a request received from a client to the server.
        # TO DO: handle connection errors
        self.resp.httpconn = client.HTTPConnection(self.redirect_address, self.redirect_port)
        self.log_debug('_send_request', 'initialized connection')

        self.resp.httpconn.request(
            self.req.method, self.req.url, body=self.req.data, headers=self.req.headers)
        self.log_debug('_send_request', 'made request')

        # Get the response (but not the response body yet).
        self.resp.response = self.resp.httpconn.getresponse()
        self.log_debug('_send_request', 'got response')

    def _parse_response(self):
        self.resp.status = self.resp.response.status
        self.resp.reason = self.resp.response.reason
        self.log_debug('_parse_response', 'resp: {} {}'.format(self.resp.status, self.resp.reason))

        self.resp.headers = self.resp.response.getheaders()
        self.log_debug('_parse_response', 'resp.headers:')
        for e in sorted(self.resp.headers):
            self.log_debug('_parse_response', '   {}: {}'.format(e[0], e[1]))

        self.resp.content_type = self.resp.response.msg.get_content_type().lower()
        self.log_debug('_parse_response', 'resp.content_type: {}'.format(self.resp.content_type))

    def _read_response_body(self):
        # TO DO: check content-length?
        self.resp.data = self.resp.response.read()
        self.log_debug('_read_response_body', 'resp.data: {} b'.format(len(self.resp.data)))

    def _send_response(self, f_start_response):
        # Send the response with headers (but no body yet).
        status = '{} {}'.format(self.resp.status, self.resp.reason)
        f_start_response(status, self.resp.headers)
        self.log_debug('_send_response', 'status: {}'.format(status))
