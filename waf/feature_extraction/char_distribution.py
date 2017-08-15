# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Nico Epp and Ralf Funk
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from typing import List, Tuple
from . import base


_MAX_CHAR_LENGTH = 256                          # type: int
_BIN_SIZES = (1, 2, 3, 4, _MAX_CHAR_LENGTH)     # type: Tuple[int]
_NUM_BINS = len(_BIN_SIZES)                     # type: int
_N_GRAM_SIZES = (1, )                           # type: Tuple[int]


class _CharDisMixin:

    @staticmethod
    def _get_features_per_key() -> List[str]:
        return ['N{}B{}'.format(n, i)
                for n in _N_GRAM_SIZES
                for i in range(_NUM_BINS)]

    @staticmethod
    def _evaluate(v: str) -> List[float]:
        """
        Calculates the character distribution of a string.
        """
        result_list = []

        for n in _N_GRAM_SIZES:
            result_list.extend(
                _get_bins(n, v))

        return result_list


def _get_bins(n_gram_size: int, value: str) -> List[float]:
    """
    Returns a list of bins containing the character distribution of the value.
    """
    d = {}
    for i in range(len(value) - n_gram_size + 1):
        sub = value[i:i + n_gram_size]
        d.setdefault(sub, 0)
        d[sub] += 1
    char_distribution = list(sorted(d.values(), reverse=True))

    # normalize
    total = sum(char_distribution)
    char_distribution = [e/total for e in char_distribution]

    # sum the char distribution probabilities for each bin
    bins = []
    j = 0
    for e in _BIN_SIZES:
        i = j
        j += e
        bins.append(sum(char_distribution[i:j]))

    return bins


class HeCharDisTransformer(
        _CharDisMixin,
        base.HeaderMixin,
        base.KeyTransformer):
    pass


class QpCharDisTransformer(
        _CharDisMixin,
        base.QueryParamMixin,
        base.KeyTransformer):
    pass


class BpCharDisTransformer(
        _CharDisMixin,
        base.BodyParamMixin,
        base.KeyTransformer):
    pass


class RqCharDisTransformer(
        _CharDisMixin,
        base.ReqTransformer):
    pass
