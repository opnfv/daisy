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

from config.schemas import (
    MIN_NODE_DISK_SIZE,
    MIN_CEPH_DISK_SIZE
)
from daisy_server import (
    DaisyServer
)
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
    LD,
    LI,
    LW,
    err_exit,
    run_shell,
    path_join,
    ipmi_reboot_node,
)

CREATE_QCOW2_PATH = path_join(WORKSPACE, 'tools')

VMDEPLOY_DAISY_SERVER_NET = path_join(WORKSPACE, 'templates/virtual_environment/networks/daisy.xml')
VMDEPLOY_TARGET_NODE_NET = path_join(WORKSPACE, 'templates/virtual_environment/networks/os-all_in_one.xml')
VMDEPLOY_DAISY_SERVER_VM = path_join(WORKSPACE, 'templates/virtual_environment/vms/daisy.xml')

BMDEPLOY_DAISY_SERVER_VM = path_join(WORKSPACE, 'templates/physical_environment/vms/daisy.xml')

ALL_IN_ONE_TEMPLATE = path_join(WORKSPACE, 'templates/virtual_environment/vms/all_in_one.xml')
CONTROLLER_TEMPLATE = path_join(WORKSPACE, 'templates/virtual_environment/vms/controller.xml')
COMPUTE_TEMPLATE = path_join(WORKSPACE, 'templates/virtual_environment/vms/computer.xml')
VIRT_NET_TEMPLATE_PATH = path_join(WORKSPACE, 'templates/virtual_environment/networks')


class DaisyEnvironment(object):
    def __new__(cls, deploy_struct, net_struct, adapter, pxe_bridge,
                daisy_server_info, work_dir, storage_dir, scenario):
        if adapter == 'libvirt':
            return VirtualEnvironment(deploy_struct, net_struct,
                                      adapter, pxe_bridge,
                                      daisy_server_info, work_dir,
                                      storage_dir, scenario)
        else:
            return BareMetalEnvironment(deploy_struct, net_struct,
                                        adapter, pxe_bridge,
                                        daisy_server_info, work_dir,
                                        storage_dir, scenario)


class DaisyEnvironmentBase(object):
    def __init__(self, deploy_struct, net_struct, adapter, pxe_bridge,
                 daisy_server_info, work_dir, storage_dir, scenario):
        self.deploy_struct = deploy_struct
        self.net_struct = net_struct
        self.adapter = adapter
        self.pxe_bridge = pxe_bridge
        self.work_dir = work_dir
        self.storage_dir = storage_dir
        self.daisy_server_info = daisy_server_info
        self.server = None
        self.scenario = scenario
        LI('Daisy Environment Initialized')

    def delete_daisy_server(self):
        delete_vm_and_disk(self.daisy_server_info['name'])

    def create_daisy_server_image(self):
        LI('Begin to create Daisy Server image')
        script = path_join(CREATE_QCOW2_PATH, 'daisy-img-modify.sh')
        sub_script = path_join(CREATE_QCOW2_PATH, 'centos-img-modify.sh')
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
        image = path_join(self.work_dir, 'daisy/centos7.qcow2')
        shutil.move(image, self.daisy_server_info['image'])
        LI('Daisy Server image is created %s' % self.daisy_server_info['image'])

    def install_daisy(self, remote_dir, bin_file):
        self.server = DaisyServer(self.daisy_server_info['name'],
                                  self.daisy_server_info['address'],
                                  self.daisy_server_info['password'],
                                  remote_dir,
                                  bin_file,
                                  self.adapter,
                                  self.scenario)
        self.server.connect()
        self.server.install_daisy()


class BareMetalEnvironment(DaisyEnvironmentBase):
    def delete_old_environment(self):
        LW('Begin to delete old environment !')
        self.delete_daisy_server()
        LW('Old environment cleanup finished !')

    def create_daisy_server(self):
        self.create_daisy_server_image()
        self.create_daisy_server_vm()

    def create_daisy_server_vm(self):
        # TODO: refactor the structure of deploy.yml, add VM template param of Daisy Server
        #       add self.pxe_bridge into the vm template
        if 'template' in self.deploy_struct:
            # get VM name of Daisy Server from the template
            template = self.deploy_struct['template']
        else:
            template = BMDEPLOY_DAISY_SERVER_VM

        create_vm(template,
                  name=self.daisy_server_info['name'],
                  disk_file=self.daisy_server_info['image'])

    def reboot_nodes(self, boot_dev=None):
        # TODO: add ipmi info into deploy.yml, or read from PDF
        address = 106
        for node in self.deploy_struct['hosts']:
            node['ipmiIp'] = '192.168.1.' + str(address)
            address += 1
            if address > 111:
                err_exit('the ipmi address exceeds the range 106~110')
            node['ipmiUser'] = 'zteroot'
            node['ipmiPass'] = 'superuser'
            ipmi_reboot_node(node['ipmiIp'], node['ipmiUser'],
                             node['ipmiPass'], boot_source=boot_dev)

    def deploy(self, deploy_file, net_file):
        self.server.prepare_cluster(deploy_file, net_file)
        self.reboot_nodes(boot_dev='pxe')
        self.server.prepare_host_and_pxe()

        LI('The hosts number is %d' % len(self.deploy_struct['hosts']))
        self.server.check_os_installation(len(self.deploy_struct['hosts']))
        time.sleep(10)
        self.server.check_openstack_installation(len(self.deploy_struct['hosts']))


class VirtualEnvironment(DaisyEnvironmentBase):
    def __init__(self, deploy_struct, net_struct, adapter, pxe_bridge,
                 daisy_server_info, work_dir, storage_dir, scenario):
        super(VirtualEnvironment, self).__init__(deploy_struct, net_struct, adapter, pxe_bridge,
                                                 daisy_server_info, work_dir, storage_dir, scenario)
        self.check_configuration()

    def check_configuration(self):
        self.check_nodes_template()

    def check_nodes_template(self):
        for node in self.deploy_struct['hosts']:
            template = node.get('template', None)
            if not template or os.access(template, os.R_OK):
                continue
            elif os.access(path_join(WORKSPACE, template), os.R_OK):
                template_new = path_join(WORKSPACE, template)
                LD('Template of VM node %s is %s' % (node.get('name', ''), template_new))
                node['template'] = template_new
            else:
                err_exit('The template of vm node %s does not exist.' % node.get('name'))

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
        else:
            template = VMDEPLOY_DAISY_SERVER_VM

        create_vm(template,
                  name=self.daisy_server_info['name'],
                  disks=[self.daisy_server_info['image']])

    def create_daisy_server(self):
        self.create_daisy_server_image()
        self.create_daisy_server_network()
        self.create_daisy_server_vm()

    def create_virtual_node(self, node):
        name = node['name']
        roles = node['roles']
        disks = self.deploy_struct.get('disks', {})
        controller_size = disks.get('controller', MIN_NODE_DISK_SIZE)
        compute_size = disks.get('compute', MIN_NODE_DISK_SIZE)
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
        disk_file = path_join(self.storage_dir, name + '.qcow2')
        create_virtual_disk(disk_file, size)

        disks = [disk_file]
        ceph_disk_name = self.deploy_struct.get('ceph_disk_name', '')
        # if ceph_disk_name and ceph_disk_name != '/dev/sda' and 'CONTROLLER_LB' in roles:
        if ceph_disk_name and ceph_disk_name != '/dev/sda':
            ceph_size = self.deploy_struct.get('disks', {}).get('ceph', MIN_CEPH_DISK_SIZE)
            ceph_disk_file = path_join(self.storage_dir, name + '_data.qcow2')
            create_virtual_disk(ceph_disk_file, ceph_size)
            disks.append(ceph_disk_file)

        create_vm(template, name, disks)

    def create_nodes(self):
        # TODO: support virtNetTemplatePath in deploy.yml
        #       and multi interfaces, not only all-in-one
        create_virtual_network(VMDEPLOY_TARGET_NODE_NET)
        for node in self.deploy_struct['hosts']:
            self.create_virtual_node(node)
        time.sleep(20)

    def reboot_nodes(self, boot_devs=None):
        for node in self.deploy_struct['hosts']:
            reboot_vm(node['name'], boot_devs=boot_devs)

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
                f = path_join(path, f)
                if os.path.isfile(f):
                    delete_virtual_network(f)

    def delete_old_environment(self):
        LW('Begin to delete old environment !')
        self.delete_nodes()
        self.delete_daisy_server()
        self.delete_networks()
        LW('Old environment cleanup finished !')

    def deploy(self, deploy_file, net_file):
        self.server.prepare_cluster(deploy_file, net_file)
        self.create_nodes()
        self.server.prepare_host_and_pxe()
        LI('Begin Daisy virtual-deploy os and openstack')
        self.reboot_nodes()
        LI('Sleep 20s to wait the VM(s) startup')
        time.sleep(20)
        self.server.install_virtual_nodes()

        LI('The hosts number is %d' % len(self.deploy_struct['hosts']))
        self.server.check_os_installation(len(self.deploy_struct['hosts']))
        time.sleep(10)
        self.reboot_nodes(boot_devs=['hd'])
        self.server.check_openstack_installation(len(self.deploy_struct['hosts']))
        self.server.post_deploy()
