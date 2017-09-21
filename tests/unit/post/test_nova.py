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

from deploy.post import nova
from deploy.post.nova import Nova


@pytest.fixture(scope="module")
def openrc_conf_file_dir(data_root):
    return os.path.join(data_root, 'openrc_conf')


def test_create_Nova_instance(openrc_conf_file_dir):
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    nova = Nova(openrc=openrc_file)
    assert nova.flavors == nova.client.flavors


@mock.patch('novaclient.v2.flavors.FlavorManager.create')
def test_create_flavor_in_Glance(mock_create, openrc_conf_file_dir):
    class Test_flavor():
        def __init__(self, id):
            self.id = id
    flavor_conf = {
        'name': 'flavor_test',
        'ram': 64,
        'vcpus': 1,
        'disk': 1,
        'is_public': True
    }
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    id = 0x1234
    nova = Nova(openrc=openrc_file)
    mock_create.return_value = Test_flavor(id)
    ret = nova.create_flavor(flavor_conf['name'], flavor_conf['ram'],
                             flavor_conf['vcpus'], flavor_conf['disk'],
                             is_public=flavor_conf['is_public'])
    assert ret == id
    mock_create.assert_called_once_with(flavor_conf['name'], flavor_conf['ram'],
                                        flavor_conf['vcpus'], flavor_conf['disk'],
                                        is_public=flavor_conf['is_public'])


@mock.patch.object(nova.Nova, 'list_flavors')
def test_get_flavor_by_name_in_Nova(mock_list_flavors, openrc_conf_file_dir):
    class Test_flavor():
        def __init__(self, name):
            self.name = name
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    flavor_inst1 = Test_flavor('test_flavor1')
    flavor_inst2 = Test_flavor('test_flavor2')
    flavors_list = [flavor_inst1, flavor_inst2]
    flavor_name = 'test_flavor2'
    mock_list_flavors.return_value = flavors_list
    nova = Nova(openrc=openrc_file)
    ret = nova.get_flavor_by_name(flavor_name)
    assert ret == flavor_inst2
    mock_list_flavors.assert_called_once_with()


@mock.patch('novaclient.v2.flavors.FlavorManager.list')
def test_list_flavors_in_Nova(mock_list, openrc_conf_file_dir):
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    flavor_list = ['test1']
    mock_list.return_value = flavor_list
    nova = Nova(openrc=openrc_file)
    ret = nova.list_flavors()
    assert ret == flavor_list
    mock_list.assert_called_once_with(detailed=True)
