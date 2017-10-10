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
import xml.etree.ElementTree as ET
from deploy.utils import WORKSPACE
import mock
sys.modules['libvirt'] = mock.Mock()

from deploy import libvirt_utils    # noqa: ignore=E402
from deploy.libvirt_utils import (
    get_nets_name,
    modify_vm_boot_order,
    create_virtual_disk,
    modify_vm_name,
    modify_vm_disk_file,
    modify_vm_bridge,
    create_vm,
    reboot_vm,
    get_disk_file,
#    delete_vm_and_disk,
    create_virtual_network,
#    delete_virtual_network,
#    get_vm_mac_addresses
)   # noqa: ignore=E402


@pytest.mark.parametrize('template_name, exp', [
    ('templates/physical_environment/vms/daisy.xml', []),
    ('templates/virtual_environment/vms/daisy.xml', ['daisy1'])])
def test_get_nets_name(template_name, exp):
    template = os.path.join(WORKSPACE, template_name)
    tree = ET.ElementTree(file=template)
    root = tree.getroot()
    ret = get_nets_name(root)
    assert ret == exp


def test_modify_vm_boot_order():
    template = os.path.join(WORKSPACE, 'templates/virtual_environment/vms/daisy.xml')
    tree = ET.ElementTree(file=template)
    root = tree.getroot()
    boot_devs = ['hd_test']
    modify_vm_boot_order(root, boot_devs)
    os_elem = root.find('os')
    for boot_dev in boot_devs:
        is_match = False
        for boot_elem in os_elem.findall('boot'):
            if boot_elem.attrib['dev'] == boot_dev:
                is_match = True
                break
        assert is_match


def test_modify_vm_name():
    template = os.path.join(WORKSPACE, 'templates/physical_environment/vms/daisy.xml')
    tree = ET.ElementTree(file=template)
    root = tree.getroot()
    vm_name = 'test_vm'
    modify_vm_name(root, vm_name)
    name_elem = root.find('./name')
    assert name_elem.text == vm_name


def test_modify_vm_disk_file():
    template = os.path.join(WORKSPACE, 'templates/physical_environment/vms/daisy.xml')
    tree = ET.ElementTree(file=template)
    root = tree.getroot()
    disk_path = os.path.join('/home/qemu/vms', 'daisy_test.qcow2')
    disks_path = [disk_path]
    modify_vm_disk_file(root, disks_path)
    devices = root.find('./devices')
    for disk in devices.findall('disk'):
        if disk.attrib['device'] == 'disk':
            assert disk.attrib['type'] == 'file'
            driver = disk.find('driver')
            assert driver.attrib['name'] == 'qemu' and driver.attrib['type'] == 'qcow2'
            target = disk.find('target')
            assert target.attrib['bus'] == 'ide'
            source = disk.find('source')
            is_match = False
            for disk_path in disks_path:
                if disk_path == source.attrib['file']:
                    is_match = True
                    break
            assert is_match


def test_modify_vm_bridge():
    template = os.path.join(WORKSPACE, 'templates/virtual_environment/vms/daisy.xml')
    tree = ET.ElementTree(file=template)
    root = tree.getroot()
    bridge = 'daisy_test'
    modify_vm_bridge(root, bridge)
    devices = root.find('./devices')
    is_match = False
    for interface in devices.findall('interface'):
        source = interface.find('source')
        if interface.attrib.get('type', None) == 'bridge' \
                and source is not None \
                and source.attrib.get('bridge', None) == bridge:
            is_match = True
            break
    assert is_match


@pytest.mark.parametrize('status', [
    (0),
    (1)])
@mock.patch('deploy.libvirt_utils.commands.getstatusoutput')
@mock.patch('deploy.libvirt_utils.err_exit')
def test_create_virtual_disk(mock_err_exit, mock_getstatusoutput, status):
    mock_getstatusoutput.return_value = (status, 'command_output')
    disk_file = '/tmp/vms/daisy.qcow2'
    size = 110
    create_virtual_disk(disk_file, size)
    mock_getstatusoutput.assert_called_once()
    if status:
        mock_err_exit.assert_called_once()
    else:
        mock_err_exit.assert_not_called()


@pytest.mark.parametrize('name, disk_name, physical_bridge', [
    ('dasiy_test_vm', 'daisy_test.qcow2', 'daisy_test_br'),
    (None, None, None)])
def test_create_vm(name, disk_name, physical_bridge):
    template = os.path.join(WORKSPACE, 'templates/physical_environment/vms/daisy.xml')
    if disk_name:
        disk_path = os.path.join('/home/qemu/vms', 'daisy_test.qcow2')
        disks_path = [disk_path]
    else:
        disks_path = None
    ret = create_vm(template, name=name, disks=disks_path, physical_bridge=physical_bridge)
    assert ret is not None


@pytest.mark.parametrize('vm_name, boot_devs', [
    ('dasiy_test_vm', None)])
def test_reboot_vm(vm_name, boot_devs):
    reboot_vm(vm_name, boot_devs=boot_devs)


def test_get_disk_file():
    template = os.path.join(WORKSPACE, 'templates/physical_environment/vms/daisy.xml')
    tree = ET.ElementTree(file=template)
    root = tree.getroot()
    exp_disks = ['/tmp/workdir/daisy/centos7.qcow2']
    ret = get_disk_file(root)
    assert ret == exp_disks


def test_create_virtual_network():
    template = os.path.join(WORKSPACE, 'templates/physical_environment/networks/daisy.xml')
    ret = create_virtual_network(template)
    assert ret is not None
