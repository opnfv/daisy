##############################################################################
# Copyright (c) 2017 ZTE Corp and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import pytest
import argparse
import os
import sys
import shutil
import yaml
from deploy.utils import WORKSPACE
import mock
sys.modules['libvirt'] = mock.Mock()

from deploy import environment                          # noqa: ignore=E402
from deploy.deploy import (
    config_arg_parser,
    DaisyDeployment,
    parse_arguments,
    main
)   # noqa: ignore=E402


def test_config_arg_parser():
    parser = config_arg_parser()
    assert isinstance(parser, argparse.ArgumentParser)


@pytest.fixture(scope="session")
def conf_file_dir(data_root):
    return os.path.join(data_root, 'lab_conf')


@pytest.mark.parametrize('kwargs, check_err, expect_dasiy_info', [
    ({'lab_name': 'zte',
      'pod_name': 'virtual1',
      'deploy_file': 'deploy_virtual1.yml',
      'net_file': 'network_virtual1.yml',
      'bin_file': 'opnfv.bin',
      'daisy_only': False,
      'cleanup_only': False,
      'remote_dir': '/home/daisy',
      'work_dir': 'workdir',
      'storage_dir': 'vms',
      'pxe_bridge': 'pxebr',
      'deploy_log': 'deploy.log',
      'scenario': 'os-nosdn-nofeature-ha'},
     [],
     {'name': 'daisy',
      'image': 'daisy.qcow2',
      'address': '10.20.11.2',
      'gateway': '10.20.11.1',
      'password': 'r00tme',
      'disk_size': 50}),
    ({'lab_name': 'zte',
      'pod_name': 'pod1',
      'deploy_file': 'deploy_baremetal.yml',
      'net_file': 'network_baremetal.yml',
      'bin_file': 'opnfv.bin',
      'daisy_only': False,
      'cleanup_only': True,
      'remote_dir': '/home/daisy',
      'work_dir': 'workdir',
      'storage_dir': 'vms',
      'pxe_bridge': 'pxebr',
      'deploy_log': 'deploy.log',
      'scenario': 'os-odl-nofeature-ha'},
     ['disk_size invalid'],
     {'name': 'daisy',
      'image': 'daisy.qcow2',
      'address': '10.20.0.2',
      'gateway': '10.20.0.1',
      'password': 'r00tme',
      'disk_size': 50})])
@mock.patch('deploy.deploy.deploy_schema_validate')
@mock.patch('deploy.deploy.err_exit')
def test_create_DaisyDeployment_instance(mock_err_exit, mock_deploy_schema_validate,
                                         kwargs, expect_dasiy_info,
                                         conf_file_dir, tmpdir,
                                         check_err):
    kwargs['deploy_file'] = os.path.join(conf_file_dir, kwargs['deploy_file'])
    kwargs['net_file'] = os.path.join(conf_file_dir, kwargs['net_file'])
    tmpdir.join(kwargs['bin_file']).write('testdata')
    kwargs['bin_file'] = os.path.join(tmpdir.dirname, tmpdir.basename, kwargs['bin_file'])
    kwargs['deploy_log'] = os.path.join(tmpdir.dirname, tmpdir.basename, kwargs['deploy_log'])
    tmpsubdir = tmpdir.mkdir(kwargs['work_dir'])
    kwargs['work_dir'] = os.path.join(tmpsubdir.dirname, tmpsubdir.basename)
    tmpsubdir = tmpdir.mkdir(kwargs['storage_dir'])
    kwargs['storage_dir'] = os.path.join(tmpsubdir.dirname, tmpsubdir.basename)
    mock_deploy_schema_validate.return_value = check_err

    deploy = DaisyDeployment(**kwargs)
    assert (deploy.lab_name, deploy.pod_name, deploy.src_deploy_file, deploy.net_file, deploy.bin_file,
            deploy.daisy_only, deploy.cleanup_only, deploy.remote_dir, deploy.work_dir, deploy.storage_dir,
            deploy.deploy_log, deploy.scenario) == \
           (kwargs['lab_name'], kwargs['pod_name'], kwargs['deploy_file'], kwargs['net_file'],
            kwargs['bin_file'], kwargs['daisy_only'], kwargs['cleanup_only'], kwargs['remote_dir'],
            kwargs['work_dir'], kwargs['storage_dir'], kwargs['deploy_log'], kwargs['scenario'])
    if check_err:
        mock_err_exit.assert_called_once_with('Configuration deploy.yml check failed!')
    else:
        mock_err_exit.assert_not_called()

    assert deploy.deploy_file_name == 'final_deploy.yml'
    assert deploy.deploy_file == os.path.join(deploy.work_dir, 'final_deploy.yml')
    assert os.path.isfile(os.path.join(deploy.work_dir, 'final_deploy.yml'))

    if not deploy.cleanup_only:
        assert deploy.net_file_name == os.path.basename(kwargs['net_file'])
        with open(deploy.net_file) as yaml_file:
            expected_net_struct = yaml.safe_load(yaml_file)
            assert expected_net_struct == deploy.net_struct
    else:
        assert deploy.net_struct is None

    if 'virtual' in kwargs['deploy_file']:
        assert (deploy.adapter == 'libvirt' and deploy.pxe_bridge == 'daisy1')

    else:
        assert (deploy.adapter == 'ipmi' and deploy.pxe_bridge == 'br7')

    expect_dasiy_info['image'] = os.path.join(kwargs['storage_dir'], expect_dasiy_info['image'])
    assert deploy.daisy_server_info == expect_dasiy_info
    tmpdir.remove()


@pytest.mark.parametrize('kwargs', [
    (
        {
            'lab_name': 'zte',
            'pod_name': 'virtual1',
            'deploy_file': 'deploy_baremetal.yml',
            'net_file': 'network_baremetal.yml',
            'bin_file': 'opnfv.bin',
            'daisy_only': False,
            'cleanup_only': False,
            'remote_dir': '/home/daisy',
            'work_dir': 'workdir',
            'storage_dir': 'vms',
            'pxe_bridge': 'pxebr',
            'deploy_log': 'deploy.log',
            'scenario': 'os-nosdn-nofeature-ha'
        }
    ),
    (
        {
            'lab_name': 'zte',
            'pod_name': 'pod1',
            'deploy_file': 'deploy_baremetal.yml',
            'net_file': 'network_baremetal.yml',
            'bin_file': 'opnfv.bin',
            'daisy_only': False,
            'cleanup_only': True,
            'remote_dir': '/home/daisy',
            'work_dir': 'workdir',
            'storage_dir': 'vms',
            'pxe_bridge': 'pxebr',
            'deploy_log': 'deploy.log',
            'scenario': 'os-odl-nofeature-ha'
        }
    ),
    (
        {
            'lab_name': 'zte',
            'pod_name': 'pod1',
            'deploy_file': 'deploy_baremetal.yml',
            'net_file': 'network_baremetal.yml',
            'bin_file': 'opnfv.bin',
            'daisy_only': True,
            'cleanup_only': False,
            'remote_dir': '/home/daisy',
            'work_dir': 'workdir',
            'storage_dir': 'vms',
            'pxe_bridge': 'pxebr',
            'deploy_log': 'deploy.log',
            'scenario': 'os-odl-nofeature-ha'
        }
    )])
@mock.patch.object(environment.BareMetalEnvironment, 'delete_old_environment')
@mock.patch.object(environment.BareMetalEnvironment, 'create_daisy_server')
@mock.patch.object(environment.BareMetalEnvironment, 'install_daisy')
@mock.patch.object(environment.BareMetalEnvironment, 'deploy')
def test_run_in_DaisyDeployment(mock_deploy, mock_install_daisy,
                                mock_create_daisy_server, mock_delete_old_environment,
                                conf_file_dir, tmpdir, kwargs):
    kwargs['deploy_file'] = os.path.join(conf_file_dir, kwargs['deploy_file'])
    kwargs['net_file'] = os.path.join(conf_file_dir, kwargs['net_file'])
    tmpdir.join(kwargs['bin_file']).write('testdata')
    kwargs['bin_file'] = os.path.join(tmpdir.dirname, tmpdir.basename, kwargs['bin_file'])
    kwargs['deploy_log'] = os.path.join(tmpdir.dirname, tmpdir.basename, kwargs['deploy_log'])
    tmpsubdir = tmpdir.mkdir(kwargs['work_dir'])
    kwargs['work_dir'] = os.path.join(tmpsubdir.dirname, tmpsubdir.basename)
    tmpsubdir = tmpdir.mkdir(kwargs['storage_dir'])
    kwargs['storage_dir'] = os.path.join(tmpsubdir.dirname, tmpsubdir.basename)
    daisy_deploy = DaisyDeployment(**kwargs)
    daisy_deploy.run()
    mock_delete_old_environment.asser_called_once_with()
    if daisy_deploy.cleanup_only is False:
        mock_create_daisy_server.assert_called_once_with()
        if daisy_deploy.daisy_only is False:
            mock_deploy.assert_called_once_with(daisy_deploy.deploy_file, daisy_deploy.net_file)
            mock_install_daisy.assert_called_once_with(daisy_deploy.remote_dir, daisy_deploy.bin_file,
                                                       daisy_deploy.deploy_file_name, daisy_deploy.net_file_name)
        else:
            mock_deploy.assert_not_called()
            mock_install_daisy.assert_not_called()
    else:
        mock_create_daisy_server.assert_not_called()
    tmpdir.remove()


@mock.patch('deploy.deploy.argparse.ArgumentParser.parse_args')
@mock.patch('deploy.deploy.check_sudo_privilege')
@mock.patch('deploy.deploy.save_log_to_file')
@mock.patch('deploy.deploy.check_scenario_valid')
@mock.patch('deploy.deploy.check_file_exists')
@mock.patch('deploy.deploy.make_file_executable')
@mock.patch('deploy.deploy.confirm_dir_exists')
def test_parse_arguments(mock_confirm_dir_exists, mock_make_file_executable,
                         mock_check_file_exists, mock_check_scenario_valid,
                         mock_save_log_to_file, mock_check_sudo_privilege,
                         mock_parse_args, tmpdir):
    class MockArg():
        def __init__(self, lab_name, pod_name, bin_file, daisy_only,
                     cleanup_only, remote_dir, work_dir, storage_dir, pxe_bridge,
                     deploy_log, scenario):
            self.lab_name = lab_name
            self.pod_name = pod_name
            self.bin_file = bin_file
            self.daisy_only = daisy_only
            self.cleanup_only = cleanup_only
            self.remote_dir = remote_dir
            self.work_dir = work_dir
            self.storage_dir = storage_dir
            self.pxe_bridge = pxe_bridge
            self.deploy_log = deploy_log
            self.scenario = scenario

    bin_file_path = os.path.join(tmpdir.dirname, tmpdir.basename, 'opnfv.bin')
    deploy_log_path = os.path.join(tmpdir.dirname, tmpdir.basename, 'deploy.log')
    conf_base_dir = os.path.join(WORKSPACE, 'labs', 'zte', 'pod2')
    deploy_file = os.path.join(conf_base_dir, 'daisy/config/deploy.yml')
    net_file = os.path.join(conf_base_dir, 'daisy/config/network.yml')
    cleanup_only = False
    expected = {
        'lab_name': 'zte',
        'pod_name': 'pod2',
        'deploy_file': deploy_file,
        'net_file': net_file,
        'bin_file': bin_file_path,
        'daisy_only': False,
        'cleanup_only': cleanup_only,
        'remote_dir': '/home/daisy',
        'work_dir': '/tmp/workdir',
        'storage_dir': '/home/qemu/vms',
        'pxe_bridge': 'pxebr',
        'deploy_log': deploy_log_path,
        'scenario': 'os-nosdn-nofeature-noha'
    }
    mockarg = MockArg('zte', 'pod2', bin_file_path, False, cleanup_only, '/home/daisy', '/tmp/workdir',
                      '/home/qemu/vms', 'pxebr', deploy_log_path, 'os-nosdn-nofeature-noha')
    mock_parse_args.return_value = mockarg
    ret = parse_arguments()
    assert ret == expected
    mock_check_sudo_privilege.assert_called_once_with()
    mock_save_log_to_file.assert_called_once_with(deploy_log_path)
    mock_check_scenario_valid.assert_called_once_with('os-nosdn-nofeature-noha')
    if cleanup_only is False:
        mock_check_file_exists.assert_called_once_with(net_file)
    mock_make_file_executable.assert_called_once_with(bin_file_path)
    assert mock_confirm_dir_exists.call_count == 2
    tmpdir.remove()


@pytest.mark.parametrize('cleanup_only', [
    (False), (True)])
@mock.patch.object(DaisyDeployment, 'run')
@mock.patch('deploy.deploy.parse_arguments')
def test_main(mock_parse_arguments, mock_run, cleanup_only, tmpdir, conf_file_dir):
    bin_file_path = os.path.join(tmpdir.dirname, tmpdir.basename, 'opnfv.bin')
    with open(bin_file_path, 'w') as f:
        f.write('test_data')
    deploy_log_path = os.path.join(tmpdir.dirname, tmpdir.basename, 'deploy.log')
    deploy_file = os.path.join(tmpdir.dirname, tmpdir.basename, 'deploy.yml')
    src_deploy_file = os.path.join(conf_file_dir, 'deploy_baremetal.yml')
    shutil.copyfile(src_deploy_file, deploy_file)
    net_file = os.path.join(tmpdir.dirname, tmpdir.basename, 'network.yml')
    src_network_file = os.path.join(conf_file_dir, 'network_baremetal.yml')
    shutil.copyfile(src_network_file, net_file)
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename)
    kwargs = {
        'lab_name': 'zte',
        'pod_name': 'pod2',
        'deploy_file': deploy_file,
        'net_file': net_file,
        'bin_file': bin_file_path,
        'daisy_only': False,
        'cleanup_only': cleanup_only,
        'remote_dir': '/home/daisy',
        'work_dir': work_dir,
        'storage_dir': '/home/qemu/vms',
        'pxe_bridge': 'pxebr',
        'deploy_log': deploy_log_path,
        'scenario': 'os-nosdn-nofeature-noha'
    }
    mock_parse_arguments.return_value = kwargs
    main()
    mock_parse_arguments.assert_called_once_with()
    mock_run.assert_called_once_with()
    tmpdir.remove()
