##############################################################################
# Copyright (c) 2017 ZTE Corporation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import os
import shutil
import time

from libvirt_utils import (
    create_virtual_disk,
    create_vm,
    reboot_vm,
    delete_vm_and_disk,
    create_virtual_network,
    delete_virtual_network
)
from utils import (
    WORKSPACE,
    LI,
    LW,
    err_exit,
    run_shell,
    join,
    ipmi_reboot_node,
)

CREATE_QCOW2_PATH = join(WORKSPACE, 'tools')

VMDEPLOY_DAISY_SERVER_NET = join(WORKSPACE, 'templates/virtual_environment/networks/daisy.xml')
VMDEPLOY_TARGET_NODE_NET = join(WORKSPACE, 'templates/virtual_environment/networks/os-all_in_one.xml')
VMDEPLOY_DAISY_SERVER_VM = join(WORKSPACE, 'templates/virtual_environment/vms/daisy.xml')

BMDEPLOY_DAISY_SERVER_VM = join(WORKSPACE, 'templates/physical_environment/vms/daisy.xml')

ALL_IN_ONE_TEMPLATE = join(WORKSPACE, 'templates/virtual_environment/vms/all_in_one.xml')
CONTROLLER_TEMPLATE = join(WORKSPACE, 'templates/virtual_environment/vms/controller01.xml')
COMPUTE_TEMPLATE = join(WORKSPACE, 'templates/virtual_environment/vms/computer01.xml')
VIRT_NET_TEMPLATE_PATH = join(WORKSPACE, 'templates/virtual_environment/networks')


class DaisyEnvironment(object):
    def __init__(self, deploy_struct, net_struct, adapter, pxe_bridge,
                 daisy_server_info, work_dir, storage_dir):
        self.deploy_struct = deploy_struct
        self.net_struct = net_struct
        self.adapter = adapter
        self.pxe_bridge = pxe_bridge
        self.work_dir = work_dir
        self.storage_dir = storage_dir
        self.daisy_server_info = daisy_server_info
        LI('Daisy Environment Initialized')

    def create_daisy_server_image(self):
        LI('Begin to create Daisy Server image')
        script = join(CREATE_QCOW2_PATH, 'daisy-img-modify.sh')
        sub_script = join(CREATE_QCOW2_PATH, 'centos-img-modify.sh')
        cmd = '{script} -c {sub_script} -a {address} -g {gateway} -s {disk_size}'.format(
            script=script,
            sub_script=sub_script,
            address=self.daisy_server_info['address'],
            gateway=self.daisy_server_info['gateway'],
            disk_size=self.daisy_server_info['disk_size'])
        LI('Command is: ')
        LI('  %s' % cmd)
        # status, output = commands.getstatusoutput(cmd)
        status = run_shell(cmd)
        if status:
            err_exit('Failed to create Daisy Server image')
        if os.access(self.daisy_server_info['image'], os.R_OK):
            os.remove(self.daisy_server_info['image'])
        image = join(self.work_dir, 'daisy/centos7.qcow2')
        shutil.move(image, self.daisy_server_info['image'])
        LI('Daisy Server image is created %s' % self.daisy_server_info['image'])

    def create_daisy_server_network(self):
        net_name = create_virtual_network(VMDEPLOY_DAISY_SERVER_NET)
        if net_name != self.pxe_bridge:
            self.delete_virtual_network(VMDEPLOY_DAISY_SERVER_NET)
            err_exit('Network name %s is wrong, pxe bridge is %s' % (net_name, self.pxe_bridge))

    def create_daisy_server_vm(self):
        # TODO: refactor the structure of deploy.yml, add VM template param of Daisy Server
        #       add self.pxe_bridge into the vm template
        if 'template' in self.deploy_struct:
            # get VM name of Daisy Server from the template
            template = self.deploy_struct['template']
        elif 'libvirt' == self.adapter:
            template = VMDEPLOY_DAISY_SERVER_VM
        else:
            template = BMDEPLOY_DAISY_SERVER_VM
        create_vm(template,
                  name=self.daisy_server_info['name'],
                  disk_file=self.daisy_server_info['image'])

    def create_daisy_server(self):
        self.create_daisy_server_image()
        if 'libvirt' == self.adapter:
            self.create_daisy_server_network()
        self.create_daisy_server_vm()

    def create_virtual_node(self, node):
        name = node['name']
        roles = node['roles']
        controller_size = self.deploy_struct['disks']['controller']
        compute_size = self.deploy_struct['disks']['compute']
        LI('Begin to create virtual node %s, roles %s' % (name, roles))

        if 'CONTROLLER_LB' in roles:
            size = controller_size
            if 'COMPUTER' in roles:
                size = compute_size if compute_size > controller_size else controller_size
                template = ALL_IN_ONE_TEMPLATE
            else:
                template = CONTROLLER_TEMPLATE
        else:
            size = compute_size
            template = COMPUTE_TEMPLATE

        if 'template' in node:
            template = node['template']
        disk_file = join(self.storage_dir, name + '.qcow2')
        # TODO: modify the sizes in deploy.yml to more than 200G
        if size < 200:
            size = 200
        create_virtual_disk(disk_file, size)
        create_vm(template, name, disk_file)

    def create_or_find_nodes(self):
        if self.adapter == 'libvirt':
            create_virtual_network(VMDEPLOY_TARGET_NODE_NET)
            for node in self.deploy_struct['hosts']:
                self.create_virtual_node(node)
            time.sleep(20)
        else:
            address = 106
            for node in self.deploy_struct['hosts']:
                # TODO: add these info into deploy.yml, or read from PDF
                node['ipmiIp'] = '192.168.1.' + str(address)
                address += 1
                if address > 111:
                    err_exit('the ipmi address exceeds the range 106~110')
                node['ipmiUser'] = 'zteroot'
                node['ipmiPass'] = 'superuser'
                ipmi_reboot_node(node['ipmiIp'], node['ipmiUser'],
                                 node['ipmiPass'], boot_source='pxe')

    def reboot_virtual_nodes(self, boot_devs=None):
        for node in self.deploy_struct['hosts']:
            reboot_vm(node['name'], boot_devs=boot_devs)

    def delete_daisy_server(self):
        delete_vm_and_disk(self.daisy_server_info['name'])

    def delete_nodes(self):
        for host in self.deploy_struct['hosts']:
            delete_vm_and_disk(host['name'])

    def delete_networks(self):
        if 'virtNetTemplatePath' in self.deploy_struct:
            path = self.deploy_struct['virtNetTemplatePath']
        else:
            path = VIRT_NET_TEMPLATE_PATH

        if not os.path.isdir(path):
            LW('Cannot find the virtual network template path %s' % path)
            return
        for f in os.listdir(path):
                f = join(path, f)
                if os.path.isfile(f):
                    delete_virtual_network(f)

    def delete_old_environment(self):
        LW('Begin to delete old environment !')
        if self.adapter == 'libvirt':
            self.delete_nodes()

        self.delete_daisy_server()

        if self.adapter == 'libvirt':
            self.delete_networks()
        LW('Old environment cleanup finished !')
