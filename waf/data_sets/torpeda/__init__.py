# -*- coding: utf-8 -*-
"""
Torpeda 2012 HTTP data sets.
http://www.tic.itefi.csic.es/torpeda/datasets.html
"""

# Copyright (C) 2017 Nico Epp and Ralf Funk
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
from xml.etree import cElementTree as ElementTree
from xml.etree.ElementTree import ParseError
from typing import Iterable, List
from ...base import BASE_PATH
from ..base import Request, group_requests


_ORIGINAL_FILES_PATH = os.path.join(BASE_PATH, 'data_sets', 'torpeda', 'original_files')
NORMAL_FILE_NAMES = (
    'allNormals1.xml',
)
ANOMALOUS_FILE_NAMES = (
    'allAnomalies1.xml',
    'allAnomalies2.xml',
    'allAttacks1.xml',
    'allAttacks2.xml',
    'allAttacks3.xml',
    'allAttacks4.xml',
    'allAttacks5.xml',
)
SELECTED_ENDPOINT_LIST = (                              # see comment in function 'print_info'
    'POST /tienda1/miembros/editar.jsp',
    'POST /tienda1/publico/registro.jsp',
)
DS_URL_LIST = tuple(
    't{:02d}'.format(i)
    for i in range(len(SELECTED_ENDPOINT_LIST))
)


def read_requests(file_name_list: Iterable[str]) -> List[Request]:
    r_list = []

    for filename in file_name_list:
        try:
            tree = ElementTree.parse(os.path.join(_ORIGINAL_FILES_PATH, filename))
            for sample in tree.getroot():
                # request data
                r_elem = sample.find('request')
                new_r = Request(
                    method=r_elem.find('method').text,
                    url=r_elem.find('path').text,
                    encoding='Windows-1252',
                    params_to_exclude=('ntc', ))    # param 'ntc' is the same in all normal samples
                new_r.original_str = '\n'.join(s.strip() for s in r_elem.itertext())

                e = r_elem.find('headers')
                if e is not None:
                    new_r.headers = e.text

                e = r_elem.find('query')
                if e is not None:
                    new_r.query_params = e.text

                e = r_elem.find('body')
                if e is not None:
                    new_r.body_params = e.text

                # request classification
                l_elem = sample.find('label')
                new_r.label_type = l_elem.find('type').text
                if new_r.label_type == 'attack':
                    new_r.label_attack = l_elem.find('attack').text

                r_list.append(new_r)
        except (FileNotFoundError, ParseError):
            pass

    return r_list


def print_info():
    """
    This function gives the following output:
    OBS: only printing urls which have normal and anomalous samples
    -------------------------------------------------------------------------------
    #    | url and method                            | normal | anomalous | attack
    -------------------------------------------------------------------------------
      35 | POST /tienda1/miembros/editar.jsp         |  5,608 |     8,090 |  2,031
      68 | POST /tienda1/publico/registro.jsp        |  2,522 |     8,145 |  5,018
    -------------------------------------------------------------------------------
         | SELECTED SAMPLES                          |  8,130 |    16,235 |  7,049
         | TOTAL SAMPLES                             |  8,363 |    16,459 | 49,311
    -------------------------------------------------------------------------------
    """
    r_list = read_requests(NORMAL_FILE_NAMES + ANOMALOUS_FILE_NAMES)
    d1 = group_requests(r_list, lambda r: '{} {}'.format(r.url, r.method))

    print()
    print('OBS: only printing urls which have normal and anomalous samples')
    print('-' * 79)
    print('{:4s} | {:41s} | {:6s} | {:9s} | {:6s}'.format(
        '#', 'url and method', 'normal', 'anomalous', 'attack'))
    print('-' * 79)

    qty_total_normal = 0
    qty_total_anomalous = 0
    qty_total_attack = 0
    qty_selected_normal = 0
    qty_selected_anomalous = 0
    qty_selected_attack = 0

    for i, (k, v_list) in enumerate(sorted(d1.items())):
        d2 = group_requests(v_list, lambda r: r.label_type)
        qty_normal = len(d2.get('normal', []))
        qty_anomalous = len(d2.get('anomalous', []))
        qty_attack = len(d2.get('attack', []))

        if qty_normal > 100 and (qty_anomalous > 100 or qty_attack > 100):
            qty_selected_normal += qty_normal
            qty_selected_anomalous += qty_anomalous
            qty_selected_attack += qty_attack
            url, method = k.split()
            print('{:4d} | {:4s} {:36s} | {:6,d} | {:9,d} | {:6,d}'.format(
                i+1, method, url, qty_normal, qty_anomalous, qty_attack))

        qty_total_normal += qty_normal
        qty_total_anomalous += qty_anomalous
        qty_total_attack += qty_attack

    print('-' * 79)
    print('{:4s} | {:41s} | {:6,d} | {:9,d} | {:6,d}'.format(
        '', 'SELECTED SAMPLES', qty_selected_normal, qty_selected_anomalous, qty_selected_attack))
    print('{:4s} | {:41s} | {:6,d} | {:9,d} | {:6,d}'.format(
        '', 'TOTAL SAMPLES', qty_total_normal, qty_total_anomalous, qty_total_attack))
    print('-' * 79)
    print()
