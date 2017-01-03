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


def init(file):
    with open(file) as fd:
        return yaml.safe_load(fd)


def decorator_mk(types):
    def decorator(func):
        def wrapter(s):
            item_list = s.get(types, [])
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
    map = {'ip': '', 'name': net_name}
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


def network_config_parse(s, dha_file):
    network_map = network(s)
    vip = s.get('internal_vip')
    interface_map = interface(s)
    return network_map, vip, interface_map


def dha_config_parse(s, dha_file):
    host_role_map = role(s)
    hosts_name = []
    for name in host_role_map:
        hosts_name.append(name)
    return hosts_name


def config(dha_file, network_file):
    data = init(dha_file)
    hosts_name = dha_config_parse(data, dha_file)
    data = init(network_file)
    network_map, vip, interface_map = network_config_parse(data, network_file)
    return interface_map, hosts_name, network_map, vip
