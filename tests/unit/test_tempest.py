##############################################################################
# Copyright (c) 2017 ZTE Corp and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import os
import sys
import pytest
from oslo_config import cfg
from tests.unit.daisyclient_stub import (
    StubTestHost,
    StubTestCluster,
    StubTestNet,
    StubTestRole,
    StubTestClient
)

import mock
sys.modules['daisyclient'] = mock.Mock()
sys.modules['daisyclient.v1'] = mock.Mock()
import deploy.tempest   # noqa: ignore=E402
from deploy.tempest import (
    parse,
    get_configure_from_daisyconf,
    get_endpoint,
    build_pxe_for_discover,
    install_os_for_vm_step1,
    install_os_for_bm_oneshot,
    install_os_for_vm_step2,
    discover_host,
    update_network,
    get_hosts,
    get_cluster,
    update_hosts_interface,
    add_host_role,
    enable_cinder_backend,
    enable_opendaylight
)   # noqa: ignore=E402


def get_val_index_in_list(key, list):
    return list.index(key) + 1


@pytest.mark.parametrize('argv', [
    (['--dha', '/home/zte/dairy/tests/data/deploy_virtual1.ymal', '--network',
      '/home/zte/dairy/tests/data/deploy_virtual1.ymal', '--cluster', 'yes', '--host',
      'yes', '--install', 'yes', '--isbare', '1', '--scenario', 'os-nosdn-nofeature-noha']),
    (['--dha', '/home/zte/dairy/tests/data/deploy_virtual1.ymal', '--network',
      '/home/zte/dairy/tests/data/deploy_virtual1.ymal', '--cluster', 'yes']),
    (['--dha', '/home/zte/dairy/tests/data/deploy_virtual1.ymal', '--network',
      '/home/zte/dairy/tests/data/deploy_virtual1.ymal', '--install', 'yes']),
    (['--dha', '/home/zte/dairy/tests/data/deploy_virtual1.ymal', '--network',
      '/home/zte/dairy/tests/data/deploy_virtual1.ymal', '--cluster', 'yes', '--host',
      'yes', '--install', 'yes', '--isbare', '1', '--scenario', 'os-nosdn-nofeature-noha'])])
def test_parser(argv):
    options_keys = ['dha', 'network', 'cluster', 'host', 'install', 'isbare', 'scenario']

    conf = cfg.ConfigOpts()
    parse(conf, argv)
    for option in options_keys:
        if conf[option]:
            if option == 'isbare':
                argv[argv.index('--' + option) + 1] = int(argv[argv.index('--' + option) + 1])
            assert conf[option] == argv[argv.index('--' + option) + 1]


@pytest.fixture(scope="module")
def conf_file_dir(data_root):
    return os.path.join(data_root, 'daisy_conf')


@pytest.mark.parametrize('section, key, exp', [
    ("PXE", "eth_name", 'ens3'),
    ("PXE", "build_pxe", 'no')])
def test_get_configure_from_daisyconf(section, key, exp, conf_file_dir):
    res_old_val = deploy.tempest.daisy_conf_path
    deploy.tempest.daisy_conf_path = os.path.join(conf_file_dir, 'daisy.conf')
    ret = get_configure_from_daisyconf(section, key)
    deploy.tempest.daisy_conf_path = res_old_val
    assert ret == exp


def test_get_endpoint(conf_file_dir):
    daisyrc_file_path = os.path.join(conf_file_dir, 'daisyrc_admin')
    exp = 'http://10.20.11.2:19292'
    ret = get_endpoint(daisyrc_file_path)
    assert ret == exp


def test_build_pxe_for_discover():
    client = StubTestClient()
    cluster_id = 0x123456
    deployment_interface = 'eth3'
    build_pxe_for_discover(cluster_id, client, deployment_interface)


def test_install_os_for_vm_step1():
    client = StubTestClient()
    cluster_id = 0x123456
    install_os_for_vm_step1(cluster_id, client)


def test_install_os_for_bm_oneshot():
    client = StubTestClient()
    cluster_id = 0x123456
    install_os_for_bm_oneshot(cluster_id, client)


def test_install_os_for_vm_step2():
    client = StubTestClient()
    cluster_id = 0x123456
    install_os_for_vm_step2(cluster_id, client)


@mock.patch('time.sleep')
@mock.patch('deploy.tempest.get_hosts')
def test_discover_host(mock_get_hosts, mock_sleep):
    hosts_name = ['computer01', 'computer02', 'controller01', 'controller02', 'controller03']
    mock_get_hosts.return_value = hosts_name
    client = StubTestClient()
    discover_host(hosts_name, client)
    mock_sleep.assert_not_called()


def test_update_network():
    client = StubTestClient()
    cluster_id = 1
    network_map = {'MANAGEMENT': {'cidr': '10.20.11.0/24', 'gateway': '10.20.11.1',
                                  'ip_ranges': [{'start': '10.20.11.3', 'end': '10.20.11.10'}]},
                   'STORAGE': {'cidr': '10.20.11.0/24', 'gateway': '10.20.11.1',
                               'ip_ranges': [{'start': '10.20.11.3', 'end': '10.20.11.10'}]}}
    metadata_net1 = {'cidr': '10.20.11.0/24', 'gateway': '10.20.11.1',
                     'ip_ranges': [{'start': '10.20.11.3', 'end': '10.20.11.10'}]}
    net1 = StubTestNet(0x1234, 'MANAGEMENT', 1, **metadata_net1)
    client.networks.add(net1)
    metadata_net2 = {'cidr': '10.20.11.0/24', 'gateway': '10.20.11.1',
                     'ip_ranges': [{'start': '10.20.11.3', 'end': '10.20.11.10'}]}
    net2 = StubTestNet(0x2345, 'STORAGE', 1, **metadata_net2)
    client.networks.add(net2)
    exp_nets_data = [metadata_net1, metadata_net2]
    update_network(cluster_id, network_map, client)
    for i in range(len(exp_nets_data)):
        assert client.networks.networks[i].metadata == exp_nets_data[i]


def test_get_hosts():
    client = StubTestClient()
    host1 = StubTestHost(0x1234, 'test_host_1', 1,
                         [{'name': 'ens8', 'mac': '11:11:11:11:11:11'}])
    client.hosts.add(host1)
    host2 = StubTestHost(0x2345, 'test_host_2', 1,
                         [{'name': 'ens3', 'mac': '22:22:22:22:22:22'}])
    client.hosts.add(host2)
    exp = [host1, host2]
    ret = get_hosts(client)
    assert ret == exp


def test_get_cluster():
    client = StubTestClient()
    cluster1 = StubTestCluster(1, 'test_cluster_1')
    client.clusters.add(cluster1)
    cluster2 = StubTestCluster(2, 'test_cluster_2')
    client.clusters.add(cluster2)
    exp = 'test_cluster_2'
    ret = get_cluster(client)
    assert ret == exp


@pytest.mark.parametrize('isbare', [
    (False), (True)])
def test_update_hosts_interface(isbare, tmpdir):
    res_old_val = deploy.tempest.iso_path
    deploy.tempest.iso_path = os.path.join(tmpdir.dirname, tmpdir.basename) + '/'
    iso_file_path = os.path.join(deploy.tempest.iso_path, 'test_os.iso')
    with open(iso_file_path, 'a') as f:
        f.write('test_data')
    client = StubTestClient()
    cluster_id = 1
    host_id1 = 0x1234
    host_id2 = 0x2345
    host_id3 = 0x3456
    host1 = StubTestHost(host_id1, 'controller01', cluster_id, [{'name': 'ens8', 'mac': '11:11:11:11:11:11'}])
    client.hosts.add(host1)
    host2 = StubTestHost(host_id2, 'controller02', cluster_id, [{'name': 'ens3', 'mac': '22:22:22:22:22:22'}])
    client.hosts.add(host2)
    host3 = StubTestHost(host_id3, 'computer01', cluster_id, [{'name': 'ens9', 'mac': '33:33:33:33:33:33'}])
    client.hosts.add(host3)
    hosts_info = [host1, host2, host3]
    role1 = StubTestRole(0xaaaa, 'CONTROLLER_LB', cluster_id)
    client.roles.add(role1)
    role2 = StubTestRole(0xbbbb, 'COMPUTER', cluster_id)
    client.roles.add(role2)
    mac_address_map = {
        'controller01': ['11:11:11:11:11:11'], 'controller02': ['22:22:22:22:22:22'], 'controller03': [],
        'computer01': ['33:33:33:33:33:33'], 'computer02': []}
    host_interface_map = {
        'ens8': [{'ip': '', 'name': 'EXTERNAL'}],
        'ens3': [{'ip': '', 'name': 'MANAGEMENT'},
                 {'ip': '', 'name': 'PUBLICAPI'},
                 {'ip': '', 'name': 'STORAGE'},
                 {'ip': '', 'name': 'physnet1'}],
        'ens9': [{'ip': '', 'name': 'HEARTBEAT'}]}
    vip = '10.20.11.11'
    update_hosts_interface(1, hosts_info, mac_address_map,
                        host_interface_map,
                        vip, isbare, client, True)
    deploy.tempest.iso_path = res_old_val
    if isbare:
        assert client.hosts.get(host_id1).metadata == {
            'id': host_id1, 'name': 'controller01', 'cluster_id': cluster_id,
            'cluster': cluster_id, 'os_version': iso_file_path,
            'ipmi_user': 'zteroot', 'ipmi_passwd': 'superuser',
            'interfaces': [{'name': 'ens8', 'mac': '11:11:11:11:11:11',
                            'assigned_networks': [{'ip': '', 'name': 'EXTERNAL'}]}],
        }
        assert client.hosts.get(host_id2).metadata == {
            'id': host_id2, 'name': 'controller02', 'cluster_id': cluster_id,
            'cluster': cluster_id, 'os_version': iso_file_path,
            'ipmi_user': 'zteroot', 'ipmi_passwd': 'superuser',
            'interfaces': [{'name': 'ens3', 'mac': '22:22:22:22:22:22',
                            'assigned_networks': [
                                {'ip': '', 'name': 'MANAGEMENT'},
                                {'ip': '', 'name': 'PUBLICAPI'},
                                {'ip': '', 'name': 'STORAGE'},
                                {'ip': '', 'name': 'physnet1'}]}],
        }
        assert client.hosts.get(host_id3).metadata == {
            'id': host_id3, 'name': 'computer01', 'cluster_id': cluster_id,
            'cluster': cluster_id, 'os_version': iso_file_path,
            'ipmi_user': 'zteroot', 'ipmi_passwd': 'superuser',
            'interfaces': [{'name': 'ens9', 'mac': '33:33:33:33:33:33',
                            'assigned_networks': [{'ip': '', 'name': 'HEARTBEAT'}]}],
        }
    else:
        assert client.hosts.get(host_id1).metadata == {
            'id': host_id1, 'name': 'controller01', 'cluster_id': cluster_id,
            'cluster': cluster_id, 'os_version': iso_file_path,
            'interfaces': [{'name': 'ens8', 'mac': '11:11:11:11:11:11',
                            'assigned_networks': [{'ip': '', 'name': 'EXTERNAL'}]}],
        }
        assert client.hosts.get(host_id2).metadata == {
            'id': host_id2, 'name': 'controller02', 'cluster_id': cluster_id,
            'cluster': cluster_id, 'os_version': iso_file_path,
            'interfaces': [{'name': 'ens3', 'mac': '22:22:22:22:22:22',
                            'assigned_networks': [
                                {'ip': '', 'name': 'MANAGEMENT'},
                                {'ip': '', 'name': 'PUBLICAPI'},
                                {'ip': '', 'name': 'STORAGE'},
                                {'ip': '', 'name': 'physnet1'}]}],
        }
        assert client.hosts.get(host_id3).metadata == {
            'id': host_id3, 'name': 'computer01', 'cluster_id': cluster_id,
            'cluster': cluster_id, 'os_version': iso_file_path,
            'interfaces': [{'name': 'ens9', 'mac': '33:33:33:33:33:33',
                            'assigned_networks': [{'ip': '', 'name': 'HEARTBEAT'}]}],
        }
    tmpdir.remove()


@pytest.mark.parametrize('dha_host_name, cluster_id, host_id, vip, exp', [
    ('controller01', 1, 0x1234, '10.20.11.11', {'nodes': [0x1234], 'cluster_id': 1, 'vip': '10.20.11.11'}),
    ('computer01', 1, 0x2345, '10.20.11.11', {'nodes': [0x2345], 'cluster_id': 1}),
    ('all_in_one', 1, 0x1234, '10.20.11.11',
     [{'nodes': [0x1234], 'cluster_id': 1, 'vip': '10.20.11.11'},
      {'nodes': [0x1234], 'cluster_id': 1}])])
def test_add_host_role(dha_host_name, cluster_id, host_id, vip, exp):
    client = StubTestClient()
    role1 = StubTestRole(0x1234, 'CONTROLLER_LB', 1)
    client.roles.add(role1)
    role2 = StubTestRole(0x2345, 'COMPUTER', 1)
    client.roles.add(role2)
    add_host_role(cluster_id, host_id, dha_host_name, vip, client)
    if dha_host_name == 'controller01':
        assert client.roles.roles[0].metadata == exp
    if dha_host_name == 'computer01':
        assert client.roles.roles[1].metadata == exp
    if dha_host_name == 'all_in_one':
        assert client.roles.roles[0].metadata == exp[0]
        assert client.roles.roles[1].metadata == exp[1]


def test_enable_cinder_backend():
    client = StubTestClient()
    role1 = StubTestRole(0x1234, 'CONTROLLER_LB', 1)
    client.roles.add(role1)
    service_name = 'ceph'
    disk_name = '/dev/sdb'
    protocol_type = 'RAW'
    exp_disk_meta = {'service': service_name,
                     'disk_location': 'local',
                     'partition': disk_name,
                     'protocol_type': protocol_type,
                     'role_id': 0x1234}
    enable_cinder_backend(1, service_name, disk_name, protocol_type, client)
    assert client.disk_array.disks[0] == exp_disk_meta


@pytest.mark.parametrize('layer, exp', [
    ('odl_l3', {
        'neutron_backends_array': [{'zenic_ip': '',
                                    'sdn_controller_type': 'opendaylight',
                                    'zenic_port': '',
                                    'zenic_user_password': '',
                                    'neutron_agent_type': '',
                                    'zenic_user_name': '',
                                    'enable_l2_or_l3': 'l3'}]}),
    ('odl_l2', {
        'neutron_backends_array': [{'zenic_ip': '',
                                    'sdn_controller_type': 'opendaylight',
                                    'zenic_port': '',
                                    'zenic_user_password': '',
                                    'neutron_agent_type': '',
                                    'zenic_user_name': '',
                                    'enable_l2_or_l3': 'l2'}]})])
def test_enable_opendaylight(layer, exp):
    client = StubTestClient()
    role1 = StubTestRole(0x1234, 'CONTROLLER_LB', 1)
    client.roles.add(role1)
    enable_opendaylight(1, layer, client)
    assert client.roles.roles[0].metadata == exp
