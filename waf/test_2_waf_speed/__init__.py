# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Nico Epp and Ralf Funk
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# This module implements a simple speed test for our detection system,
# intended to show the time difference created by the detection
# mechanism.
#
# The test consists of four parts, to be run in separate processes:
#   > 'data_server.py'
#     Serves the test data for the other parts.
#   > 'destination.py'
#     Simulates a web application; its only responsible for checking
#     if the requests get there with all the data with which they
#     left the 'source.py' process.
#   > 'proxy_implementation.py'
#     Receives requests intended for 'destination.py', checks them
#     for anomalies and acts accordingly.
#   > 'source.py'
#     Sends requests to 'destination.py', printing timing statistics
#     at the end.
#
# To run the test, start the 'run' function of each the mentioned files,
# preferably in the given order. Beware that some of them may need a
# short initialization time before the next one can start properly.
#
# The file 'base.py' contains some customizable settings for the test.
