# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Nico Epp and Ralf Funk
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import pandas as pd
from sklearn.externals import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion
from typing import Dict, Tuple
from ..base import BASE_PATH
from .. import data_sets
from . import base, char_distribution, entropy, length, raw_data


COLUMN_NAMES = ('tf_name', 'tf_part', 'source_0', 'source_1')
META_ID = ('Meta', 'id', '-', '-')
META_GROUP = ('Meta', 'group', '-', '-')
META_TRUE_LABEL = ('Meta', 'true_label', '-', '-')
META_PRED_LABEL = ('Meta', 'pred_label', '-', '-')
NUMBERS_TF_LIST = (
    char_distribution.RqCharDisTransformer,
    # char_distribution.HeCharDisTransformer,
    char_distribution.QpCharDisTransformer,
    char_distribution.BpCharDisTransformer,
    entropy.RqEntropyTransformer,
    # entropy.HeEntropyTransformer,
    entropy.QpEntropyTransformer,
    entropy.BpEntropyTransformer,
    length.RqLengthTransformer,
    # length.HeLengthTransformer,
    length.QpLengthTransformer,
    length.BpLengthTransformer,
)
RAW_DATA_TF_LIST = (
    raw_data.RqRawDataTransformer,
    # raw_data.HeRawDataTransformer,
    raw_data.QpRawDataTransformer,
    raw_data.BpRawDataTransformer,
)
COMMON_FILTER_CONSTRAINTS = {
    'R': {'source_0': ('Rq', '-')},
    'K': {'source_0': ('Qp', 'Bp', '-')},
    'numbers': {'tf_name': ('CharDis', 'Entropy', 'Length')},
}


_file_memory = joblib.Memory(cachedir=os.path.join(BASE_PATH, 'cache'))


@_file_memory.cache
def _transform(ds_url: str) -> pd.DataFrame:
    normal_list, anomalous_list = data_sets.get(ds_url)

    X_normal_list = []
    X_anomalous_list = []

    for tf_list in (NUMBERS_TF_LIST, RAW_DATA_TF_LIST):
        # make and fit feature union
        fu = FeatureUnion(
            [(class_.__name__.replace('Transformer', ''), class_())
             for class_ in tf_list],
            n_jobs=-1)
        fu.fit(normal_list)

        # create column MultiIndex
        col_tuples = []
        for s in fu.get_feature_names():
            s = '{}__{}'.format(s[:2], s[2:])
            source_0, tf_name, source_1, tf_part = s.split('__')
            col_tuples.append((tf_name, tf_part, source_0, source_1))
        idx = pd.MultiIndex.from_tuples(col_tuples, names=COLUMN_NAMES)

        # transform requests
        X_normal = pd.DataFrame(
            fu.transform(normal_list),
            columns=idx)
        X_anomalous = pd.DataFrame(
            fu.transform(anomalous_list),
            columns=idx)
        X_normal_list.append(X_normal)
        X_anomalous_list.append(X_anomalous)

    # concatenate all features
    X_normal = pd.concat(X_normal_list, axis=1)         # type: pd.DataFrame
    X_anomalous = pd.concat(X_anomalous_list, axis=1)   # type: pd.DataFrame

    # add meta
    X_normal[META_ID] = X_normal.index
    X_normal[META_TRUE_LABEL] = 'normal'
    X_anomalous[META_ID] = X_anomalous.index
    X_anomalous[META_TRUE_LABEL] = 'anomalous'

    return pd.concat([X_normal, X_anomalous], ignore_index=True)


def _split(df: pd.DataFrame, random_state, train_size_normal, train_size_anomalous) -> pd.DataFrame:
    for label, train_size in zip(
            ('normal','anomalous'),
            (train_size_normal, train_size_anomalous),      # can be float or int
    ):
        sub_df = df[df[META_TRUE_LABEL] == label]

        if train_size > 0:
            # mark some requests as train group, the others as test group
            train_index_list, _ = train_test_split(
                list(sub_df.index),
                random_state=random_state,
                train_size=train_size)
        else:
            # all requests will be test group
            train_index_list = []

        # assign the corresponding labels
        group_list = tuple(
            'train' if i in train_index_list else 'test'
            for i in sub_df.index)
        df.loc[df[META_TRUE_LABEL] == label, META_GROUP] = group_list

    return df


def get(ds_url: str, random_state, train_size_normal, train_size_anomalous) -> pd.DataFrame:
    df = _transform(ds_url)
    df = _split(df, random_state, train_size_normal, train_size_anomalous)
    return df


def filter_by(df: pd.DataFrame, constraints: Dict) -> pd.DataFrame:
    # assure that the constraints are lists of values
    constraints = {
        k: [v, ] if isinstance(v, str) else v
        for k, v in constraints.items()}

    new_df = pd.DataFrame()

    # check each column if it fits the constraints
    for col_tuple in df.columns:
        include_col = True
        for level_name, col_val in zip(df.columns.names, col_tuple):
            if level_name in constraints:
                if col_val not in constraints[level_name]:
                    include_col = False

        if include_col:
            new_df[col_tuple] = df[col_tuple]

    new_df.columns = pd.MultiIndex.from_tuples(new_df.columns, names=df.columns.names)
    return new_df


def feature_numbers(df: pd.DataFrame) -> Tuple:
    sub_df = df[df[META_GROUP] == 'train']
    X_train = filter_by(
        sub_df,
        COMMON_FILTER_CONSTRAINTS['numbers'])
    y_train_true = sub_df[META_TRUE_LABEL].map(lambda x: 1 if x == 'normal' else -1)

    sub_df = df[df[META_GROUP] == 'test']
    X_test = filter_by(
        sub_df,
        COMMON_FILTER_CONSTRAINTS['numbers'])
    y_test_true = sub_df[META_TRUE_LABEL].map(lambda x: 1 if x == 'normal' else -1)

    return X_train, y_train_true, X_test, y_test_true
