# -*- coding: utf-8 -*-
#
# Make PDF from latex files.
#
# Copyright (C) 2017 Nico Epp and Ralf Funk
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import shutil
import subprocess


MAIN_FILENAME = 'paper'
AUX_DIR = 'aux_files'
FILES_TO_COPY_FOR_BIB = (
    'p_references.bib',
    'sbc.bst',
)


def _run_cmd(cmd, cwd):
    print()
    print()
    print('#' * 50)
    print('RUN:', cmd)
    subprocess.run(cmd, cwd=cwd, shell=True)


def make_pdf():
    _run_cmd(
        cmd='pdflatex -interaction batchmode -output-directory "{}" {}'.format(
            AUX_DIR, MAIN_FILENAME),
        cwd='.')


def make_bibliography():
    for filename in FILES_TO_COPY_FOR_BIB:
        src = filename
        dst = os.path.join(AUX_DIR, filename)
        shutil.copy2(src, dst)

    _run_cmd(
        cmd='bibtex {}'.format(MAIN_FILENAME),
        cwd=AUX_DIR)


if __name__ == '__main__':
    # Some online forums suggest running the PDF command multiple times to get the bibliography
    # working correctly; that seems to work for us as well
    make_pdf()
    make_bibliography()
    make_pdf()
    make_pdf()
