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

import deploy.prepare.execute
from deploy.prepare.execute import (
    _set_qemu_compute,
    _set_default_floating_pool,
    _set_trusts_auth
)

deploy.prepare.execute.KOLLA_CONF_PATH = '/tmp'


@pytest.fixture(scope="module")
def kolla_conf_file_nov_path():
    return os.path.join(deploy.prepare.execute.KOLLA_CONF_PATH, 'nova')


@pytest.fixture(scope="module")
def kolla_conf_file_heat_dir():
    return os.path.join(deploy.prepare.execute.KOLLA_CONF_PATH, 'heat')


@pytest.fixture(scope="module")
def conf_file_dir(data_root):
    return os.path.join(data_root, 'lab_conf')


def clear_tmp_dir(path):
    filelist = os.listdir(path)
    for file in filelist:
        file_path = os.path.join(path, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
    os.rmdir(path)


def test__set_qemu_compute(kolla_conf_file_nov_path):
    _set_qemu_compute()
    exp_conf_file = os.path.join(kolla_conf_file_nov_path, 'nova-compute.conf')
    assert os.path.isfile(exp_conf_file)
    clear_tmp_dir(kolla_conf_file_nov_path)


def test__set_default_floating_pool(kolla_conf_file_nov_path, conf_file_dir):
    network_conf_file = os.path.join(conf_file_dir, 'network_virtual1.yml')
    _set_default_floating_pool(network_conf_file)
    exp_conf_file = os.path.join(kolla_conf_file_nov_path, 'nova-api.conf')
    assert os.path.isfile(exp_conf_file)
    clear_tmp_dir(kolla_conf_file_nov_path)


def test__set_trusts_auth(kolla_conf_file_heat_dir):
    _set_trusts_auth()
    exp_conf_file_1 = os.path.join(kolla_conf_file_heat_dir, 'heat-api.conf')
    exp_conf_file_2 = os.path.join(kolla_conf_file_heat_dir, 'heat-engine.conf')
    assert (os.path.isfile(exp_conf_file_1) and os.path.isfile(exp_conf_file_2))
    clear_tmp_dir(kolla_conf_file_heat_dir)
