# -*- coding: utf-8 -*-
"""
CSIC 2010 HTTP data sets.
http://www.isi.csic.es/dataset/
"""

# Copyright (C) 2017 Nico Epp and Ralf Funk
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
from typing import Iterable, List
from ...base import BASE_PATH
from ..base import Request, group_requests


_ORIGINAL_FILES_PATH = os.path.join(BASE_PATH, 'data_sets', 'csic', 'original_files')
NORMAL_FILE_NAMES = (
    'normalTrafficTraining.txt',
    'normalTrafficTest.txt',
)
ANOMALOUS_FILE_NAMES = (
    'anomalousTrafficTest.txt',
)
SELECTED_ENDPOINT_LIST = (                              # see comment in function 'print_info'
    'GET /tienda1/miembros/editar.jsp',
    'POST /tienda1/miembros/editar.jsp',
    'GET /tienda1/publico/anadir.jsp',
    'POST /tienda1/publico/anadir.jsp',
    'GET /tienda1/publico/autenticar.jsp',
    'POST /tienda1/publico/autenticar.jsp',
    'GET /tienda1/publico/caracteristicas.jsp',
    'POST /tienda1/publico/caracteristicas.jsp',
    'GET /tienda1/publico/entrar.jsp',
    'POST /tienda1/publico/entrar.jsp',
    'GET /tienda1/publico/pagar.jsp',
    'POST /tienda1/publico/pagar.jsp',
    'GET /tienda1/publico/registro.jsp',
    'POST /tienda1/publico/registro.jsp',
    'GET /tienda1/publico/vaciar.jsp',
    'POST /tienda1/publico/vaciar.jsp',
)
DS_URL_LIST = tuple(
    'c{:02d}'.format(i)
    for i in range(len(SELECTED_ENDPOINT_LIST))
)


def read_requests(file_name_list: Iterable[str]) -> List[Request]:
    r_list = []

    for filename in file_name_list:
        line_group_list = []

        # get strings from file
        try:
            with open(os.path.join(_ORIGINAL_FILES_PATH, filename)) as f:
                line_group = []

                for line in f.readlines():
                    line = line.strip()         # empty lines will also be added

                    if 'http://' in line:
                        if line_group:
                            line_group_list.append(line_group)

                        line_group = [line, ]
                    else:
                        line_group.append(line)

                if line_group:
                    line_group_list.append(line_group)      # append last group
        except FileNotFoundError:
            pass

        # convert strings to requests
        for line_group in line_group_list:
            try:
                # request data
                method, url_and_query_params, _ = line_group[0].split(maxsplit=2)
                parts = url_and_query_params.split('?', maxsplit=1)

                new_r = Request(
                    method=method,
                    url=parts[0].replace('http://localhost:8080', '', 1),
                    encoding='Windows-1252')
                new_r.original_str = '\n'.join(line_group)
                new_r.headers = '\n'.join(line_group[1:-2])
                if len(parts) > 1:
                    new_r.query_params = parts[1]
                new_r.body_params = line_group[-2]

                # request classification
                if filename in NORMAL_FILE_NAMES:
                    new_r.label_type = 'normal'
                else:
                    new_r.label_type = 'anomalous'

                r_list.append(new_r)
            except ValueError:
                pass

    return r_list


def print_info():
    """
    This function gives the following output:
    OBS: only printing urls which have normal and anomalous samples
    -----------------------------------------------------------------------
    #    | url and method                             | normal | anomalous
    -----------------------------------------------------------------------
     883 | GET  /tienda1/miembros/editar.jsp          |  2,000 |     1,362
     884 | POST /tienda1/miembros/editar.jsp          |  2,000 |     1,362
    1217 | GET  /tienda1/publico/anadir.jsp           |  2,000 |     1,380
    1218 | POST /tienda1/publico/anadir.jsp           |  2,000 |     1,380
    1285 | GET  /tienda1/publico/autenticar.jsp       |  2,000 |     1,361
    1286 | POST /tienda1/publico/autenticar.jsp       |  2,000 |     1,361
    1330 | GET  /tienda1/publico/caracteristicas.jsp  |  2,000 |       954
    1331 | POST /tienda1/publico/caracteristicas.jsp  |  2,000 |       954
    1407 | GET  /tienda1/publico/entrar.jsp           |  2,000 |       897
    1408 | POST /tienda1/publico/entrar.jsp           |  2,000 |       897
    1484 | GET  /tienda1/publico/pagar.jsp            |  2,000 |     1,343
    1485 | POST /tienda1/publico/pagar.jsp            |  2,000 |     1,343
    1552 | GET  /tienda1/publico/registro.jsp         |  2,000 |     1,364
    1553 | POST /tienda1/publico/registro.jsp         |  2,000 |     1,364
    1597 | GET  /tienda1/publico/vaciar.jsp           |  2,000 |       919
    1598 | POST /tienda1/publico/vaciar.jsp           |  2,000 |       919
    -----------------------------------------------------------------------
         | SELECTED SAMPLES                           | 32,000 |    19,160
         | TOTAL SAMPLES                              | 72,000 |    25,065
    -----------------------------------------------------------------------
    """
    r_list = read_requests(NORMAL_FILE_NAMES + ANOMALOUS_FILE_NAMES)
    d1 = group_requests(r_list, lambda r: '{} {}'.format(r.url, r.method))

    print()
    print('OBS: only printing urls which have normal and anomalous samples')
    print('-' * 70)
    print('{:4s} | {:41s} | {:6s} | {:9s}'.format(
        '#', 'url and method', 'normal', 'anomalous'))
    print('-' * 70)

    qty_total_normal = 0
    qty_total_anomalous = 0
    qty_selected_normal = 0
    qty_selected_anomalous = 0

    for i, (k, v_list) in enumerate(sorted(d1.items())):
        d2 = group_requests(v_list, lambda r: r.label_type)
        qty_normal = len(d2.get('normal', []))
        qty_anomalous = len(d2.get('anomalous', []))

        if qty_normal > 100 and qty_anomalous > 100:
            qty_selected_normal += qty_normal
            qty_selected_anomalous += qty_anomalous
            url, method = k.split()
            print('{:4d} | {:4s} {:36s} | {:6,d} | {:9,d}'.format(
                i+1, method, url, qty_normal, qty_anomalous))

        qty_total_normal += qty_normal
        qty_total_anomalous += qty_anomalous

    print('-' * 70)
    print('{:4s} | {:41s} | {:6,d} | {:9,d}'.format(
        '', 'SELECTED SAMPLES', qty_selected_normal, qty_selected_anomalous))
    print('{:4s} | {:41s} | {:6,d} | {:9,d}'.format(
        '', 'TOTAL SAMPLES', qty_total_normal, qty_total_anomalous))
    print('-' * 70)
    print()
