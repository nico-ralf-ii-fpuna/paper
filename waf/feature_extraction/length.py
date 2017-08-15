# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Nico Epp and Ralf Funk
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from typing import List
from . import base


_COUNTER_FUNCTION_NAMES = (
    'ALL',
    'DIGIT',
    'ALPHA',
    'OTHER',
)
_COUNTER_FUNCTIONS = (
     lambda s: len(s),
     lambda s: len(list(filter(lambda x: x.isdigit(), s))),
     lambda s: len(list(filter(lambda x: x.isalpha(), s))),
     lambda s: len(list(filter(lambda x: not (x.isdigit() or x.isalpha()), s))),
)


class _LengthMixin:

    @staticmethod
    def _get_features_per_key() -> List[str]:
        return _COUNTER_FUNCTION_NAMES

    @staticmethod
    def _evaluate(v: str) -> List[float]:
        """
        Calculates various lengths.
        """
        result_list = []

        for func in _COUNTER_FUNCTIONS:
            result_list.append(
                func(v))

        return result_list


class HeLengthTransformer(
        _LengthMixin,
        base.HeaderMixin,
        base.KeyTransformer):
    pass


class QpLengthTransformer(
        _LengthMixin,
        base.QueryParamMixin,
        base.KeyTransformer):
    pass


class BpLengthTransformer(
        _LengthMixin,
        base.BodyParamMixin,
        base.KeyTransformer):
    pass


class RqLengthTransformer(
        _LengthMixin,
        base.ReqTransformer):
    pass
