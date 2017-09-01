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

from deploy.config.network import NetworkConfig


@pytest.fixture(scope="session")
def conf_file_dir(data_root):
    return os.path.join(data_root, 'lab_conf')


@pytest.mark.parametrize('network_file_name, metadatas, networks, interfaces, internal_vip, public_vip', [
    ('network_virtual1.yml',
     {'title': 'zte-virtual1 network config',
      'version': '0.1',
      'created': 'Tue Apr 11 2017',
      'comment': 'five vm node deploy'},
     [{'cidr': '10.20.11.0/24', 'gateway': '10.20.11.1',
       'ip_ranges': [{'start': '10.20.11.3', 'end': '10.20.11.10'}],
       'name': 'MANAGEMENT'},
      {'cidr': '10.20.11.0/24', 'gateway': '10.20.11.1',
       'ip_ranges': [{'start': '10.20.11.3', 'end': '10.20.11.10'}],
       'name': 'STORAGE'},
      {'cidr': '172.10.101.0/24', 'gateway': '172.10.101.1',
       'ip_ranges': [{'start': '172.10.101.2', 'end': '172.10.101.20'}],
       'name': 'EXTERNAL', 'network_name': 'admin_external', 'mapping': 'physnet1'},
      {'cidr': '10.20.11.0/24', 'gateway': '10.20.11.1',
       'ip_ranges': [{'start': '10.20.11.3', 'end': '10.20.11.10'}],
       'name': 'PUBLICAPI'},
      {'cidr': '10.20.11.0/24', 'gateway': '10.20.11.1',
       'ip_ranges': [{'start': '10.20.11.3', 'end': '10.20.11.10'}],
       'name': 'TENANT'},
      {'cidr': '100.20.11.0/24', 'gateway': '100.20.11.1',
       'ip_ranges': [{'start': '100.20.11.3', 'end': '100.20.11.10'}],
       'name': 'HEARTBEAT'}],
     [{'name': 'EXTERNAL', 'interface': 'ens8'},
      {'name': 'MANAGEMENT', 'interface': 'ens3'},
      {'name': 'PUBLICAPI', 'interface': 'ens3'},
      {'name': 'STORAGE', 'interface': 'ens3'},
      {'name': 'TENANT', 'interface': 'ens3'},
      {'name': 'HEARTBEAT', 'interface': 'ens9'}],
     '10.20.11.11',
     '10.20.11.11')])
def test_create_NetworkConf_instance(conf_file_dir, network_file_name, metadatas,
                                     networks, interfaces, internal_vip, public_vip):
    type2name = {
        'EXTERNAL': 'ext',
        'MANAGEMENT': 'man',
        'STORAGE': 'stor',
        'PUBLICAPI': 'pub',
        'TENANT': 'tenant',
        'HEARTBEAT': 'hbt',
    }

    network_file_path = os.path.join(conf_file_dir, network_file_name)
    NetworkConfClient = NetworkConfig(network_file_path)
    assert NetworkConfClient._file == network_file_path

    for key, val in metadatas.iteritems():
        assert getattr(NetworkConfClient, key) == val
    for network in networks:
        name = network['name']
        mapname = type2name[name]
        assert getattr(NetworkConfClient, mapname) == network
        for net_key, net_val in network.iteritems():
            net_name = '{}_{}'.format(mapname, net_key)
            assert getattr(NetworkConfClient, net_name) == net_val

    for interface in interfaces:
        name = interface['name']
        mapname = type2name[name]
        interface_name = '{}_{}'.format(mapname, 'iterface')
        assert getattr(NetworkConfClient, interface_name) == interface['interface']

    assert getattr(NetworkConfClient, 'internal_vip') == internal_vip
    assert getattr(NetworkConfClient, 'public_vip') == public_vip


@pytest.mark.parametrize('network_file_name, name, expected', [
    ('network_virtual1.yml', 'EXTERNAL',
     {'cidr': '172.10.101.0/24', 'gateway': '172.10.101.1',
      'ip_ranges': [{'start': '172.10.101.2', 'end': '172.10.101.20'}],
      'name': 'EXTERNAL', 'network_name': 'admin_external', 'mapping': 'physnet1'}),
    ('network_virtual1.yml', 'NO_EXIT', None)])
def test__get_network_NetworkConf(conf_file_dir, network_file_name, name, expected):
    network_file_path = os.path.join(conf_file_dir, network_file_name)
    NetworkConfClient = NetworkConfig(network_file_path)
    assert NetworkConfClient._get_network(name) == expected
