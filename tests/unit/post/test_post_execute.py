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

from deploy.post.execute import (
    _config_external_network,
    _config_icmp_security_group_rule,
    _config_ssh_security_group_rule,
    _config_kolla_admin_openrc
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
    dst_globals_file_path = os.path.join(tmpdir.dirname, 'globals.yml')
    shutil.copyfile(src_globals_file_path, dst_globals_file_path)

    src_openrc_file_path = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    dst_openrc_file_path = os.path.join(tmpdir.dirname, 'admin-openrc.sh')
    shutil.copyfile(src_openrc_file_path, dst_openrc_file_path)

    _config_kolla_admin_openrc(tmpdir.dirname)
    src_openrc_lines = open(src_openrc_file_path, 'r').readlines()
    dst_openrc_lines = open(dst_openrc_file_path, 'r').readlines()
    if globals_file_name == 'globals.yml':
        assert DeepDiff(src_openrc_lines, dst_openrc_lines, ignore_order=True) == {}
    elif globals_file_name == 'globals_odl.yml':
        diff = DeepDiff(src_openrc_lines, dst_openrc_lines, ignore_order=True)
        assert len(diff) == 1 and diff.get('iterable_item_added') != None
        assert len(diff['iterable_item_added']) == 1
        for val in diff['iterable_item_added'].values():
            assert 'export SDN_CONTROLLER_IP' in val
    tmpdir.remove()
