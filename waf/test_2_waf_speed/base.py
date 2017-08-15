# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Nico Epp and Ralf Funk
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


TEST_CONFIG = {
    'DATA_SERVER_ADDRESS': 'localhost',
    'DATA_SERVER_PORT': 8800,
    'PROXY_ADDRESS': 'localhost',
    'PROXY_PORT': 8801,
    'PROXY_VERBOSITY': 1,
    'DESTINATION_ADDRESS': 'localhost',
    'DESTINATION_PORT': 8802,
    'REQ_TIMEOUT': 10,
    'DS_URL_SLICE': slice(16),  # exclude TORPEDA data because it has the same URLs as CSIC
    'REQ_RANGES': (
        ('n', range(2)),
        ('a', range(2)),
    ),
    'DO_DETECTION': True,
    'DO_BLOCKING': False,
}
