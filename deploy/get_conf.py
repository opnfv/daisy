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


def networkdecorator(func):
    def wrapter(s, seq):
        network_list = s.get('networks', [])
        result = {}
        for network in network_list:
            s = func(s, seq, network)
            if not s:
                continue
            result.update(s)
        if len(result) == 0:
            return ""
        else:
            return result
    return wrapter


def interfacedecorator(func):
    def wrapter(s, seq):
        interface_list = s.get('interfaces', [])
        result = {}
        for interface in interface_list:
            s = func(s, seq, interface)
            if not s:
                continue
            if s.keys()[0] in result:
                result[s.keys()[0]].append(s.values()[0][0])
            else:
                result.update(s)
        if len(result) == 0:
            return ""
        else:
            return result
    return wrapter


def hostdecorator(func):
    def wrapter(s, seq):
        host_list = s.get('hosts', [])
        result = {}
        for host in host_list:
            s = func(s, seq, host)
            if not s:
                continue
            result.update(s)
        if len(result) == 0:
            return ""
        else:
            return result
    return wrapter


def decorator(func):
    def wrapter(s, seq):
        host_list = s.get('hosts', [])
        result = []
        for host in host_list:
            s = func(s, seq, host)
            if not s:
                continue
            result.append(s)
        if len(result) == 0:
            return ""
        else:
            return result
    return wrapter


@networkdecorator
def network(s, seq, network=None):
    net_plane = network.get('name', '')
    network.pop('name')
    map = {}
    map[net_plane] = network
    return map


@interfacedecorator
def interface(s, seq, interface=None):
    name = interface.get('name', '')
    if name == "TENANT":
        name = "physnet1"
    interface = interface.get('interface', '')
    map2 = {}
    map = {'ip': '', 'name': name}
    map2[interface] = [map]
    return map2


@hostdecorator
def role(s, seq, host=None):
    hostname = host.get('name', '')
    role = host.get('roles', '')
    map = {}
    map[hostname] = role
    return map


@decorator
def name(s, seq, host=None):
    hostname = host.get('name', '')
    return hostname


def network_config_parse(s, dha_file):
    network_map = network(s, ',')
    vip = s.get('internal_vip')
    interface_map = interface(s, ',')
    return network_map, vip, interface_map


def dha_config_parse(s, dha_file):
    hosts_name = name(s, ',')
    return hosts_name


def config(dha_file, network_file):
    data = init(dha_file)
    hosts_name = dha_config_parse(data, dha_file)
    data = init(network_file)
    network_map, vip, interface_map = network_config_parse(data, network_file)
    return interface_map, hosts_name, network_map, vip
