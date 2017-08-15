# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Nico Epp and Ralf Funk
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from urllib import parse
from typing import Dict, List


class Request:

    def __init__(self, method: str, url: str, encoding='utf-8', headers_to_exclude=None,
                 params_to_exclude=None):
        self.method = method                # type: str
        self.url = url                      # type: str
        self.label_type = ''                # type: str
        self.label_attack = ''              # type: str
        self.original_str = ''              # type: str
        self._encoding = encoding           # type: str
        self._headers = {}                  # type: Dict[str, str]
        self._query_params = {}             # type: Dict[str, str]
        self._body_params = {}              # type: Dict[str, str]
        self._headers_to_exclude = headers_to_exclude
        self._params_to_exclude = params_to_exclude

    def __str__(self) -> str:
        return '{} {}'.format(self.method, self.url)

    @property
    def label(self) -> str:
        return '{} {}'.format(self.label_type, self.label_attack).strip()

    @property
    def headers(self) -> Dict[str, str]:
        return self._headers

    @headers.setter
    def headers(self, s: str):
        self._headers = _split(s, '\n', ': ', self._headers_to_exclude)

    @property
    def query_params(self) -> Dict[str, str]:
        return self._query_params

    @query_params.setter
    def query_params(self, s: str):
        d = _split(s, '&', '=', self._params_to_exclude)
        self._query_params = {
            k: parse.unquote_plus(v, encoding=self._encoding)
            for k, v in d.items()}

    @property
    def body_params(self) -> Dict[str, str]:
        return self._body_params

    @body_params.setter
    def body_params(self, s: str):
        d = _split(s, '&', '=', self._params_to_exclude)
        self._body_params = {
            k: parse.unquote_plus(v, encoding=self._encoding)
            for k, v in d.items()}

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if (self.method == other.method
                    and self.url == other.url
                    and self.headers == other.headers
                    and self.query_params == other.query_params
                    and self.body_params == other.body_params):
                return True
            return False
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self == other
        return NotImplemented


def _split(input_s: str, sep_1: str, sep_2: str, blacklist: List[str]) -> Dict:
    d = {}

    if input_s:
        for e in input_s.split(sep_1):
            e = e.strip()

            if e:
                try:
                    k, v = e.split(sep_2, maxsplit=1)   # will raise error if sep is not present
                    k = k.strip().lower()               # all keys in lowercase
                    v = v.strip()
                    d[k] = v                    # in case of repeated keys, holds only the last one
                except ValueError:
                    pass

    if blacklist:
        # remove some keys
        for k in blacklist:
            d.pop(k, None)

    return d


def read_and_group_requests(
        selected_endpoint_list: List[str], ds_url_list: List[str], normal_file_names: List[str],
        anomalous_file_names: List[str], read_func) -> Dict:
    d = {}

    # initialize dict with empty lists
    for key in selected_endpoint_list:
        d[key] = {
            'normal': [],
            'anomalous': [],
        }

    # read requests and group them by key
    for label, file_name_list in zip(
            ('normal', 'anomalous'),
            (normal_file_names, anomalous_file_names)
    ):
        for req in read_func(file_name_list):
            key = str(req)
            if key in selected_endpoint_list:
                d[key][label].append(req)

    # replace keys with ds_url
    new_d = {}
    for key, ds_url in zip(selected_endpoint_list, ds_url_list):
        new_d[ds_url] = d[key]

    return new_d


def group_requests(r_list: List[Request], key_func) -> Dict:
    d = {}
    for r in r_list:
        k = key_func(r)
        d.setdefault(k, [])
        d[k].append(r)

    return d
