#!/usr/bin/python
##############################################################################
# Copyright (c) 2016 ZTE Coreporation and others.
# hu.zhijiang@zte.com.cn
# lu.yao135@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from oslo_config import cfg
import sys
from daisyclient.v1 import client as daisy_client
import get_conf
import traceback
import time
import os
import ConfigParser

from utils import err_exit


daisy_version = 1.0
daisyrc_path = "/root/daisyrc_admin"
daisy_conf_path = "/home/daisy_install/daisy.conf"
iso_path = "/var/lib/daisy/kolla/"
deployment_interface = "ens3"
cluster_name = "clustertest"

_CLI_OPTS = [
    cfg.StrOpt('dha',
               help='The dha file path'),
    cfg.StrOpt('network',
               help='The network file path'),
    cfg.StrOpt('cluster',
               help='Config cluster'),
    cfg.StrOpt('host',
               help='Config host'),
    cfg.StrOpt('install',
               help='install daisy'),
    cfg.IntOpt('isbare',
               help='deploy environment'),
    cfg.StrOpt('scenario',
               help='deploy scenario'),
]


# ------------------------------------------------------------------------------------------
def parse(conf, args):
    conf.register_cli_opts(_CLI_OPTS)
    conf(args=args)


def print_bar(msg):
    print ("--------------------------------------------")
    print (msg)
    print ("--------------------------------------------")


def get_configure_from_daisyconf(section, key):
    config = ConfigParser.ConfigParser()
    config.read(daisy_conf_path)
    option_value = config.get(section, key)
    return option_value


def get_endpoint(file_path):
    for line in open(file_path):
        if 'OS_ENDPOINT' in line:
            daisyrc_admin_line = line.strip()
            daisy_endpoint = daisyrc_admin_line.split("=")[1]
    return daisy_endpoint


def prepare_install():
    global deployment_interface
    try:
        print("get config...")
        conf = cfg.ConfigOpts()
        parse(conf, sys.argv[1:])
        host_interface_map, hosts_name, network_map, vip, ceph_disk_name, mac_address_map = \
            get_conf.config(conf['dha'], conf['network'])
        if conf['cluster'] and conf['cluster'] == 'yes':
            print("add cluster...")
            cluster_meta = {'name': cluster_name, 'description': '',
                            'target_systems': 'os+kolla'}
            clusters_info = client.clusters.add(**cluster_meta)
            cluster_id = clusters_info.id
            print("cluster_id=%s." % cluster_id)
            print("update network...")
            update_network(cluster_id, network_map)
            print("build pxe server to install os...")
            deployment_interface = get_configure_from_daisyconf("PXE", "eth_name")
            build_pxe_for_discover(cluster_id, client, deployment_interface)
        elif conf['host'] and conf['host'] == 'yes':
            isbare = False if 'isbare' in conf and conf['isbare'] == 0 else True
            print("discover host...")
            discover_host(hosts_name)
            time.sleep(10)
            print("update hosts interface...")
            hosts_info = get_hosts()
            cluster_info = get_cluster(client)
            cluster_id = cluster_info.id
            add_hosts_interface(cluster_id, hosts_info, mac_address_map,
                                host_interface_map, vip, isbare, client)
            if len(hosts_name) == 1:
                protocol_type = 'LVM'
                service_name = 'cinder'
            elif len(hosts_name) > 2:
                protocol_type = 'RAW'
                service_name = 'ceph'
            else:
                print('hosts_num is %s' % len(hosts_name))
                protocol_type = None
            enable_cinder_backend(cluster_id, service_name,
                                  ceph_disk_name, protocol_type, client)

            if 'scenario' in conf:
                if 'odl_l3' in conf['scenario'] or \
                    'odl' in conf['scenario']:
                    enable_opendaylight(cluster_id, 'odl_l3', client)
                elif 'odl_l2' in conf['scenario']:
                    enable_opendaylight(cluster_id, 'odl_l2', client)

            if not isbare:
                install_os_for_vm_step1(cluster_id, client)
            else:
                print("daisy baremetal deploy start")
                install_os_for_bm_oneshot(cluster_id, client)
        elif conf['install'] and conf['install'] == 'yes':
            cluster_info = get_cluster(client)
            cluster_id = cluster_info.id
            install_os_for_vm_step2(cluster_id, client)

    except Exception:
        print("Deploy failed!!!.%s." % traceback.format_exc())
        sys.exit(1)
    else:
        print_bar("Everything is done!")


def build_pxe_for_discover(cluster_id, client, deployment_interface):
    cluster_meta = {'cluster_id': cluster_id,
                    'deployment_interface': deployment_interface}
    client.install.install(**cluster_meta)


def install_os_for_vm_step1(cluster_id, client):
    cluster_meta = {'cluster_id': cluster_id,
                    'pxe_only': "true"}
    client.install.install(**cluster_meta)


def install_os_for_bm_oneshot(cluster_id, client):
    cluster_meta = {'cluster_id': cluster_id}
    client.install.install(**cluster_meta)


def install_os_for_vm_step2(cluster_id, client):
    cluster_meta = {'cluster_id': cluster_id,
                    'skip_pxe_ipmi': "true"}
    client.install.install(**cluster_meta)


def discover_host(hosts_name):
    while True:
        hosts_info = get_hosts()
        if len(hosts_info) == len(hosts_name):
            print('discover hosts success!')
            break
        else:
            time.sleep(10)


def update_network(cluster_id, network_map, client):
    network_meta = {'filters': {'cluster_id': cluster_id}}
    network_info_gernerator = client.networks.list(**network_meta)
    for net in network_info_gernerator:
        network_id = net.id
        network_name = net.name
        if network_map.get(network_name):
            network_meta = network_map[network_name]
            client.networks.update(network_id, **network_meta)


def get_hosts(client):
    hosts_list_generator = client.hosts.list()
    hosts_info = []
    for host in hosts_list_generator:
        host_info = client.hosts.get(host.id)
        hosts_info.append(host_info)
    return hosts_info


def get_cluster(client):
    cluster_list_generator = client.clusters.list()
    for cluster in cluster_list_generator:
        cluster_info = client.clusters.get(cluster.id)
    return cluster_info


def add_hosts_interface(cluster_id, hosts_info, mac_address_map,
                        host_interface_map,
                        vip, isbare, client):
    for host in hosts_info:
        dha_host_name = None
        host = host.to_dict()
        host['cluster'] = cluster_id
        if isbare:
            host['ipmi_user'] = 'zteroot'
            host['ipmi_passwd'] = 'superuser'
        for interface in host['interfaces']:
            interface_name = interface['name']
            if interface_name in host_interface_map:
                interface['assigned_networks'] = \
                    host_interface_map[interface_name]
            for nodename in mac_address_map:
                if interface['mac'] in mac_address_map[nodename]:
                    dha_host_name = nodename

        if dha_host_name is None:
            err_exit('Failed to find host name by mac address map: %r'
                     % mac_address_map)

        pathlist = os.listdir(iso_path)
        for filename in pathlist:
            if filename.endswith('iso'):
                host['os_version'] = iso_path + filename
        if host['os_version'] == iso_path:
            print("do not have os iso file in /var/lib/daisy/kolla/.")
        client.hosts.update(host['id'], **host)
        print("update role...")
        add_host_role(cluster_id, host['id'], dha_host_name, vip, client)


def add_host_role(cluster_id, host_id, dha_host_name, vip, client):
    role_meta = {'filters': {'cluster_id': cluster_id}}
    role_list_generator = client.roles.list(**role_meta)
    role_list = [role for role in role_list_generator]
    lb_role_id = [role.id for role in role_list if
                  role.name == "CONTROLLER_LB"][0]
    computer_role_id = [role.id for role in role_list if
                        role.name == "COMPUTER"][0]
    if dha_host_name in ['all_in_one']:
        role_lb_update_meta = {'nodes': [host_id],
                               'cluster_id': cluster_id, 'vip': vip}
        client.roles.update(lb_role_id, **role_lb_update_meta)
        role_computer_update_meta = {'nodes': [host_id],
                                     'cluster_id': cluster_id}
        client.roles.update(computer_role_id, **role_computer_update_meta)
    if dha_host_name in ['controller01', 'controller02', 'controller03']:
        role_lb_update_meta = {'nodes': [host_id],
                               'cluster_id': cluster_id, 'vip': vip}
        client.roles.update(lb_role_id, **role_lb_update_meta)
    if dha_host_name in ['computer01', 'computer02', 'computer03', 'computer04']:
        role_computer_update_meta = {'nodes': [host_id],
                                     'cluster_id': cluster_id}
        client.roles.update(computer_role_id, **role_computer_update_meta)


def enable_cinder_backend(cluster_id, service_name, disk_name, protocol_type, client):
    role_meta = {'filters': {'cluster_id': cluster_id}}
    role_list_generator = client.roles.list(**role_meta)
    lb_role_id = [role.id for role in role_list_generator if
                  role.name == "CONTROLLER_LB"][0]
    service_disk_meta = {'service': service_name,
                         'disk_location': 'local',
                         'partition': disk_name,
                         'protocol_type': protocol_type,
                         'role_id': lb_role_id}
    try:
        client.disk_array.service_disk_add(**service_disk_meta)
    except Exception as e:
        print e


def enable_opendaylight(cluster_id, layer, client):
    role_meta = {'filters': {'cluster_id': cluster_id}}
    role_list_generator = client.roles.list(**role_meta)
    lb_role_id = [role.id for role in role_list_generator if
                  role.name == "CONTROLLER_LB"][0]
    odl_layer = 'l3'
    if 'odl_l3' == layer:
        odl_layer = 'l3'
    elif 'odl_l2' == layer:
        odl_layer = 'l2'
    neutron_backend_info = {
        'neutron_backends_array': [{'zenic_ip': '',
                                    'sdn_controller_type': 'opendaylight',
                                    'zenic_port': '',
                                    'zenic_user_password': '',
                                    'neutron_agent_type': '',
                                    'zenic_user_name': '',
                                    'enable_l2_or_l3': odl_layer}]}
    try:
        client.roles.update(lb_role_id, **neutron_backend_info)
    except Exception as e:
        print e


if __name__ == "__main__":
    daisy_endpoint = get_endpoint(daisyrc_path)
    client = daisy_client.Client(version=daisy_version, endpoint=daisy_endpoint)
    prepare_install()
