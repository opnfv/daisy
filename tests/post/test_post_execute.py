##############################################################################
# Copyright (c) 2017 ZTE Corp and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import pytest

import deploy.post.execute
from deploy.post.execute import (
    _config_external_network,
    _config_icmp_security_group_rule,
    _config_ssh_security_group_rule
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
