##############################################################################
# Copyright (c) 2017 ZTE Corp and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import shutil
import os

from deepdiff import DeepDiff
import pytest
import mock

from deploy.post import execute
from deploy.post.execute import (
    _config_external_network,
    _config_external_subnet,
    _config_icmp_security_group_rule,
    _config_ssh_security_group_rule,
    _config_kolla_admin_openrc,
    _create_external_network,
    _create_flavor_m1_micro,
    _prepare_cirros,
    _create_image_TestVM,
    _create_security_group_rules
)


@pytest.mark.parametrize('ext_name, physnet, expected', [
    ('EXTERNAL', 'ens8',
     {
         'network': {
             'name': 'EXTERNAL',
             'admin_state_up': True,
             'shared': False,
             'provider:network_type': 'flat',
             'provider:physical_network': 'ens8',
             'router:external': True
         }
     }),
    ('EXTERNAL', 'ens3',
     {
         'network': {
             'name': 'EXTERNAL',
             'admin_state_up': True,
             'shared': False,
             'provider:network_type': 'flat',
             'provider:physical_network': 'ens3',
             'router:external': True
         }
     })])
def test__config_external_network(ext_name, physnet, expected):
    assert _config_external_network(ext_name, physnet) == expected


@pytest.mark.parametrize('ext_id, network_conf, expected', [
    (0x1234,
     {
         'ext_network_name': 'admin_external',
         'ext_cidr': '172.70.0.0/24',
         'ext_gateway': '172.70.0.1',
         'ext_ip_ranges': [{'start': '172.70.0.2', 'end': '172.70.0.100'}]
     },
     {
         'subnets': [
             {
                 'name': 'admin_external_subnet',
                 'cidr': '172.70.0.0/24',
                 'ip_version': 4,
                 'network_id': 0x1234,
                 'gateway_ip': '172.70.0.1',
                 'allocation_pools': [{'start': '172.70.0.2', 'end': '172.70.0.100'}],
                 'enable_dhcp': False
             }
         ]
     })])
def test__config_external_subnet(ext_id, network_conf, expected):
    class Network_conf():
        def __init__(self, network_name, cidr, gateway, ip_ranges):
            self.ext_network_name = network_name
            self.ext_cidr = cidr
            self.ext_gateway = gateway
            self.ext_ip_ranges = ip_ranges

    network_conf_inst = Network_conf(network_conf['ext_network_name'],
                                     network_conf['ext_cidr'],
                                     network_conf['ext_gateway'],
                                     network_conf['ext_ip_ranges'])
    assert _config_external_subnet(ext_id, network_conf_inst) == expected


@pytest.mark.parametrize('security_group_id, expected', [
    ('0x1111',
     {
         'security_group_rule': {
             'direction': 'ingress',
             'ethertype': 'IPv4',
             'protocol': 'icmp',
             'remote_ip_prefix': '0.0.0.0/0',
             'security_group_id': '0x1111'
         }
     }),
    ('0xaaaa',
     {
         'security_group_rule': {
             'direction': 'ingress',
             'ethertype': 'IPv4',
             'protocol': 'icmp',
             'remote_ip_prefix': '0.0.0.0/0',
             'security_group_id': '0xaaaa'
         }
     })])
def test__config_icmp_security_group_rule(security_group_id, expected):
    assert _config_icmp_security_group_rule(security_group_id) == expected


@pytest.mark.parametrize('security_group_id, expected', [
    ('0x1111',
     {
         'security_group_rule': {
             'direction': 'ingress',
             'ethertype': 'IPv4',
             'protocol': 'tcp',
             'port_range_min': 22,
             'port_range_max': 22,
             'remote_ip_prefix': '0.0.0.0/0',
             'security_group_id': '0x1111'
         }
     }),
    ('0xaaaa',
     {
         'security_group_rule': {
             'direction': 'ingress',
             'ethertype': 'IPv4',
             'protocol': 'tcp',
             'port_range_min': 22,
             'port_range_max': 22,
             'remote_ip_prefix': '0.0.0.0/0',
             'security_group_id': '0xaaaa'
         }
     })])
def test__config_ssh_security_group_rule(security_group_id, expected):
    assert _config_ssh_security_group_rule(security_group_id) == expected


@pytest.fixture(scope="module")
def openrc_conf_file_dir(data_root):
    return os.path.join(data_root, 'openrc_conf')


@pytest.mark.parametrize('globals_file_name', [
    ('globals.yml'), ('globals_odl.yml')])
def test__config_kolla_admin_openrc(globals_file_name, openrc_conf_file_dir, tmpdir):
    src_globals_file_path = os.path.join(openrc_conf_file_dir, globals_file_name)
    dst_globals_file_path = os.path.join(tmpdir.dirname, tmpdir.basename, 'globals.yml')
    shutil.copyfile(src_globals_file_path, dst_globals_file_path)

    src_openrc_file_path = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    dst_openrc_file_path = os.path.join(tmpdir.dirname, tmpdir.basename, 'admin-openrc.sh')
    shutil.copyfile(src_openrc_file_path, dst_openrc_file_path)

    _config_kolla_admin_openrc(os.path.join(tmpdir.dirname, tmpdir.basename))
    src_openrc_lines = open(src_openrc_file_path, 'r').readlines()
    dst_openrc_lines = open(dst_openrc_file_path, 'r').readlines()
    if globals_file_name == 'globals.yml':
        assert DeepDiff(src_openrc_lines, dst_openrc_lines, ignore_order=True) == {}
    elif globals_file_name == 'globals_odl.yml':
        diff = DeepDiff(src_openrc_lines, dst_openrc_lines, ignore_order=True)
        assert len(diff) == 1 and diff.get('iterable_item_added') is not None
        assert len(diff['iterable_item_added']) == 3
        diffvals = ','.join(diff['iterable_item_added'].values())
        assert 'export SDN_CONTROLLER_IP' in diffvals
        assert 'export SDN_CONTROLLER_WEBPORT=' in diffvals
        assert 'export SDN_CONTROLLER_RESTCONFPORT=' in diffvals

    tmpdir.remove()


@pytest.fixture(scope="module")
def net_conf_file_dir(data_root):
    return os.path.join(data_root, 'lab_conf')


@mock.patch.object(execute.neutron.Neutron, 'create_network')
@mock.patch.object(execute.neutron.Neutron, 'create_subnet')
def test__create_external_network_with_openrc(mock_create_subnet, mock_create_network,
                                              net_conf_file_dir, openrc_conf_file_dir):
    external_network_info = {
        'network': {
            'name': 'admin_external',
            'admin_state_up': True,
            'shared': False,
            'provider:network_type': 'flat',
            'provider:physical_network': 'physnet1',
            'router:external': True
        }
    }
    external_subnet_info = {
        'subnets': [
            {
                'name': 'admin_external_subnet',
                'cidr': '172.70.0.0/24',
                'ip_version': 4,
                'network_id': 0x1234,
                'gateway_ip': '172.70.0.1',
                'allocation_pools': [{'start': '172.70.0.2', 'end': '172.70.0.100'}],
                'enable_dhcp': False
            }
        ]
    }
    network_file = os.path.join(net_conf_file_dir, 'network_baremetal.yml')
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    mock_create_network.return_value = 0x1234
    mock_create_subnet.return_value = 0xabcd
    _create_external_network(network_file, openrc_file)
    mock_create_network.assert_called_once_with('admin_external', external_network_info)
    mock_create_subnet.assert_called_once_with(external_subnet_info)


@mock.patch.object(execute.neutron.Neutron, 'create_network')
@mock.patch.object(execute.neutron.Neutron, 'create_subnet')
@mock.patch('deploy.post.execute.neutron.Neutron')
def test__create_external_network_without_openrc(mock_Neutron, mock_create_subnet, mock_create_network,
                                                 net_conf_file_dir):
    network_file = os.path.join(net_conf_file_dir, 'network_baremetal.yml')
    mock_create_network.return_value = 0x1234
    mock_create_subnet.return_value = 0xabcd
    _create_external_network(network_file)
    mock_create_network.assert_not_called()
    mock_create_subnet.assert_not_called()


@pytest.mark.parametrize('flavor,', [
    (None),
    ({'name': 'm1.micro', 'ram': 64})])
@mock.patch.object(execute.nova.Nova, 'get_flavor_by_name')
@mock.patch.object(execute.nova.Nova, 'create_flavor')
def test__create_flavor_m1_micro(mock_create_flavor, mock_get_flavor_by_name,
                                 openrc_conf_file_dir, flavor):
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    mock_create_flavor.return_value = True
    mock_get_flavor_by_name.return_value = flavor
    _create_flavor_m1_micro(openrc_file)
    mock_get_flavor_by_name.assert_called_once_with('m1.micro')
    if flavor is None:
        mock_create_flavor.assert_called_once_with('m1.micro', ram=64, vcpus=1, disk=0)
    else:
        mock_create_flavor.assert_not_called()


@mock.patch('deploy.post.execute.os.system')
def test__prepare_cirros(mock_system):
    mock_system.return_value = 0
    _prepare_cirros()
    assert mock_system.call_count == 3


@pytest.mark.parametrize('image_path, image_info', [
    (None, None),
    ('/var/lib/daisy/images/cirros-0.3.5-x86_64-disk.img', None),
    (None, {'name': 'TestVM'}),
    ('/var/lib/daisy/images/cirros-0.3.5-x86_64-disk.img', {'name': 'TestVM'})])
@mock.patch('deploy.post.execute._prepare_cirros')
@mock.patch('deploy.post.execute.err_exit')
@mock.patch.object(execute.glance.Glance, 'create')
@mock.patch.object(execute.glance.Glance, 'get_by_name')
def test__create_image_TestVM(mock_get_by_name, mock_create,
                              mock_err_exit, mock___prepare_cirros,
                              image_path, image_info,
                              openrc_conf_file_dir):
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    mock_get_by_name.return_value = image_info
    mock_create.return_value = 0x1234
    mock___prepare_cirros.return_value = image_path
    _create_image_TestVM(openrc_file)
    mock_get_by_name.assert_called_once_with('TestVM')
    if image_info:
        mock___prepare_cirros.assert_not_called()
    else:
        mock___prepare_cirros.assert_called_once_with()
        if image_path:
            mock_create.assert_called_once_with('TestVM', image_path)
        else:
            mock_err_exit.assert_called_once_with("Test image preparation failed")


@mock.patch.object(execute.neutron.Neutron, 'create_security_group_rule')
@mock.patch.object(execute.neutron.Neutron, 'get_security_group_by_name')
def test__create_security_group_rules(mock_get_security_group_by_name, mock_create_security_group_rule,
                                      openrc_conf_file_dir):
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    mock_get_security_group_by_name.return_value = {'id': 0xaaaa}
    _create_security_group_rules(openrc_file)
    mock_get_security_group_by_name.assert_called_once_with('default')
    assert mock_create_security_group_rule.call_count == 2
