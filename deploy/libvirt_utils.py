##############################################################################
# Copyright (c) 2017 ZTE Corporation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import commands
import libvirt
import os
import string
import xml.etree.ElementTree as ET

from utils import (
    LI,
    LE,
    LW,
    WORKSPACE,
    err_exit,
    path_join
)


def get_nets_name(root):
    nets = []
    for interface in root.findall('./devices/interface'):
        if 'type' in interface.attrib and interface.attrib['type'] == 'network':
            for source in interface.iterfind('source'):
                if 'network' in source.attrib:
                    nets.append(source.attrib['network'])
    return nets


def modify_vm_boot_order(root, boot_devs):
    os_elem = root.find('os')
    for boot_elem in os_elem.findall('boot'):
        os_elem.remove(boot_elem)
    for boot_dev in boot_devs:
        boot_elem = ET.Element('boot', attrib={'dev': boot_dev})
        os_elem.append(boot_elem)
    return root


def modify_vm_name(root, vm_name):
    name_elem = root.find('./name')
    name_elem.text = vm_name


def modify_vm_disk_file(root, disks):
    dev_list = ['hd' + ch for ch in string.ascii_lowercase]
    devices = root.find('./devices')
    for disk in devices.findall('disk'):
        if disk.attrib['device'] == 'disk':
            devices.remove(disk)
        else:
            target = disk.find('target')
            dev = target.attrib['dev']
            if dev in dev_list:
                dev_list.remove(dev)

    for disk_file in disks:
        dev = dev_list.pop(0)
        disk = ET.Element('disk', attrib={'device': 'disk', 'type': 'file'})
        disk.append(ET.Element('driver', attrib={'name': 'qemu', 'type': 'qcow2'}))
        disk.append(ET.Element('source', attrib={'file': disk_file}))
        disk.append(ET.Element('target', attrib={'dev': dev, 'bus': 'ide'}))
        devices.append(disk)


def create_virtual_disk(disk_file, size):
    LI('Create virtual disk file %s size %d GB' % (disk_file, size))
    cmd = 'qemu-img create -f qcow2 {disk_file} {size}G'.format(
        disk_file=disk_file, size=size)
    status, output = commands.getstatusoutput(cmd)
    if status:
        LE(output)
        err_exit('Fail to create qemu image !')


def create_vm(template, name=None, disks=None):
    LI('Begin to create VM %s' % template)

    if name or disks:
        tree = ET.ElementTree(file=template)
        root = tree.getroot()
        if name:
            modify_vm_name(root, name)
        if disks:
            modify_vm_disk_file(root, disks)

        temp_file = path_join(WORKSPACE, 'tmp.xml')
        tree.write(temp_file)
        output = commands.getoutput('cat %s' % temp_file)
        os.remove(temp_file)
    else:
        output = commands.getoutput('cat %s' % template)

    conn = libvirt.open('qemu:///system')
    domain = conn.defineXML(output)
    if domain is None:
        err_exit('Failed to define VM %s' % template)
    if domain.create() < 0:
        err_exit('Failed to start VM %s' % template)
    domain.setAutostart(1)

    LI('VM %s is started' % domain.name())
    return


def reboot_vm(vm_name, boot_devs=None):
    LI('Begin to reboot VM %s', vm_name)
    conn = libvirt.open('qemu:///system')
    try:
        vm = conn.lookupByName(vm_name)
    except libvirt.libvirtError as e:
        LE(e)
        err_exit('VM %s is not found: ' % vm_name)

    if boot_devs:
        if vm.isActive():
            vm.destroy()
            LI('Destroy VM %s' % vm_name)

        # root = ET.fromstring(vm.XMLDesc())
        temp_file = path_join(WORKSPACE, 'tmp.xml')
        commands.getoutput('virsh dumpxml %s > %s' % (vm_name, temp_file))
        tree = ET.parse(temp_file)
        root = tree.getroot()
        LI('Modify the boot order %s' % boot_devs)
        modify_vm_boot_order(root, boot_devs)
        tree.write(temp_file)

        LI('Re-define and start the VM %s' % vm_name)
        vm.undefine()
        vm = conn.defineXML(commands.getoutput('cat %s' % temp_file))
        vm.create()
        vm.setAutostart(1)
    else:
        vm.reset()

    conn.close()


def get_disk_file(root):
    disks = []
    for disk in root.findall('./devices/disk'):
        if 'device' in disk.attrib and disk.attrib['device'] == 'disk':
            for source in disk.iterfind('source'):
                if 'file' in source.attrib:
                    disks.append(source.attrib['file'])
    return disks


def delete_vm_and_disk(vm_name):
    LI('Begin to delete VM %s', vm_name)
    conn = libvirt.open('qemu:///system')
    vm = None
    for item in conn.listAllDomains():
        if vm_name == item.name():
            vm = item
            break
    if vm is None:
        conn.close()
        LI('VM %s is not found' % vm_name)
        return

    output = vm.XMLDesc()
    root = ET.fromstring(output)

    if vm.isActive():
        vm.destroy()
        LI('Destroy VM %s' % vm.name())
    vm.undefine()

    for disk_file in get_disk_file(root):
        if os.path.isfile(disk_file):
            status, output = commands.getstatusoutput('rm -f %s' % disk_file)
            if status:
                LW('Failed to delete the VM disk file %s' % disk_file)

    conn.close()
    LI('VM %s is removed' % vm_name)


def create_virtual_network(template):
    LI('Begin to create virtual network %s' % template)
    output = commands.getoutput('cat %s' % template)
    conn = libvirt.open('qemu:///system')
    network = conn.networkDefineXML(output)
    if network is None:
        err_exit('Failed to define a virtual network %s' % template)

    network.create()  # set the network active
    network.setAutostart(1)
    conn.close()
    LI('Virtual network %s is created' % network.name())
    return network.name()


def delete_virtual_network(network_xml):
    LI('Begin to find and delete network %s' % network_xml)
    tree = ET.ElementTree(file=network_xml)
    root = tree.getroot()
    names = root.findall('./name')
    assert len(names) == 1
    name = names[0].text

    result = 0
    conn = libvirt.open('qemu:///system')

    for net in conn.listAllNetworks():
        if name == net.name():
            if net.isActive():
                net.destroy()
                LI('Network %s is destroyed' % name)
            net.undefine()
            LI('Network %s is deleted' % name)
            result = 1
            break
    conn.close()
    if not result:
        LI('Network %s is not found' % name)
