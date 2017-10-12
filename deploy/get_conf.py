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
import yaml
from oslo_config import cfg
import sys

_CLI_OPTS = [
    cfg.StrOpt('dha',
               help='The dha file path'),
]


def init(file):
    with open(file) as fd:
        return yaml.safe_load(fd)


def decorator_mk(types):
    def decorator(func):
        def wrapter(data):
            item_list = data.get(types, [])
            result = {}
            for item in item_list:
                ret = func(item)
                item_name = ret.keys().pop()
                if result is not None and item_name in result:
                    result[item_name] = result[item_name] + ret[item_name]
                else:
                    result.update(ret)
            return result
        return wrapter
    return decorator


@decorator_mk('networks')
def network(network=None):
    net_plane = network.get('name', '')
    if net_plane == "TENANT":
        net_plane = "physnet1"
    network.pop('name')
    map = {}
    map[net_plane] = network
    return map


@decorator_mk('interfaces')
def interface(interface=None):
    net_name = interface.get('name', '')
    if net_name == "TENANT":
        net_name = "physnet1"
    interface_name = interface.get('interface', '')
    map2 = {}
    map = {'name': net_name}
    map2[interface_name] = [map]
    return map2


@decorator_mk('hosts')
def role(host=None):
    hostname = host.get('name', '')
    role = host.get('roles', '')
    map = {}
    map[hostname] = role
    return map


@decorator_mk('hosts')
def host(host=None):
    hostip = host.get('ip', [])
    passwd = host.get('password', [])
    map = {}
    map = {'ip': hostip, 'passwd': passwd}
    return map


@decorator_mk('hosts')
def mac_address(host=None):
    mac_addresses = host.get('mac_addresses', [])
    map = {host['name']: mac_addresses}
    return map


def network_config_parse(network_data):
    network_map = network(network_data)
    vip = network_data.get('internal_vip')
    interface_map = interface(network_data)
    return network_map, vip, interface_map


def dha_config_parse(dha_data):
    host_role_map = role(dha_data)
    hosts_name = []
    for name in host_role_map:
        hosts_name.append(name)
    return hosts_name


def config(dha_file, network_file):
    dha_data = init(dha_file)
    ceph_disk_name = dha_data.get('ceph_disk_name')
    hosts_name = dha_config_parse(dha_data)
    mac_address_map = mac_address(dha_data)
    network_data = init(network_file)
    network_map, vip, interface_map = network_config_parse(network_data)
    return interface_map, hosts_name, network_map, vip, ceph_disk_name, mac_address_map


def parse(conf, args):
    conf.register_cli_opts(_CLI_OPTS)
    conf(args=args)


def get_yml_para(dha_file):
    data = init(dha_file)
    disks = data.get("disks", 0)
    daisyserver_size = disks.get("daisy", 0)
    controller_node_size = disks.get("controller", 0)
    compute_node_size = disks.get("compute", 0)
    daisy_passwd = data.get("daisy_passwd", "")
    daisy_ip = data.get("daisy_ip", "")
    daisy_gateway = data.get("daisy_gateway", "")
    daisy_target_node = data.get("hosts", "")
    hosts_num = len(daisy_target_node)
    return daisyserver_size, controller_node_size,\
        compute_node_size, daisy_passwd, daisy_ip, daisy_gateway,\
        hosts_num


def get_conf_from_deploy():
    conf = cfg.ConfigOpts()
    parse(conf, sys.argv[1:])
    daisyserver_size, controller_node_size, compute_node_size,\
        daisy_passwd, daisy_ip, daisy_gateway,\
        hosts_num = get_yml_para(conf['dha'])
    print "{hosts_num} {ip} {passwd} -s {size} -g {gateway}".format(
        hosts_num=hosts_num,
        passwd=daisy_passwd,
        size=daisyserver_size,
        ip=daisy_ip,
        gateway=daisy_gateway)


if __name__ == "__main__":
    get_conf_from_deploy()
