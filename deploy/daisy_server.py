##############################################################################
# Copyright (c) 2017 ZTE Corporation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import os
import paramiko
import scp
import time

from utils import (
    WORKSPACE,
    LD,
    LI,
    LW,
    err_exit,
    log_bar,
    path_join,
    update_config
)

TIMEOUT = 300
BLOCK_SIZE = 1024


def log_from_stream(res, data, log_func):
    lines = data.splitlines()
    res_data = res
    if res_data:
        lines[0] = res_data + lines[0]
        res_data = None

    if not data.endswith("\n"):
        res_data = lines[-1]
        del (lines[-1])
    for string in lines:
        log_func(string)

    if res_data and len(res_data) >= BLOCK_SIZE:
        log_func(res_data)
        res_data = None

    return res_data


LEN_OF_NAME_PART = 50
LEN_OF_SIZE_PART = 15


def log_scp(filename, size, send):
    if size != send:
        return
    unit = "  B"
    if size > 1024:
        size /= 1024
        unit = " KB"
    if size > 1024:
        size /= 1024
        unit = " MB"

    name_part = 'SCP: ' + filename + ' '
    size_part = ' ' + str(size) + unit + ' 100%'
    if len(name_part) <= LEN_OF_NAME_PART:
        LD(name_part.ljust(LEN_OF_NAME_PART, '.') + size_part.rjust(LEN_OF_SIZE_PART, '.'))
    else:
        LD(name_part)
        LD("     ".ljust(LEN_OF_NAME_PART, '.') + size_part.rjust(LEN_OF_SIZE_PART, '.'))


class DaisyServer(object):
    def __init__(self, name, address, password, remote_dir, bin_file,
                 adapter, scenario, deploy_file_name, net_file_name):
        self.name = name
        self.address = address
        self.password = password
        self.remote_dir = remote_dir
        self.bin_file = bin_file
        self.adapter = adapter
        self.ssh_client = None
        self.scenario = scenario
        self.deploy_file_name = deploy_file_name
        self.net_file_name = net_file_name

    def connect(self):
        LI('Try to connect to Daisy Server ...')
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        count = 0
        MAX_COUNT = 120
        while count < MAX_COUNT:
            try:
                self.ssh_client.connect(hostname=self.address,
                                        username='root',
                                        password=self.password,
                                        timeout=TIMEOUT)
            except (paramiko.ssh_exception.SSHException,
                    paramiko.ssh_exception.NoValidConnectionsError):
                count += 1
                LD('Attempted SSH connection %d time(s)' % count)
                time.sleep(2)
            else:
                break
        if count >= MAX_COUNT:
            err_exit('SSH connect to Daisy Server failed')

        LI('SSH connection established')
        LI('Try ssh_run: ls -al')
        self.ssh_run('ls -al', check=True)

    def close(self):
        self.ssh_client.close()

    def ssh_exec_cmd(self, cmd):
        stdin, stdout, stderr = self.ssh_client.exec_command(cmd, timeout=TIMEOUT)
        response = stdout.read().strip()
        error = stderr.read().strip()

        if error:
            self.close()
            err_exit('SSH client error occurred')
        else:
            return response

    def ssh_run(self, cmd, check=False, exit_msg='Ssh_run failed'):
        transport = self.ssh_client.get_transport()
        transport.set_keepalive(1)
        session = transport.open_session()
        res_data = None
        session.exec_command(cmd)
        while True:
            if session.recv_ready():
                data = session.recv(BLOCK_SIZE)
                while data:
                    res_data = log_from_stream(res_data, data, LI)
                    data = session.recv(BLOCK_SIZE)
                if res_data:
                    LI(res_data)
                    res_data = None

            if session.recv_stderr_ready():
                data = session.recv_stderr(BLOCK_SIZE)
                while data:
                    res_data = log_from_stream(res_data, data, LW)
                    data = session.recv_stderr(BLOCK_SIZE)
                if res_data:
                    LW(res_data)
                    res_data = None
            if session.exit_status_ready():
                break

        status = session.recv_exit_status()
        if check and status:
            err_exit(exit_msg)

        return status

    def scp_get(self, remote, local='.'):
        scp_client = scp.SCPClient(self.ssh_client.get_transport(),
                                   progress=log_scp,
                                   socket_timeout=TIMEOUT)
        scp_client.get(remote, local_path=local, recursive=True)

    def scp_put(self, local, remote='.'):
        scp_client = scp.SCPClient(self.ssh_client.get_transport(),
                                   progress=log_scp,
                                   socket_timeout=TIMEOUT)
        scp_client.put(local, remote_path=remote, recursive=True)

    def create_dir(self, remote_dir):
        cmd = 'mkdir -p %s' % remote_dir
        self.ssh_exec_cmd(cmd)

    def delete_dir(self, remote_dir):
        cmd = 'if [[ -f {DIR} || -d {DIR} ]]; then rm -fr {DIR}; fi'.format(DIR=remote_dir)
        self.ssh_exec_cmd(cmd)

    def prepare_files(self):
        self.delete_dir(self.remote_dir)
        LI('Copy WORKSPACE directory to Daisy Server')
        self.scp_put(WORKSPACE, self.remote_dir)
        time.sleep(2)
        LI('Copy finished')

        self.create_dir('/home/daisy_install')
        LI('Write Daisy Server address into daisy.conf')
        update_config(path_join(WORKSPACE, 'deploy/daisy.conf'),
                      'daisy_management_ip',
                      self.address,
                      section='DEFAULT')
        LI('Copy daisy.conf to Daisy Server')
        self.scp_put(path_join(WORKSPACE, 'deploy/daisy.conf'), '/home/daisy_install/')

        if os.path.dirname(os.path.abspath(self.bin_file)) != WORKSPACE:
            LI('Copy opnfv.bin to Daisy Server')
            self.scp_put(self.bin_file, path_join(self.remote_dir, 'opnfv.bin'))

    def install_daisy(self):
        self.prepare_files()
        LI('Begin to install Daisy')
        status = self.ssh_run('%s install' % path_join(self.remote_dir, 'opnfv.bin'))
        log_bar('Daisy installation completed ! status = %s' % status)

    def prepare_configurations(self):
        if self.adapter != 'libvirt':
            return
        LI('Prepare some configuration files')
        cmd = 'export PYTHONPATH={python_path}; python {script} -nw {net_file} -b {is_bare}'.format(
            python_path=self.remote_dir,
            script=path_join(self.remote_dir, 'deploy/prepare/execute.py'),
            net_file=path_join(self.remote_dir, self.net_file_name),
            is_bare=1 if self.adapter == 'ipmi' else 0)
        self.ssh_run(cmd)

    def prepare_cluster(self, deploy_file, net_file):
        LI('Copy cluster configuration files to Daisy Server')
        self.scp_put(deploy_file, path_join(self.remote_dir, self.deploy_file_name))
        self.scp_put(net_file, path_join(self.remote_dir, self.net_file_name))

        self.prepare_configurations()

        LI('Prepare cluster and PXE')
        cmd = "python {script} --dha {deploy_file} --network {net_file} --cluster \'yes\'".format(
            script=path_join(self.remote_dir, 'deploy/tempest.py'),
            deploy_file=path_join(self.remote_dir, self.deploy_file_name),
            net_file=path_join(self.remote_dir, self.net_file_name))
        self.ssh_run(cmd, check=True)

    def prepare_host_and_pxe(self):
        LI('Prepare host and PXE')
        cmd = "python {script} --dha {deploy_file} --network {net_file} --host \'yes\' --isbare {is_bare} --scenario {scenario}".format(
            script=path_join(self.remote_dir, 'deploy/tempest.py'),
            deploy_file=path_join(self.remote_dir, self.deploy_file_name),
            net_file=path_join(self.remote_dir, self.net_file_name),
            is_bare=1 if self.adapter == 'ipmi' else 0,
            scenario=self.scenario)
        self.ssh_run(cmd, check=True)

    def install_virtual_nodes(self):
        LI('Daisy install virtual nodes')
        cmd = "python {script} --dha {deploy_file} --network {net_file} --install \'yes\'".format(
            script=path_join(self.remote_dir, 'deploy/tempest.py'),
            deploy_file=path_join(self.remote_dir, self.deploy_file_name),
            net_file=path_join(self.remote_dir, self.net_file_name))
        self.ssh_run(cmd, check=True)

    def check_os_installation(self, nodes_num):
        LI('Check Operating System installation progress')
        cmd = '{script} -d {is_bare} -n {nodes_num}'.format(
            script=path_join(self.remote_dir, 'deploy/check_os_progress.sh'),
            is_bare=1 if self.adapter == 'ipmi' else 0,
            nodes_num=nodes_num)
        self.ssh_run(cmd, check=True)

    def check_openstack_installation(self, nodes_num):
        LI('Check OpenStack installation progress')
        cmd = '{script} -n {nodes_num}'.format(
            script=path_join(self.remote_dir, 'deploy/check_openstack_progress.sh'),
            nodes_num=nodes_num)
        self.ssh_run(cmd, check=True)

    def post_deploy(self):
        LI('Post deploy ...')
        cmd = 'bash {script} -n {net_file}'.format(
            script=path_join(self.remote_dir, 'deploy/post.sh'),
            net_file=path_join(self.remote_dir, self.net_file_name))
        self.ssh_run(cmd, check=False)
