# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Nico Epp and Ralf Funk
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import collections
import pandas as pd
from abc import ABCMeta
from typing import List
from . import base


class _RawDataKeyTransformer(base.KeyTransformer, metaclass=ABCMeta):

    def transform(self, X: List[base.Request], y=None) -> pd.DataFrame:
        if not isinstance(X, collections.Iterable):
            # convert to list if its only one element
            X = [X, ]

        dict_attr_name = self._get_dict_attr_name()
        n_features_per_key = len(self._get_features_per_key())

        n_samples = len(X)
        n_features = len(self._key_list) * n_features_per_key

        row_list = []
        for i, req in enumerate(X):
            col_list = []
            for j, key in enumerate(self._key_list):
                d = getattr(req, dict_attr_name, {})
                v = d.get(key, '')
                col_list.append(v)
            row_list.append(col_list)

        df = pd.DataFrame(row_list)
        assert df.shape == (n_samples, n_features)

        return df

    @staticmethod
    def _evaluate(v: str) -> List[float]:
        pass


class _RawDataReqTransformer(base.ReqTransformer, metaclass=ABCMeta):

    def transform(self, X: List[base.Request], y=None) -> pd.DataFrame:
        if not isinstance(X, collections.Iterable):
            # convert to list if its only one element
            X = [X, ]

        n_samples = len(X)
        n_features = len(self._get_features_per_key())

        row_list = []
        for i, req in enumerate(X):
            row_list.append(req.original_str)

        df = pd.DataFrame(row_list)
        assert df.shape == (n_samples, n_features)

        return df

    @staticmethod
    def _evaluate(v_list: List[str]) -> List[float]:
        pass


class HeRawDataTransformer(
        base.HeaderMixin,
        _RawDataKeyTransformer):
    pass


class QpRawDataTransformer(
        base.QueryParamMixin,
        _RawDataKeyTransformer):
    pass


class BpRawDataTransformer(
        base.BodyParamMixin,
        _RawDataKeyTransformer):
    pass


class RqRawDataTransformer(
        _RawDataReqTransformer):
    pass
