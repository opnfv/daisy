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

from deploy.post import neutron
from deploy.post.neutron import Neutron


@pytest.fixture(scope="module")
def openrc_conf_file_dir(data_root):
    return os.path.join(data_root, 'openrc_conf')


def test_create_Neutron_instance(openrc_conf_file_dir):
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    neutron = Neutron(openrc=openrc_file)
    assert neutron.openrc == openrc_file


@pytest.mark.parametrize('ret_get_network_by_name', [
    (None),
    ({'name': 'network_test2'})])
@mock.patch.object(neutron.Neutron, 'get_network_by_name')
@mock.patch.object(neutron.Neutron, '_create_network')
def test_create_network_in_Neutron(mock__create_network, mock_get_network_by_name,
                                   ret_get_network_by_name, openrc_conf_file_dir):
    net_name = 'network_test1'
    net_body = {'name': 'network_test1'}
    net_id = 0xabcd
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    mock_get_network_by_name.return_value = ret_get_network_by_name
    mock__create_network.return_value = net_id
    neutron = Neutron(openrc=openrc_file)
    ret = neutron.create_network(net_name, net_body)
    if ret_get_network_by_name is None:
        assert ret == net_id
        mock__create_network.asset_called_once_with(net_body)
    else:
        assert ret is None
        mock__create_network.assert_not_called()


@pytest.mark.parametrize('ret_get_subnet_by_name', [
    (None),
    ({'name': 'subnet_test2'})])
@mock.patch.object(neutron.Neutron, 'get_subnet_by_name')
@mock.patch.object(neutron.Neutron, '_create_subnet')
def test_create_subnet_in_Neutron_no_exist(mock__create_subnet, mock_get_subnet_by_name,
                                           ret_get_subnet_by_name, openrc_conf_file_dir):
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    subnet_body = {'name': 'subnet_test1'}
    subnet_id = 0xabcd
    mock_get_subnet_by_name.return_value = ret_get_subnet_by_name
    mock__create_subnet.return_value = subnet_id
    neutron = Neutron(openrc=openrc_file)
    ret = neutron.create_subnet(subnet_body)
    if ret_get_subnet_by_name is None:
        assert ret == subnet_id
        mock__create_subnet.asset_called_once_with(subnet_body)
    else:
        assert ret is None
        mock__create_subnet.assert_not_called()


@mock.patch('neutronclient.v2_0.client.Client.list_networks')
def test_list_networks_in_Neutron(mock_list_networks, openrc_conf_file_dir):
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    network_list = [{'name': 'network_test1'}]
    mock_list_networks.return_value = {'networks': network_list}
    neutron = Neutron(openrc=openrc_file)
    ret = neutron.list_networks()
    assert ret == network_list
    mock_list_networks.assert_called_once()


@mock.patch('neutronclient.v2_0.client.Client.list_subnets')
def test_list_subnets_in_Neutron(mock_list_subnets, openrc_conf_file_dir):
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    subnet_list = [{'name': 'subnet_test1'}]
    mock_list_subnets.return_value = {'subnets': subnet_list}
    neutron = Neutron(openrc=openrc_file)
    ret = neutron.list_subnets()
    assert ret == subnet_list
    mock_list_subnets.assert_called_once()


@mock.patch.object(neutron.Neutron, 'list_networks')
def test_get_network_by_name_in_Neutron(mock_list_networks, openrc_conf_file_dir):
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    network_list = [{'name': 'network_test1'}, {'name': 'network_test2'}]
    network_name = 'network_test1'
    mock_list_networks.return_value = network_list
    neutron = Neutron(openrc=openrc_file)
    ret = neutron.get_network_by_name(network_name)
    assert ret == {'name': 'network_test1'}
    mock_list_networks.assert_called_once()


@pytest.mark.parametrize('body, ret_list_subnets, expeced', [
    (
        {
            'subnets': [
                {
                    'name': 'ext_subnet',
                    'ip_version': 4,
                    'network_id': 0x1234
                }
            ]
        },
        [
            {'name': 'ext_subnet', 'network_id': 0x1234},
            {'name': 'inter_subnet', 'network_id': 0x2345}
        ],
        {'name': 'ext_subnet', 'network_id': 0x1234}
    ),
    (
        {
            'subnets': [
                {
                    'name': 'ext_subnet',
                    'ip_version': 4,
                    'network_id': 0x1234
                }
            ]
        },
        [
            {'name': 'admin_subnet', 'network_id': 0x1234},
            {'name': 'inter_subnet', 'network_id': 0x2345}
        ], None
    )])
@mock.patch.object(neutron.Neutron, 'list_subnets')
def test_get_subnet_by_name_in_Neutron(mock_list_subnets, body,
                                       ret_list_subnets, expeced,
                                       openrc_conf_file_dir):
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    mock_list_subnets.return_value = ret_list_subnets
    neutron = Neutron(openrc=openrc_file)
    ret = neutron.get_subnet_by_name(body)
    assert ret == expeced
    mock_list_subnets.assert_called_once()


@mock.patch('neutronclient.v2_0.client.Client.create_network')
def test__create_network_in_Neutron_no_exist(mock_create_network, openrc_conf_file_dir):
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    nid = 0x1234
    name = 'ext'
    body = {
        'network': {
            'name': 'ext',
            'admin_state_up': True,
            'shared': False,
            'provider:network_type': 'flat',
            'provider:physical_network': 'physnet1',
            'router:external': True
        }
    }
    ret_net_info = {
        'network':
            {
                'id': 0x1234
            }
    }
    mock_create_network.return_value = ret_net_info
    neutron = Neutron(openrc=openrc_file)
    ret = neutron._create_network(name, body)
    assert ret == nid
    mock_create_network.assert_called_once_with(body=body)


@mock.patch('neutronclient.v2_0.client.Client.create_subnet')
def test__create_subnet_in_Neutron_no_exist(mock_create_subnet, openrc_conf_file_dir):
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    snid = 0xabcd
    body = {
        'subnets': {
            'name': 'admin_external_subnet',
            'cidr': '172.70.0.0/24',
            'gateway_ip': '172.70.0.1',
            'allocation_pools': [{'start': '172.70.0.2', 'end': '172.70.0.100'}],
            'enable_dhcp': False
        }
    }
    ret_subnet_info = {
        'subnets': [
            {
                'name': 'admin_external_subnet',
                'cidr': '172.70.0.0/24',
                'ip_version': 4,
                'network_id': 0x1234,
                'gateway_ip': '172.70.0.1',
                'allocation_pools': [{'start': '172.70.0.2', 'end': '172.70.0.100'}],
                'enable_dhcp': False,
                'id': 0xabcd
            }
        ]
    }
    mock_create_subnet.return_value = ret_subnet_info
    neutron = Neutron(openrc=openrc_file)
    ret = neutron._create_subnet(body)
    assert ret == snid
    mock_create_subnet.assert_called_once_with(body)


@mock.patch('neutronclient.v2_0.client.Client.list_security_groups')
def test__list_security_groups_in_Neutron(mock_list_security_groups, openrc_conf_file_dir):
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    ret_security_groups = {
        'security_groups':
            [
                {
                    'name': 'default'
                }
            ]
    }
    security_groups_list = [
        {
            'name': 'default'
        }
    ]
    mock_list_security_groups.return_value = ret_security_groups
    neutron = Neutron(openrc=openrc_file)
    ret = neutron._list_security_groups()
    assert ret == security_groups_list
    mock_list_security_groups.assert_called_once_with()


@mock.patch.object(neutron.Neutron, '_list_security_groups')
def test_get_security_group_by_name_in_Neutron(mock__list_security_groups, openrc_conf_file_dir):
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    security_group_1 = {'name': 'default', 'security_group_id': 0x1234}
    security_group_2 = {'name': 'security_1', 'security_group_id': 0x2345}
    security_group_list = [security_group_1, security_group_2]
    mock__list_security_groups.return_value = security_group_list
    neutron = Neutron(openrc=openrc_file)
    ret = neutron.get_security_group_by_name(security_group_1['name'])
    assert ret == security_group_1
    mock__list_security_groups.assert_called_once_with()


@pytest.mark.parametrize('security_group, body, expected', [
    (
        {
            'security_group_rules':
                [
                    {
                        'direction': 'ingress',
                        'ethertype': 'IPv4',
                        'protocol': 'tcp',
                        'port_range_min': 22,
                        'port_range_max': 22,
                        'remote_ip_prefix': '0.0.0.0/0',
                    },
                    {
                        'direction': 'ingress',
                        'ethertype': 'IPv4',
                        'protocol': 'icmp',
                        'remote_ip_prefix': '0.0.0.0/0',
                    }
                ],
            'id': 0x1234
        },
        {
            'security_group_rule':
                {
                    'direction': 'ingress',
                    'ethertype': 'IPv4',
                    'protocol': 'tcp',
                    'port_range_min': 22,
                    'port_range_max': 22,
                    'remote_ip_prefix': '0.0.0.0/0',
                }
        }, True
    ),
    (
        {
            'security_group_rules':
                [
                    {
                        'direction': 'ingress',
                        'ethertype': 'IPv4',
                        'protocol': 'icmp',
                        'remote_ip_prefix': '0.0.0.0/0',
                    }
                ],
            'id': 0x1234
        },
        {
            'security_group_rule':
                {
                    'direction': 'ingress',
                    'ethertype': 'IPv4',
                    'protocol': 'tcp',
                    'port_range_min': 22,
                    'port_range_max': 22,
                    'remote_ip_prefix': '0.0.0.0/0',
                }
        }, False
    )])
def test__check_security_group_rule_conflict(security_group, body,
                                             expected, openrc_conf_file_dir):
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    neutron = Neutron(openrc=openrc_file)
    ret = neutron._check_security_group_rule_conflict(security_group, body)
    assert ret == expected


@pytest.mark.parametrize('ret__check_security_group_rule_conflict', [
    (True),
    (False)])
@mock.patch('neutronclient.v2_0.client.Client.create_security_group_rule')
@mock.patch.object(neutron.Neutron, '_check_security_group_rule_conflict')
def test_create_security_group_rule_in_Neutron(mock__check_security_group_rule_conflict,
                                               mock_create_security_group_rule,
                                               ret__check_security_group_rule_conflict,
                                               openrc_conf_file_dir):
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    security_group = {
        'security_group_rules':
            [
                {
                    'direction': 'ingress',
                    'ethertype': 'IPv4',
                    'protocol': 'tcp',
                    'port_range_min': 22,
                    'port_range_max': 22,
                    'remote_ip_prefix': '0.0.0.0/0',
                },
                {
                    'direction': 'ingress',
                    'ethertype': 'IPv4',
                    'protocol': 'icmp',
                    'remote_ip_prefix': '0.0.0.0/0',
                }
            ],
        'id': 0x1234
    }
    body = {
        'security_group_rule':
            {
                'direction': 'ingress',
                'ethertype': 'IPv4',
                'protocol': 'tcp',
                'port_range_min': 22,
                'port_range_max': 22,
                'remote_ip_prefix': '0.0.0.0/0',
            }
    }
    rule = {
        'security_group_rule':
            {
                'id': 0x1234
            }
    }
    mock__check_security_group_rule_conflict.return_value = ret__check_security_group_rule_conflict
    mock_create_security_group_rule.return_value = rule
    neutron = Neutron(openrc=openrc_file)
    neutron.create_security_group_rule(security_group, body)
    if ret__check_security_group_rule_conflict is False:
        mock_create_security_group_rule.assert_called_once_with(body=body)
    else:
        mock_create_security_group_rule.assert_not_called()
