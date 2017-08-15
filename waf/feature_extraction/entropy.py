# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Nico Epp and Ralf Funk
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import collections
import math
from typing import List
from . import base


class _EntropyMixin:

    @staticmethod
    def _evaluate(v: str) -> List[float]:
        """
        Calculates the Shannon entropy of the string.
        Source: https://www.reddit.com/r/dailyprogrammer/comments/4fc896/20160418_challenge_263_easy_calculating_shannon/d27n7xh/
        """
        entropy = (-1) * sum(
            i / len(v) * math.log2(i / len(v))
            for i in collections.Counter(v).values())

        return [entropy, ]


class HeEntropyTransformer(
        _EntropyMixin,
        base.HeaderMixin,
        base.KeyTransformer):
    pass


class QpEntropyTransformer(
        _EntropyMixin,
        base.QueryParamMixin,
        base.KeyTransformer):
    pass


class BpEntropyTransformer(
        _EntropyMixin,
        base.BodyParamMixin,
        base.KeyTransformer):
    pass


class RqEntropyTransformer(
        _EntropyMixin,
        base.ReqTransformer):
    pass
