# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Nico Epp and Ralf Funk
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import collections
import numpy as np
from abc import ABCMeta, abstractmethod
from sklearn.base import BaseEstimator
from typing import List
from ..data_sets import Request


class _BaseTransformer(BaseEstimator, metaclass=ABCMeta):

    @abstractmethod
    def get_feature_names(self) -> List[str]:
        pass

    def fit(self, X: List[Request], y=None):
        return self

    @abstractmethod
    def transform(self, X: List[Request], y=None) -> np.ndarray:
        pass

    def fit_transform(self, X: List[Request], y=None) -> np.ndarray:
        self.fit(X, y)
        return self.transform(X, y)

    @staticmethod
    def _get_features_per_key() -> List[str]:
        return ['-', ]

    @staticmethod
    @abstractmethod
    def _evaluate(v: str) -> List[float]:
        pass


class KeyTransformer(_BaseTransformer, metaclass=ABCMeta):

    def __init__(self):
        self._key_list = []     # type: List[str]

    def get_feature_names(self) -> List[str]:
        features_per_key = self._get_features_per_key()
        return ['{}__{}'.format(k, s)
                for k in self._key_list
                for s in features_per_key]

    def fit(self, X: List[Request], y=None):
        dict_attr_name = self._get_dict_attr_name()
        self._key_list = list(sorted(set(
            k
            for r in X
            for k in getattr(r, dict_attr_name))))
        return self

    def transform(self, X: List[Request], y=None) -> np.ndarray:
        if not isinstance(X, collections.Iterable):
            # convert to list if its only one element
            X = [X, ]

        dict_attr_name = self._get_dict_attr_name()
        n_features_per_key = len(self._get_features_per_key())

        n_samples = len(X)
        n_features = len(self._key_list) * n_features_per_key
        X_new = np.zeros((n_samples, n_features))

        for i, req in enumerate(X):
            for j, key in enumerate(self._key_list):
                d = getattr(req, dict_attr_name, {})

                if key in d:
                    result_list = self._evaluate(d[key])
                    assert len(result_list) == n_features_per_key

                    j_start = j * n_features_per_key
                    for k, elem in enumerate(result_list):
                        if elem != 0:
                            X_new[i, j_start + k] = float(elem)

        return X_new

    @staticmethod
    @abstractmethod
    def _get_dict_attr_name() -> str:
        pass


class ReqTransformer(_BaseTransformer, metaclass=ABCMeta):

    def get_feature_names(self) -> List[str]:
        features_per_key = self._get_features_per_key()
        return ['Req__{}'.format(s)
                for s in features_per_key]

    def transform(self, X: List[Request], y=None) -> np.ndarray:
        if not isinstance(X, collections.Iterable):
            # convert to list if its only one element
            X = [X, ]

        n_samples = len(X)
        n_features = len(self._get_features_per_key())
        X_new = np.zeros((n_samples, n_features))

        for i, req in enumerate(X):
            result_list = self._evaluate(req.original_str)
            assert len(result_list) == n_features

            for k, elem in enumerate(result_list):
                if elem != 0:
                    X_new[i, k] = float(elem)

        return X_new


class HeaderMixin:

    @staticmethod
    def _get_dict_attr_name() -> str:
        return 'headers'


class QueryParamMixin:

    @staticmethod
    def _get_dict_attr_name() -> str:
        return 'query_params'


class BodyParamMixin:

    @staticmethod
    def _get_dict_attr_name() -> str:
        return 'body_params'
