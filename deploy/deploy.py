##############################################################################
# Copyright (c) 2017 ZTE Corporation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

##############################################################################
# TODO:
# [ ] 1. specify VM templates (Server, Controller & Compute) in deploy.yml
# [ ] 2. specify network templates in deploy.yml
# [ ] 3. specify adapter(ipmi, libvirt) in deploy.yml
# [ ] 4. get ipmi user/password from PDF (Pod Descriptor File)
# [ ] 5. get pxe bridge from jjb
# [ ] 6. enlarge the vm size of Controller & Compute in deploy.yml
# [ ] 7. support scenarios options and configuration
##############################################################################

import argparse
import yaml
import time


from config.schemas import (
    MIN_DAISY_DISK_SIZE,
    deploy_schema_validate
)
from utils import (
    WORKSPACE,
    save_log_to_file,
    LI,
    LE,
    err_exit,
    log_bar,
    path_join,
    check_sudo_privilege,
    check_file_exists,
    make_file_executable,
    confirm_dir_exists,
    merge_dicts,
    check_scenario_valid
)
from environment import (
    DaisyEnvironment,
)


class DaisyDeployment(object):
    def __init__(self, lab_name, pod_name, deploy_file, net_file, bin_file,
                 daisy_only, cleanup_only, remote_dir, work_dir, storage_dir,
                 pxe_bridge, deploy_log, scenario):
        self.lab_name = lab_name
        self.pod_name = pod_name

        self.src_deploy_file = deploy_file
        self.scenario = scenario
        self.deploy_struct = self._construct_final_deploy_conf(deploy_file, scenario)
        self.deploy_file = self._construct_final_deploy_file(self.deploy_struct, work_dir)

        if not cleanup_only:
            self.net_file = net_file
            with open(net_file) as yaml_file:
                self.net_struct = yaml.safe_load(yaml_file)
        else:
            self.net_struct = None

        self.bin_file = bin_file
        self.daisy_only = daisy_only
        self.cleanup_only = cleanup_only
        self.remote_dir = remote_dir
        self.work_dir = work_dir
        self.storage_dir = storage_dir
        self.pxe_bridge = pxe_bridge
        self.deploy_log = deploy_log

        result = deploy_schema_validate(self.deploy_struct)
        if result:
            LE(result)
            err_exit('Configuration deploy.yml check failed!')

        self.adapter = self._get_adapter_info()
        LI('The adapter is %s' % self.adapter)

        # TODO: modify the jjb code to provide bridge name
        if self.adapter == 'libvirt':
            self.pxe_bridge = 'daisy1'
        else:
            self.pxe_bridge = 'br7'

        self.daisy_server_info = self._get_daisy_server_info()

        self.daisy_env = DaisyEnvironment(self.deploy_struct,
                                          self.net_struct,
                                          self.adapter,
                                          self.pxe_bridge,
                                          self.daisy_server_info,
                                          self.work_dir,
                                          self.storage_dir,
                                          self.scenario)

    def _get_adapter_info(self):
        default_adapter = 'libvirt' if 'virtual' in self.pod_name else 'ipmi'
        return self.deploy_struct.get('adapter', default_adapter)

    def _get_daisy_server_info(self):
        address = self.deploy_struct.get('daisy_ip', '10.20.11.2')
        gateway = self.deploy_struct.get('daisy_gateway', '10.20.11.1')
        password = self.deploy_struct.get('daisy_passwd', 'r00tme')
        disk_size = self.deploy_struct.get('disks', {}).get('daisy', MIN_DAISY_DISK_SIZE)
        # TODO: get VM name of daisy server from deploy.yml or vm template
        name = 'daisy'
        image = path_join(self.storage_dir, name + '.qcow2')

        return {'name': name,
                'image': image,
                'address': address,
                'gateway': gateway,
                'password': password,
                'disk_size': disk_size}

    def _construct_final_deploy_conf(self, deploy_file, scenario):
        with open(deploy_file) as yaml_file:
            deploy_struct = yaml.safe_load(yaml_file)
        scenario_file = path_join(WORKSPACE, 'deploy/scenario/scenario.yaml')
        with open(scenario_file) as yaml_file:
            scenario_trans_conf = yaml.safe_load(yaml_file)
        if scenario in scenario_trans_conf:
            fin_scenario_file = path_join(WORKSPACE, 'deploy/scenario',
                                          scenario_trans_conf[scenario]['configfile'])
        else:
            fin_scenario_file = path_join(WORKSPACE, 'deploy/scenario', scenario)
        with open(fin_scenario_file) as yaml_file:
            deploy_scenario_conf = yaml.safe_load(yaml_file)
        deploy_scenario_override_conf = deploy_scenario_conf['deploy-override-config']
        # Only virtual deploy scenarios can override deploy.yml
        if deploy_scenario_conf and (deploy_struct['adapter'] == 'libvirt'):
            deploy_struct = dict(merge_dicts(deploy_struct, deploy_scenario_override_conf))
        modules = deploy_scenario_conf['stack-extensions']
        deploy_struct['modules'] = modules
        return deploy_struct

    def _construct_final_deploy_file(self, deploy_infor, work_dir):
        final_deploy_file = path_join(work_dir, 'final_deploy.yml')
        with open(final_deploy_file, 'w') as f:
            f.write("\n".join([("title: This file automatically generated"),
                               "created: " + str(time.strftime("%d/%m/%Y")) +
                               " " + str(time.strftime("%H:%M:%S")),
                               "comment: none\n"]))
            yaml.dump(deploy_infor, f, default_flow_style=False)
        return final_deploy_file

    def run(self):
        self.daisy_env.delete_old_environment()
        if self.cleanup_only:
            return
        self.daisy_env.create_daisy_server()
        if self.daisy_only:
            log_bar('Create Daisy Server successfully !')
            return
        self.daisy_env.install_daisy(self.remote_dir, self.bin_file)
        self.daisy_env.deploy(self.deploy_file, self.net_file)
        log_bar('Daisy deploy successfully !')


def config_arg_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('-lab', dest='lab_name', action='store', nargs='?',
                        default=None,
                        help='Lab Name')
    parser.add_argument('-pod', dest='pod_name', action='store', nargs='?',
                        default=None,
                        help='Pod Name')

    parser.add_argument('-bin', dest='bin_file', action='store', nargs='?',
                        default=path_join(WORKSPACE, 'opnfv.bin'),
                        help='OPNFV Daisy BIN File')

    parser.add_argument('-do', dest='daisy_only', action='store_true',
                        default=False,
                        help='Install Daisy Server only')
    parser.add_argument('-co', dest='cleanup_only', action='store_true',
                        default=False,
                        help='Cleanup VMs and Virtual Networks')
    # parser.add_argument('-nd', dest='no_daisy', action='store_true',
    #                     default=False,
    #                     help='Do not install Daisy Server when it exists')

    parser.add_argument('-rdir', dest='remote_dir', action='store', nargs='?',
                        default='/home/daisy',
                        help='Code directory on Daisy Server')

    parser.add_argument('-wdir', dest='work_dir', action='store', nargs='?',
                        default='/tmp/workdir',
                        help='Temporary working directory')
    parser.add_argument('-sdir', dest='storage_dir', action='store', nargs='?',
                        default='/home/qemu/vms',
                        help='Storage directory for VM images')
    parser.add_argument('-B', dest='pxe_bridge', action='store', nargs='?',
                        default='pxebr',
                        help='Linux Bridge for booting up the Daisy Server VM '
                             '[default: pxebr]')
    parser.add_argument('-log', dest='deploy_log', action='store', nargs='?',
                        default=path_join(WORKSPACE, 'deploy.log'),
                        help='Path and name of the deployment log file')
    parser.add_argument('-s', dest='scenario', action='store', nargs='?',
                        default='os-nosdn-nofeature-noha',
                        help='Deployment scenario')
    return parser


def parse_arguments():
    parser = config_arg_parser()
    args = parser.parse_args()

    save_log_to_file(args.deploy_log)
    LI(args)

    check_scenario_valid(args.scenario)

    conf_base_dir = path_join(WORKSPACE, 'labs', args.lab_name, args.pod_name)
    deploy_file = path_join(conf_base_dir, 'daisy/config/deploy.yml')
    net_file = path_join(conf_base_dir, 'daisy/config/network.yml')

    check_file_exists(deploy_file)
    if not args.cleanup_only:
        check_file_exists(net_file)
    make_file_executable(args.bin_file)

    confirm_dir_exists(args.work_dir)
    confirm_dir_exists(args.storage_dir)

    kwargs = {
        'lab_name': args.lab_name,
        'pod_name': args.pod_name,
        'deploy_file': deploy_file,
        'net_file': net_file,
        'bin_file': args.bin_file,
        'daisy_only': args.daisy_only,
        'cleanup_only': args.cleanup_only,
        'remote_dir': args.remote_dir,
        'work_dir': args.work_dir,
        'storage_dir': args.storage_dir,
        'pxe_bridge': args.pxe_bridge,
        'deploy_log': args.deploy_log,
        'scenario': args.scenario
    }
    return kwargs


def main():
    check_sudo_privilege()
    kwargs = parse_arguments()
    deploy = DaisyDeployment(**kwargs)
    deploy.run()


if __name__ == '__main__':
    main()
