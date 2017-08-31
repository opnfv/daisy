##############################################################################
# Copyright (c) 2017 ZTE Corp and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import pytest

from deploy.common.query import (
    find
)


@pytest.mark.parametrize('sequence, expected', [
    ([{'cidr': '10.20.11.0/24', 'gateway': '10.20.11.1',
       'ip_ranges': [{'start': '10.20.11.3', 'end': '10.20.11.10'}],
       'name': 'MANAGEMENT'},
      {'cidr': '10.20.11.0/24', 'gateway': '10.20.11.1',
       'ip_ranges': [{'start': '10.20.11.3', 'end': '10.20.11.10'}],
       'name': 'STORAGE'}],
      {'cidr': '10.20.11.0/24', 'gateway': '10.20.11.1',
       'ip_ranges': [{'start': '10.20.11.3', 'end': '10.20.11.10'}],
       'name': 'STORAGE'}),
    ([{'cidr': '10.20.11.0/24', 'gateway': '10.20.11.1',
       'ip_ranges': [{'start': '10.20.11.3', 'end': '10.20.11.10'}],
       'name': 'MANAGEMENT'},
      {'cidr': '10.20.11.0/24', 'gateway': '10.20.11.1',
       'ip_ranges': [{'start': '10.20.11.3', 'end': '10.20.11.10'}],
       'name': 'PUBLICAPI'}],
       None)])
def test_find(sequence, expected):
    def sample_func(item):
        return item['name'] == 'STORAGE'
    assert find(sample_func, sequence) == expected
