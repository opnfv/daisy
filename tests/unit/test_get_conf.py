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

from deepdiff import DeepDiff

from deploy.get_conf import (
    get_yml_para,
    config
)


@pytest.fixture(scope="session")
def deploy_file(data_root):
    return os.path.join(data_root, 'lab_conf', 'deploy_virtual1.yml')


@pytest.fixture(scope="session")
def network_file(data_root):
    return os.path.join(data_root, 'lab_conf', 'network_virtual1.yml')


def test_get_yml_para(deploy_file):
    assert get_yml_para(deploy_file) == (50, 110, 110, 'r00tme', '10.20.11.2', '10.20.11.1', 5)


def test_config(deploy_file, network_file):
    result = config(deploy_file, network_file)
    expect = ({'ens8': [{'ip': '', 'name': 'EXTERNAL'}],
               'ens3': [{'ip': '', 'name': 'MANAGEMENT'},
                        {'ip': '', 'name': 'PUBLICAPI'},
                        {'ip': '', 'name': 'STORAGE'},
                        {'ip': '', 'name': 'physnet1'}],
               'ens9': [{'ip': '', 'name': 'HEARTBEAT'}]},
              ['computer01', 'computer02', 'controller01', 'controller02', 'controller03'],
              {'MANAGEMENT': {'cidr': '10.20.11.0/24', 'gateway': '10.20.11.1',
                              'ip_ranges': [{'start': '10.20.11.3',
                                             'end': '10.20.11.10'}]},
               'STORAGE': {'cidr': '10.20.11.0/24', 'gateway': '10.20.11.1',
                           'ip_ranges': [{'start': '10.20.11.3',
                                          'end': '10.20.11.10'}]},
               'EXTERNAL': {'cidr': '172.10.101.0/24', 'gateway': '172.10.101.1',
                            'ip_ranges': [{'start': '172.10.101.2',
                                           'end': '172.10.101.20'}],
                            'network_name': 'admin_external',
                            'mapping': 'physnet1'},
               'PUBLICAPI': {'cidr': '10.20.11.0/24', 'gateway': '10.20.11.1',
                             'ip_ranges': [{'start': '10.20.11.3',
                                            'end': '10.20.11.10'}]},
               'physnet1': {'cidr': '10.20.11.0/24', 'gateway': '10.20.11.1',
                            'ip_ranges': [{'start': '10.20.11.3',
                                           'end': '10.20.11.10'}]},
               'HEARTBEAT': {'cidr': '100.20.11.0/24', 'gateway': '100.20.11.1',
                             'ip_ranges': [{'start': '100.20.11.3',
                                            'end': '100.20.11.10'}]}},
              '10.20.11.11', '/dev/sdb',
              {'controller01': [], 'controller02': [], 'controller03': [],
               'computer01': [], 'computer02': []})
    DeepDiff(result, expect) == {}
