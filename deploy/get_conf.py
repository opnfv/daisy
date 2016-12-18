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
                if ret:
                    result.update(ret)
            return result
        return wrapter
    return decorator


@decorator_mk('networks')
def network(network=None):
    net_plane = network.get('name', '')
    network.pop('name')
    map = {}
    map[net_plane] = network
    return map


@decorator_mk('hosts')
def interface(host=None):
    hostname = host.get('name', '')
    interface = host.get('interface', '')
    map = {}
    for k in interface:
        for v in k['logic']:
            map[v['name']]={'ip': v['ip'], 'phynic': k['phynic']}
    return map


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
    return network_map, vip


def dha_config_parse(s, dha_file):
    host_interface_map = interface(s)
    host_role_map = role(s)
    host_ip_passwd_map = host(s)
    return host_interface_map, host_role_map, host_ip_passwd_map


def config(dha_file, network_file):
    data = init(dha_file)
    host_interface_map, host_role_map, host_ip_passwd_map = \
        dha_config_parse(data, dha_file)
    data = init(network_file)
    network_map, vip = network_config_parse(data, network_file)
    for k in host_interface_map:
        host_interface_map[k].update(network_map[k])
    return host_interface_map, host_role_map, \
        host_ip_passwd_map, network_map, vip

