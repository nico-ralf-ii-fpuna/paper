# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Nico Epp and Ralf Funk
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
from waf import test_1_detection
from waf import test_3_training_time
from waf.test_2_waf_speed import data_server
from waf.test_2_waf_speed import destination
from waf.test_2_waf_speed import proxy_implementation
from waf.test_2_waf_speed import source

AVAILABLE_COMMANDS = '''{}

Available commands are: 
    test1
    test2 dataserver
    test2 destination
    test2 proxy
    test2 source
    test3
'''

USAGE = AVAILABLE_COMMANDS.format('Usage: python run.py COMMAND')
FALSE_CMD = AVAILABLE_COMMANDS.format('"{}" is not an available command')


def run():
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test1':
            test_1_detection.run()
        elif sys.argv[1] == 'test2':
            if sys.argv[2] == 'dataserver':
                data_server.run()
            elif sys.argv[2] == 'destination':
                destination.run()
            elif sys.argv[2] == 'proxy':
                proxy_implementation.run()
            elif sys.argv[2] == 'source':
                source.run()
            else:
                print(FALSE_CMD.format('test2 ' + sys.argv[2]))
        elif sys.argv[1] == 'test3':
            test_3_training_time.run()
        elif sys.argv[1] == '-h' or sys.argv[1] == '--help':
            print(USAGE)
        else:
            print(FALSE_CMD.format(sys.argv[1]))
    else:
        print(USAGE)


if __name__ == '__main__':
    sys.path.extend(os.path.dirname(os.path.realpath(__file__)))
    run()