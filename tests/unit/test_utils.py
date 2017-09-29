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
import shutil

from deploy import utils
from deploy.utils import (
    get_logger,
    save_log_to_file,
    err_exit,
    log_bar,
    check_sudo_privilege,
    check_file_exists,
    make_file_executable,
    confirm_dir_exists,
    update_config,
    ipmi_reboot_node,
    run_shell,
    check_scenario_valid,
    LI
)


@pytest.fixture(scope="module")
def daisy_conf_file_dir(data_root):
    return os.path.join(data_root, 'daisy_conf')


@mock.patch.object(utils.logging.Logger, 'addHandler')
def test_get_logger(mock_addHandler):
    get_logger()
    mock_addHandler.assert_called_once()


@mock.patch.object(utils.logging.Logger, 'addHandler')
def test_save_log_to_file(mock_addHandler, tmpdir):
    log_file = os.path.join(tmpdir.dirname, tmpdir.basename, 'test_log.txt')
    save_log_to_file(log_file)
    mock_addHandler.assert_called_once()
    tmpdir.remove()


def test_err_exit():
    message = 'test error msg!'
    with pytest.raises(SystemExit):
        err_exit(message)


def test_log_bar():
    log_bar('test_messgae', log_func=LI)


@mock.patch('deploy.utils.err_exit')
@mock.patch('deploy.utils.os.getuid')
def test_check_sudo_privilege(mock_getuid, mock_err_exit):
    mock_getuid.return_value = 1
    check_sudo_privilege()
    mock_err_exit.assert_called_once_with('You need run this script with sudo privilege')


@pytest.mark.parametrize('test_file_name, include_dirname', [
    ('no_exist_file', True),
    ('exist_file', True),
    ('no_exist_file', False),
    ('exist_file', False)])
@mock.patch('deploy.utils.err_exit')
def test_check_file_exists(mock_err_exit, tmpdir, test_file_name, include_dirname):
    if include_dirname:
        file_path = os.path.join(tmpdir.dirname, tmpdir.basename, test_file_name)
        if test_file_name == 'exist_file':
            os.mknod(file_path)
    else:
        file_path = test_file_name
    check_file_exists(file_path)
    if include_dirname is True:
        if test_file_name == 'exist_file':
            mock_err_exit.assert_not_called()
        else:
            mock_err_exit.assert_called_once()
    if include_dirname is False:
        mock_err_exit.assert_called_once()
    tmpdir.remove()


@pytest.mark.parametrize('test_file_name, status, include_dir', [
    ('no_exist_file', False, False),
    ('no_exe_file', False, True),
    ('no_exe_file', True, True),
    ('exe_file', False, True)])
@mock.patch('deploy.utils.commands.getstatusoutput')
@mock.patch('deploy.utils.err_exit')
def test_make_file_executable(mock_err_exit, mock_getstatusoutput,
                              tmpdir, test_file_name,
                              status, include_dir):
    if include_dir:
        file_path = os.path.join(tmpdir.dirname, tmpdir.basename, test_file_name)
    else:
        file_path = test_file_name
    if test_file_name == 'no_exe_file':
        os.mknod(file_path)
    if test_file_name == 'exe_file':
        os.mknod(file_path, 0700)
    output = 'test_out'
    mock_getstatusoutput.return_value = (status, output)
    make_file_executable(file_path)
    if test_file_name == 'exe_file':
        mock_err_exit.assert_not_called()
        assert os.access(file_path, os.X_OK)
    if test_file_name == 'no_exe_file' and status is False:
        mock_err_exit.assert_not_called()
    if test_file_name == 'no_exe_file' and status is True:
        mock_err_exit.assert_called()
    if test_file_name == 'no_exist_file':
        mock_err_exit.assert_called()
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


def test_update_config(daisy_conf_file_dir, tmpdir):
    src_daisy_conf_file = os.path.join(daisy_conf_file_dir, 'daisy.conf')
    dst_daisy_conf_file = os.path.join(tmpdir.dirname, tmpdir.basename, 'daisy.conf')
    shutil.copyfile(src_daisy_conf_file, dst_daisy_conf_file)
    key = 'daisy_management_ip'
    value = '10.20.11.2'
    update_line = 'daisy_management_ip = 10.20.11.2'
    is_match = False
    update_config(dst_daisy_conf_file, key, value, section='DEFAULT')
    with open(dst_daisy_conf_file) as f:
        lines = f.readlines()
        for line in lines:
            line_content = line.strip()
            if update_line in line_content:
                is_match = True
                break
    assert is_match
    tmpdir.remove()


@pytest.mark.parametrize('boot_source, status', [
    (None, 0),
    (None, 1),
    ('test_source', 0),
    ('test_source', 1)])
@mock.patch('deploy.utils.err_exit')
@mock.patch.object(utils.commands, 'getstatusoutput')
def test_ipmi_reboot_node(mock_getstatusoutput, mock_err_exit,
                          boot_source, status):
    host = '192.168.1.11'
    user = 'testuser'
    passwd = 'testpass'
    output = 'test_out'
    mock_getstatusoutput.return_value = (status, output)
    ipmi_reboot_node(host, user, passwd, boot_source=boot_source)
    if boot_source:
        assert mock_getstatusoutput.call_count == 2
        if status:
            assert mock_err_exit.call_count == 2
    else:
        mock_getstatusoutput.called_once()
        if status:
            mock_err_exit.called_once()


@pytest.mark.parametrize('cmd, check, expect', [
    ('cd /home', False, 0),
    ('cd /home', True, 0),
    ('test_command', False, 127),
    ('test_command', True, 127)])
@mock.patch('deploy.utils.err_exit')
def test_run_shell(mock_err_exit, cmd, check, expect):
    ret = run_shell(cmd, check=check)
    if check:
        if cmd == 'cd /home':
            mock_err_exit.assert_not_called()
        elif cmd == 'test_command':
            mock_err_exit.assert_called_once()
    assert ret == expect


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
