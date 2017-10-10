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
import mock

from deploy import utils
from deploy.utils import (
    err_exit,
    check_sudo_privilege,
    check_file_exists,
    make_file_executable,
    confirm_dir_exists,
    check_scenario_valid
)


def test_err_exit():
    message = 'test error msg!'
    with pytest.raises(SystemExit):
        err_exit(message)


@mock.patch('deploy.utils.err_exit')
@mock.patch('deploy.utils.os.getuid')
def test_check_sudo_privilege(mock_getuid, mock_err_exit):
    mock_getuid.return_value = 1
    check_sudo_privilege()
    utils.err_exit.assert_called_once_with('You need run this script with sudo privilege')


@pytest.mark.parametrize('test_file_name', [
    ('no_exist_file'),
    ('exist_file')])
def test_check_file_exists(tmpdir, test_file_name):
    try:
        file_path = os.path.join(tmpdir.dirname, tmpdir.basename, test_file_name)
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
        file_path = os.path.join(tmpdir.dirname, tmpdir.basename, test_file_name)
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
        dir_path = os.path.join(tmpdir.dirname, tmpdir.basename, 'no_exist_dir')
    if test_dir_name == 'exist_dir':
        tmpsubdir = tmpdir.mkdir('exist_dir')
        dir_path = os.path.join(tmpsubdir.dirname, tmpsubdir.basename)
    confirm_dir_exists(dir_path)
    assert os.path.isdir(dir_path)
    tmpdir.remove()


@pytest.mark.parametrize('scenario', [
    ('os-nosdn-nofeature-ha')])
@mock.patch("deploy.utils.err_exit")
def test_check_scenario_supported(mock_err_exit, scenario):
    check_scenario_valid(scenario)
    mock_err_exit.assert_not_called()


@pytest.mark.parametrize('scenario', [
    ('os-odl-kvm-ha')])
@mock.patch("deploy.utils.err_exit")
def test_check_scenario_unsupported(mock_err_exit, scenario):
    check_scenario_valid(scenario)
    mock_err_exit.assert_called_once()