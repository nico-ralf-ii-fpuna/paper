# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Nico Epp and Ralf Funk
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import numpy as np
import pandas as pd
import seaborn as sns
import time
from sklearn.externals import joblib
from sklearn.pipeline import make_pipeline, make_union
from sklearn.svm import OneClassSVM
from ..base import BASE_PATH
from .. import data_sets, feature_extraction


_file_memory = joblib.Memory(cachedir=os.path.join(BASE_PATH, 'cache'))


@_file_memory.cache
def _build_and_fit(ds_url: str) -> pd.DataFrame:
    result_list = []

    normal_list, anomalous_list = data_sets.get(ds_url)

    for i in range(1, 5):
        n = 10**i
        print('ds_url {} | n {:9,d}'.format(ds_url, n))

        train_list = []
        while len(train_list) < n:
            train_list += normal_list
        train_list = train_list[:n]
        assert len(train_list) == n

        t_start = time.perf_counter()
        clf = make_pipeline(
            make_union(*[class_() for class_ in feature_extraction.NUMBERS_TF_LIST]),
            OneClassSVM(random_state=0, nu=0.01, gamma=0.01))
        clf.fit(train_list)
        t_end = time.perf_counter()
        result_list.append([ds_url, n, (t_end - t_start) * 1000])

    df = pd.DataFrame(data=result_list, columns=['ds_url', 'n_samples', 'total_duration'])
    df['duration_per_sample'] = df['total_duration'] / df['n_samples']

    return df


def run() -> pd.DataFrame:
    df_list = []

    for ds_url in data_sets.DS_URL_LIST:
        df_list.append(
            _build_and_fit(ds_url))

    df = pd.concat(df_list, ignore_index=True)      # type: pd.DataFrame

    print()
    print('max training time')
    for n_samples, sub_df in df.groupby(['n_samples', ]):
        print('n_samples {:9,d} | per sample {:15.2f} ms | total {:15.2f} ms'.format(
            n_samples, sub_df['duration_per_sample'].max(), sub_df['total_duration'].max()))

    return df


def plot(df: pd.DataFrame):
    df = df.copy()      # type: pd.DataFrame
    df['number of requests'] = df['n_samples'].map(lambda x: '{:,d}'.format(x))

    fig, axs = sns.plt.subplots(nrows=2, ncols=1, sharex=True)
    fig.suptitle('Processing time for fitting the classifier')

    sns.pointplot(
        data=df, x='number of requests', y='total_duration', ax=axs[0],
        estimator=np.max, ci=None)
    sns.pointplot(
        data=df, x='number of requests', y='duration_per_sample', ax=axs[1],
        estimator=np.max, ci=None)

    axs[0].set_xlabel('')
    axs[0].set_yscale('log')
    axs[0].set_ylabel('total duration (ms)')
    axs[1].set_ylabel('duration per request (ms)')
    sns.plt.show()
