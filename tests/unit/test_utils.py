##############################################################################
# Copyright (c) 2017 ZTE Corp and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import os

import pytest

from deploy.utils import (
    check_file_exists,
    make_file_executable,
    confirm_dir_exists,
    check_scenario_valid
)


@pytest.mark.parametrize('test_file_name', [
    ('no_exist_file'),
    ('exist_file')])
def test_check_file_exists(tmpdir, test_file_name):
    try:
        file_path = os.path.join(tmpdir.dirname, test_file_name)
        if test_file_name == 'exist_file':
            os.mknod(file_path)
        check_file_exists(file_path)
    except SystemExit:
        if test_file_name == 'exist_file':
            assert 0
    else:
        if test_file_name == 'no_exist_file':
            assert 0
    finally:
        tmpdir.remove()


@pytest.mark.parametrize('test_file_name', [
    ('no_exist_file'),
    ('no_exe_file'),
    ('exe_file')])
def test_make_file_executable(tmpdir, test_file_name):
    try:
        file_path = os.path.join(tmpdir.dirname, test_file_name)
        if test_file_name == 'no_exe_file':
            os.mknod(file_path)
        if test_file_name == 'exe_file':
            os.mknod(file_path, 0700)
        make_file_executable(file_path)
    except SystemExit:
        if test_file_name == 'no_exe_file' or test_file_name == 'exe_file':
            assert 0
    else:
        if test_file_name == 'no_exist_file':
            assert 0
    finally:
        if test_file_name == 'no_exe_file' or test_file_name == 'exe_file':
            assert os.access(file_path, os.X_OK)
        tmpdir.remove()


@pytest.mark.parametrize('test_dir_name', [
    ('no_exist_dir'),
    ('exist_dir')])
def test_confirm_dir_exists(tmpdir, test_dir_name):
    if test_dir_name == 'no_exist_dir':
        dir_path = os.path.join(tmpdir.dirname, 'no_exist_dir')
    if test_dir_name == 'exist_dir':
        dir_path = tmpdir.mkdir('exist_dir').dirname
    confirm_dir_exists(dir_path)
    assert os.path.isdir(dir_path)
    tmpdir.remove()


@pytest.mark.parametrize('scenario', [
    ('os-nosdn-nofeature-ha'),
    ('os-odl-kvm-ha')])
def test_check_scenario_valid(scenario):
    try:
        check_scenario_valid(scenario)
    except SystemExit:
        if scenario == 'os-nosdn-nofeature-ha':
            assert 0
    else:
        if scenario == 'os-odl-kvm-ha':
            assert 0
