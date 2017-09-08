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
import yaml
import mock
sys.modules['libvirt'] = mock.Mock()

from deploy.deploy import (
    config_arg_parser,
    DaisyDeployment
)


def test_config_arg_parser():
    parser = config_arg_parser()
    assert isinstance(parser, argparse.ArgumentParser)


@pytest.fixture(scope="session")
def conf_file_dir(data_root):
    return os.path.join(data_root, 'lab_conf')


@pytest.mark.parametrize('kwargs, expect_dasiy_info', [
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
      'cleanup_only': False,
      'remote_dir': '/home/daisy',
      'work_dir': 'workdir',
      'storage_dir': 'vms',
      'pxe_bridge': 'pxebr',
      'deploy_log': 'deploy.log',
      'scenario': 'os-odl-nofeature-ha'},
     {'name': 'daisy',
      'image': 'daisy.qcow2',
      'address': '10.20.0.2',
      'gateway': '10.20.0.1',
      'password': 'r00tme',
      'disk_size': 50})])
def test_create_DaisyDeployment_instance(kwargs, expect_dasiy_info, conf_file_dir, tmpdir):
    kwargs['deploy_file'] = os.path.join(conf_file_dir, kwargs['deploy_file'])
    kwargs['net_file'] = os.path.join(conf_file_dir, kwargs['net_file'])
    tmpdir.join(kwargs['bin_file']).write('testdata')
    kwargs['bin_file'] = os.path.join(tmpdir.dirname, tmpdir.basename, kwargs['bin_file'])
    kwargs['deploy_log'] = os.path.join(tmpdir.dirname, tmpdir.basename, kwargs['deploy_log'])
    tmpsubdir = tmpdir.mkdir(kwargs['work_dir'])
    kwargs['work_dir'] = os.path.join(tmpsubdir.dirname, tmpsubdir.basename)
    tmpsubdir = tmpdir.mkdir(kwargs['storage_dir'])
    kwargs['storage_dir'] = os.path.join(tmpsubdir.dirname, tmpsubdir.basename)

    deploy = DaisyDeployment(**kwargs)
    assert (deploy.lab_name, deploy.pod_name, deploy.src_deploy_file, deploy.net_file, deploy.bin_file,
            deploy.daisy_only, deploy.cleanup_only, deploy.remote_dir, deploy.work_dir, deploy.storage_dir,
            deploy.deploy_log, deploy.scenario) == \
           (kwargs['lab_name'], kwargs['pod_name'], kwargs['deploy_file'], kwargs['net_file'],
            kwargs['bin_file'], kwargs['daisy_only'], kwargs['cleanup_only'], kwargs['remote_dir'],
            kwargs['work_dir'], kwargs['storage_dir'], kwargs['deploy_log'], kwargs['scenario'])

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
