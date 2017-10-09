import os
import pytest
import mock
import paramiko

from deploy import daisy_server
from deploy.daisy_server import (
    DaisyServer,
    log_from_stream,
    log_scp
)
from deploy.utils import WORKSPACE


@pytest.fixture(scope="module")
def conf_file_dir(data_root):
    return os.path.join(data_root, 'lab_conf')


@pytest.fixture(scope="module")
def common_test_file_dir(data_root):
    return os.path.join(data_root, 'common')


def ssh_test_file_dir():
    return os.path.join(WORKSPACE, 'tests/data/common')


def get_ssh_test_command_from_file(dir, file_name):
    file_path = os.path.join(dir, file_name)
    with open(file_path) as f:
        return f.read()


data1 = get_ssh_test_command_from_file(ssh_test_file_dir(), 'ssh_stream_data1.txt')
res1 = None
expected_ret1 = None
res2 = 'test_res_commd'
data2 = get_ssh_test_command_from_file(ssh_test_file_dir(), 'ssh_stream_data2.txt')
expected_ret2 = 'test_ssh_cmd3'
data3 = get_ssh_test_command_from_file(ssh_test_file_dir(), 'ssh_stream_data3.txt')


@pytest.mark.parametrize('data, res, expected', [
    (data1, res1, expected_ret1),
    (data1, res2, expected_ret1),
    (data2, res1, expected_ret2),
    (data2, res2, expected_ret2),
    (data3, res1, expected_ret1),
    (data3, res2, expected_ret1)])
def test_log_from_stream(data, res, expected):
    def log_func(str):
        print str
    pre_val = daisy_server.BLOCK_SIZE
    daisy_server.BLOCK_SIZE = 16
    ret = log_from_stream(res, data, log_func)
    daisy_server.BLOCK_SIZE = pre_val
    assert expected == ret


@pytest.mark.parametrize('filename, size, send', [
    ('test_file_name', 1024, 1000),
    ('test_file_name', 2048, 2048),
    ('test_file_name_1234', 2097152, 2097152)])
@mock.patch('deploy.daisy_server.LD')
def test_log_scp(mock_LD, filename, size, send):
    pre_val = daisy_server.LEN_OF_NAME_PART
    daisy_server.LEN_OF_NAME_PART = 24
    log_scp(filename, size, send)
    daisy_server.LEN_OF_NAME_PART = pre_val
    if size != send:
        mock_LD.assert_not_called()
    elif len(filename) <= 18:
        mock_LD.assert_called_once()
    else:
        assert mock_LD.call_count == 2


daisy_server_info = {
    'name': 'daisy',
    'image': 'daisy.qcow2',
    'address': '10.20.0.2',
    'gateway': '10.20.0.1',
    'password': 'r00tme',
    'disk_size': 50
}
adapter = 'ipmi'
scenario = 'os-odl-nofeature-ha'
deploy_file_name = 'final_deploy.yml'
net_file_name = 'network_baremetal.yml'
remote_dir = '/home/daisy'
bin_file_name = 'opnfv.bin'


def test_create_DaisyServer_instance(tmpdir):
    bin_file = os.path.join(tmpdir.dirname, tmpdir.basename, bin_file_name)
    DaisyServerInst = DaisyServer(daisy_server_info['name'],
                                  daisy_server_info['address'],
                                  daisy_server_info['password'],
                                  remote_dir,
                                  bin_file,
                                  adapter,
                                  scenario,
                                  deploy_file_name,
                                  net_file_name)
    assert (DaisyServerInst.name == daisy_server_info['name'] and
            DaisyServerInst.address == daisy_server_info['address'] and
            DaisyServerInst.password == daisy_server_info['password'] and
            DaisyServerInst.remote_dir == remote_dir and
            DaisyServerInst.bin_file == bin_file and
            DaisyServerInst.adapter == adapter and
            DaisyServerInst.scenario == scenario and
            DaisyServerInst.deploy_file_name == deploy_file_name and
            DaisyServerInst.net_file_name == net_file_name and
            DaisyServerInst.ssh_client is None)
    tmpdir.remove()


@mock.patch.object(daisy_server.paramiko.SSHClient, 'connect')
@mock.patch.object(daisy_server.DaisyServer, 'ssh_run')
def test_connect_DaisyServer(mock_ssh_run, mock_connect, tmpdir):
    bin_file = os.path.join(tmpdir.dirname, tmpdir.basename, bin_file_name)
    mock_connect.return_value = 0
    DaisyServerInst = DaisyServer(daisy_server_info['name'],
                                  daisy_server_info['address'],
                                  daisy_server_info['password'],
                                  remote_dir,
                                  bin_file,
                                  adapter,
                                  scenario,
                                  deploy_file_name,
                                  net_file_name)
    DaisyServerInst.connect()
    mock_ssh_run.assert_called_once_with('ls -al', check=True)
    tmpdir.remove()


@mock.patch.object(daisy_server.paramiko.SSHClient, 'close')
@mock.patch.object(daisy_server.paramiko.SSHClient, 'connect')
@mock.patch.object(daisy_server.DaisyServer, 'ssh_run')
def test_close_DaisyServer(mock_ssh_run, mock_connect,
                           mock_close, tmpdir):
    bin_file = os.path.join(tmpdir.dirname, tmpdir.basename, bin_file_name)
    mock_connect.return_value = 0
    mock_ssh_run.return_valule = 0
    mock_close.return_value = 0
    DaisyServerInst = DaisyServer(daisy_server_info['name'],
                                  daisy_server_info['address'],
                                  daisy_server_info['password'],
                                  remote_dir,
                                  bin_file,
                                  adapter,
                                  scenario,
                                  deploy_file_name,
                                  net_file_name)
    DaisyServerInst.connect()
    DaisyServerInst.close()
    mock_close.assert_called_once_with()
    tmpdir.remove()


stdout1 = open(os.path.join(ssh_test_file_dir(), 'sim_stdout_file'))
stdin1 = open(os.path.join(ssh_test_file_dir(), 'sim_stdout_file'))
stderr1 = open(os.path.join(ssh_test_file_dir(), 'sim_stderr_file'))
stderr2 = open(os.path.join(ssh_test_file_dir(), 'sim_stdout_file'))


@pytest.mark.parametrize('stdout, stdin, stderr', [
    (stdout1, stdin1, stderr1),
    (stdout1, stdin1, stderr2)])
@mock.patch('deploy.daisy_server.err_exit')
@mock.patch.object(daisy_server.paramiko.SSHClient, 'connect')
@mock.patch.object(daisy_server.paramiko.SSHClient, 'exec_command')
@mock.patch.object(daisy_server.DaisyServer, 'ssh_run')
def test_ssh_exec_cmd_DaisyServer(mock_ssh_run, mock_exec_command,
                                  mock_connect, mock_err_exit,
                                  stdout, stdin, stderr, tmpdir):
    bin_file = os.path.join(tmpdir.dirname, tmpdir.basename, bin_file_name)
    cmd = 'ls -l'
    mock_connect.return_value = 0
    mock_ssh_run.return_valule = 0
    expect = 'stdout file data'
    mock_exec_command.return_value = (stdin, stdout, stderr)
    DaisyServerInst = DaisyServer(daisy_server_info['name'],
                                  daisy_server_info['address'],
                                  daisy_server_info['password'],
                                  remote_dir,
                                  bin_file,
                                  adapter,
                                  scenario,
                                  deploy_file_name,
                                  net_file_name)
    DaisyServerInst.connect()
    ret = DaisyServerInst.ssh_exec_cmd(cmd)
    mock_exec_command.assert_called_once()
    if stderr == stderr1:
        if stdout == stdout1:
            assert ret == expect
    elif stderr == stderr2:
        mock_err_exit.assert_called_once_with('SSH client error occurred')
    tmpdir.remove()


@pytest.mark.parametrize('check, is_recv_exit_status, expect', [
    (False, 0, 0),
    (True, 1, 1)])
@mock.patch('deploy.daisy_server.err_exit')
@mock.patch.object(daisy_server.paramiko.SSHClient, 'get_transport')
def test_ssh_run_DaisyServer(mock_get_transport, mock_err_exit,
                             check, is_recv_exit_status,
                             expect, tmpdir):
    class TestSession():

        def __init__(self, is_recv_exit_status):
            self.recv_data = 'recv_test_data'
            self.recv_data_total_len = len(self.recv_data)
            self.recv_data_read_index = 0
            self.recv_err_data = 'recv_test_err_data'
            self.recv_err_data_total_len = len(self.recv_err_data)
            self.recv_err_data_read_index = 0
            self.is_recv_exit_status = is_recv_exit_status
            return None

        def exec_command(self, cmd):
            return 0

        def recv_ready(self):
            return True

        def recv(self, size):
            if self.recv_data_read_index < self.recv_data_total_len:
                if size <= self.recv_data_total_len - self.recv_data_read_index:
                    cur_index = self.recv_data_read_index
                    self.recv_data_read_index += size
                    return self.recv_data[cur_index:self.recv_data_read_index]
                else:
                    cur_index = self.recv_data_read_index
                    self.recv_data_read_index = self.recv_data_total_len
                    return self.recv_data[cur_index:]
            else:
                return None

        def recv_stderr_ready(self):
            return True

        def recv_stderr(self, size):
            if self.recv_err_data_read_index < self.recv_err_data_total_len:
                if size <= self.recv_err_data_total_len - self.recv_err_data_read_index:
                    cur_index = self.recv_err_data_read_index
                    self.recv_err_data_read_index += size
                    return self.recv_err_data[cur_index:self.recv_err_data_read_index]
                else:
                    cur_index = self.recv_err_data_read_index
                    self.recv_err_data_read_index = self.recv_err_data_total_len
                    return self.recv_err_data[cur_index:]
            else:
                return None

        def exit_status_ready(self):
            return True

        def recv_exit_status(self):
            return self.is_recv_exit_status

    class TestTransport():
        def __init__(self, is_recv_exit_status):
            self.is_recv_exit_status = is_recv_exit_status

        def set_keepalive(self, time):
            self.time = time

        def open_session(self):
            return TestSession(is_recv_exit_status)

    bin_file = os.path.join(tmpdir.dirname, tmpdir.basename, bin_file_name)
    cmd = 'ls -l'
    mock_get_transport.return_value = TestTransport(is_recv_exit_status)
    DaisyServerInst = DaisyServer(daisy_server_info['name'],
                                  daisy_server_info['address'],
                                  daisy_server_info['password'],
                                  remote_dir,
                                  bin_file,
                                  adapter,
                                  scenario,
                                  deploy_file_name,
                                  net_file_name)
    DaisyServerInst.ssh_client = paramiko.SSHClient()
    DaisyServerInst.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ret = DaisyServerInst.ssh_run(cmd, check=check)
    if check and is_recv_exit_status:
        mock_err_exit.assert_called_once()
    assert ret == expect
    tmpdir.remove()


@mock.patch.object(daisy_server.scp.SCPClient, 'get')
@mock.patch.object(daisy_server.paramiko.SSHClient, 'get_transport')
@mock.patch.object(daisy_server.paramiko.SSHClient, 'connect')
@mock.patch.object(daisy_server.paramiko.SSHClient, 'exec_command')
@mock.patch.object(daisy_server.DaisyServer, 'ssh_run')
def test_scp_get_DaisyServer(mock_ssh_run, mock_exec_command,
                             mock_connect, mock_get_transport,
                             mock_get, tmpdir):
    bin_file = os.path.join(tmpdir.dirname, tmpdir.basename, bin_file_name)
    mock_connect.return_value = 0
    mock_ssh_run.return_valule = 0
    remote = '/remote_dir'
    local = '.'
    DaisyServerInst = DaisyServer(daisy_server_info['name'],
                                  daisy_server_info['address'],
                                  daisy_server_info['password'],
                                  remote_dir,
                                  bin_file,
                                  adapter,
                                  scenario,
                                  deploy_file_name,
                                  net_file_name)
    DaisyServerInst.connect()
    DaisyServerInst.scp_get(remote, local)
    mock_get.assert_called_once_with(remote, local_path=local, recursive=True)
    tmpdir.remove()


@mock.patch.object(daisy_server.scp.SCPClient, 'put')
@mock.patch.object(daisy_server.paramiko.SSHClient, 'get_transport')
@mock.patch.object(daisy_server.paramiko.SSHClient, 'connect')
@mock.patch.object(daisy_server.paramiko.SSHClient, 'exec_command')
@mock.patch.object(daisy_server.DaisyServer, 'ssh_run')
def test_scp_put_DaisyServer(mock_ssh_run, mock_exec_command,
                             mock_connect, mock_get_transport,
                             mock_put, tmpdir):
    bin_file = os.path.join(tmpdir.dirname, tmpdir.basename, bin_file_name)
    mock_connect.return_value = 0
    mock_ssh_run.return_valule = 0
    remote = '.'
    local = '/tmp'
    DaisyServerInst = DaisyServer(daisy_server_info['name'],
                                  daisy_server_info['address'],
                                  daisy_server_info['password'],
                                  remote_dir,
                                  bin_file,
                                  adapter,
                                  scenario,
                                  deploy_file_name,
                                  net_file_name)
    DaisyServerInst.connect()
    DaisyServerInst.scp_put(local, remote)
    mock_put.assert_called_once_with(local, remote_path=remote, recursive=True)
    tmpdir.remove()


@mock.patch.object(daisy_server.DaisyServer, 'ssh_exec_cmd')
def test_create_dir_DaisyServer(mock_ssh_exec_cmd, tmpdir):
    remote_dir_test = '/home/daisy/test'
    cmd = 'mkdir -p ' + remote_dir_test
    bin_file = os.path.join(tmpdir.dirname, tmpdir.basename, bin_file_name)
    DaisyServerInst = DaisyServer(daisy_server_info['name'],
                                  daisy_server_info['address'],
                                  daisy_server_info['password'],
                                  remote_dir,
                                  bin_file,
                                  adapter,
                                  scenario,
                                  deploy_file_name,
                                  net_file_name)
    DaisyServerInst.create_dir(remote_dir_test)
    DaisyServerInst.ssh_exec_cmd.assert_called_once_with(cmd)
    tmpdir.remove()


@mock.patch.object(daisy_server.DaisyServer, 'ssh_exec_cmd')
def test_delete_dir_DaisyServer(mock_ssh_exec_cmd, tmpdir):
    remote_dir_test = '/home/daisy/test'
    cmd = 'if [[ -f {DIR} || -d {DIR} ]]; then rm -fr {DIR}; fi'.format(DIR=remote_dir_test)
    bin_file = os.path.join(tmpdir.dirname, tmpdir.basename, bin_file_name)
    DaisyServerInst = DaisyServer(daisy_server_info['name'],
                                  daisy_server_info['address'],
                                  daisy_server_info['password'],
                                  remote_dir,
                                  bin_file,
                                  adapter,
                                  scenario,
                                  deploy_file_name,
                                  net_file_name)
    DaisyServerInst.delete_dir(remote_dir_test)
    DaisyServerInst.ssh_exec_cmd.assert_called_once_with(cmd)
    tmpdir.remove()


bin_file_path1 = os.path.join('/tmp', bin_file_name)
bin_file_path2 = os.path.join(WORKSPACE, bin_file_name)


@pytest.mark.parametrize('bin_file', [
    (bin_file_path1),
    (bin_file_path2)])
@mock.patch.object(daisy_server.DaisyServer, 'delete_dir')
@mock.patch.object(daisy_server.DaisyServer, 'scp_put')
@mock.patch.object(daisy_server.DaisyServer, 'create_dir')
@mock.patch('deploy.daisy_server.update_config')
def test_prepare_files_DaisyServer(mock_update_config,
                                   mock_create_dir,
                                   mock_scp_put,
                                   mock_delete_dir,
                                   bin_file,
                                   tmpdir):
    DaisyServerInst = DaisyServer(daisy_server_info['name'],
                                  daisy_server_info['address'],
                                  daisy_server_info['password'],
                                  remote_dir,
                                  bin_file,
                                  adapter,
                                  scenario,
                                  deploy_file_name,
                                  net_file_name)
    DaisyServerInst.prepare_files()
    DaisyServerInst.delete_dir.assert_called_once_with(remote_dir)
    DaisyServerInst.create_dir.assert_called_once_with('/home/daisy_install')
    if bin_file == bin_file_path1:
        assert DaisyServerInst.scp_put.call_count == 3
    else:
        assert DaisyServerInst.scp_put.call_count == 2
    tmpdir.remove()


@mock.patch.object(daisy_server.DaisyServer, 'ssh_run')
@mock.patch.object(daisy_server.DaisyServer, 'prepare_files')
def test_install_daisy_DaisyServer(mock_prepare_files, mock_ssh_run, tmpdir):
    bin_file = os.path.join(tmpdir.dirname, tmpdir.basename, bin_file_name)
    DaisyServerInst = DaisyServer(daisy_server_info['name'],
                                  daisy_server_info['address'],
                                  daisy_server_info['password'],
                                  remote_dir,
                                  bin_file,
                                  adapter,
                                  scenario,
                                  deploy_file_name,
                                  net_file_name)
    mock_ssh_run.return_value = 0
    cmd = '%s install' % os.path.join(remote_dir, 'opnfv.bin')
    DaisyServerInst.install_daisy()
    DaisyServerInst.ssh_run.assert_called_once_with(cmd)
    DaisyServerInst.prepare_files.assert_called_once_with()
    tmpdir.remove()


@pytest.mark.parametrize('adapter', [
    ('libvirt'), ('ipmi')])
@mock.patch.object(daisy_server.DaisyServer, 'ssh_run')
def test_prepare_configurations_DaisyServer(mock_ssh_run, adapter, tmpdir):
    bin_file = os.path.join(tmpdir.dirname, tmpdir.basename, bin_file_name)
    DaisyServerInst = DaisyServer(daisy_server_info['name'],
                                  daisy_server_info['address'],
                                  daisy_server_info['password'],
                                  remote_dir,
                                  bin_file,
                                  adapter,
                                  scenario,
                                  deploy_file_name,
                                  net_file_name)
    mock_ssh_run.return_value = 0
    cmd = 'export PYTHONPATH={python_path}; python {script} -nw {net_file} -b {is_bare}'.format(
        python_path=remote_dir,
        script=os.path.join(remote_dir, 'deploy/prepare/execute.py'),
        net_file=os.path.join(remote_dir, net_file_name),
        is_bare=1 if adapter == 'ipmi' else 0)
    DaisyServerInst.prepare_configurations()
    if adapter == 'libvirt':
        DaisyServerInst.ssh_run.assert_called_once_with(cmd)
    else:
        DaisyServerInst.ssh_run.assert_not_called()
    tmpdir.remove()


@mock.patch.object(daisy_server.DaisyServer, 'scp_put')
@mock.patch.object(daisy_server.DaisyServer, 'prepare_configurations')
@mock.patch.object(daisy_server.DaisyServer, 'ssh_run')
def test_prepare_cluster_DaisyServer(mock_scp_put,
                                     mock_prepare_configurations,
                                     mock_ssh_run,
                                     tmpdir):
    bin_file = os.path.join(tmpdir.dirname, tmpdir.basename, bin_file_name)
    DaisyServerInst = DaisyServer(daisy_server_info['name'],
                                  daisy_server_info['address'],
                                  daisy_server_info['password'],
                                  remote_dir,
                                  bin_file,
                                  adapter,
                                  scenario,
                                  deploy_file_name,
                                  net_file_name)
    mock_ssh_run.return_value = 0
    cmd = "python {script} --dha {deploy_file} --network {net_file} --cluster \'yes\'".format(
        script=os.path.join(remote_dir, 'deploy/tempest.py'),
        deploy_file=os.path.join(remote_dir, deploy_file_name),
        net_file=os.path.join(remote_dir, net_file_name))
    deploy_file = os.path.join(tmpdir.dirname, tmpdir.basename, deploy_file_name)
    net_file = os.path.join(tmpdir.dirname, tmpdir.basename, net_file_name)
    DaisyServerInst.prepare_cluster(deploy_file, net_file)
    DaisyServerInst.ssh_run.assert_called_once_with(cmd, check=True)
    DaisyServerInst.prepare_configurations.assert_called_once_with()
    assert DaisyServerInst.scp_put.call_count == 2
    tmpdir.remove()


@mock.patch.object(daisy_server.DaisyServer, 'scp_put')
def test_copy_new_deploy_config_DaisyServer(mock_scp_put, tmpdir):
    bin_file = os.path.join(tmpdir.dirname, tmpdir.basename, bin_file_name)
    adapter = 'libvirt'
    DaisyServerInst = DaisyServer(daisy_server_info['name'],
                                  daisy_server_info['address'],
                                  daisy_server_info['password'],
                                  remote_dir,
                                  bin_file,
                                  adapter,
                                  scenario,
                                  deploy_file_name,
                                  net_file_name)
    mock_scp_put.return_value = 0
    data = {
        'adapter': 'ipmi',
        'hosts': [
            {
                'name': 'controller01',
                'roles': ['CONTROLLER_LB'],
                'ipmi_ip': '192.168.1.11',
                'ipmi_user': 'testuser',
                'ipmi_pass': 'testpass'
            }
        ],
        'disks': {
            'daisy': 50
        },
        'daisy_passwd': 'r00tme'
    }
    DaisyServerInst.copy_new_deploy_config(data)
    assert DaisyServerInst.scp_put.call_count == 1
    tmpdir.remove()


@mock.patch.object(daisy_server.DaisyServer, 'ssh_run')
def test_prepare_host_and_pxe_DaisyServer(mock_ssh_run, tmpdir):
    bin_file = os.path.join(tmpdir.dirname, tmpdir.basename, bin_file_name)
    adapter = 'libvirt'
    DaisyServerInst = DaisyServer(daisy_server_info['name'],
                                  daisy_server_info['address'],
                                  daisy_server_info['password'],
                                  remote_dir,
                                  bin_file,
                                  adapter,
                                  scenario,
                                  deploy_file_name,
                                  net_file_name)
    mock_ssh_run.return_value = 0
    cmd = "python {script} --dha {deploy_file} --network {net_file} --host \'yes\' --isbare {is_bare} --scenario {scenario}".format(
        script=os.path.join(remote_dir, 'deploy/tempest.py'),
        deploy_file=os.path.join(remote_dir, deploy_file_name),
        net_file=os.path.join(remote_dir, net_file_name),
        is_bare=1 if adapter == 'ipmi' else 0,
        scenario=scenario)
    DaisyServerInst.prepare_host_and_pxe()
    DaisyServerInst.ssh_run.assert_called_once_with(cmd, check=True)
    tmpdir.remove()


@mock.patch.object(daisy_server.DaisyServer, 'ssh_run')
def test_install_virtual_nodes_DaisyServer(mock_ssh_run, tmpdir):
    bin_file = os.path.join(tmpdir.dirname, tmpdir.basename, bin_file_name)
    adapter = 'libvirt'
    DaisyServerInst = DaisyServer(daisy_server_info['name'],
                                  daisy_server_info['address'],
                                  daisy_server_info['password'],
                                  remote_dir,
                                  bin_file,
                                  adapter,
                                  scenario,
                                  deploy_file_name,
                                  net_file_name)
    mock_ssh_run.return_value = 0
    cmd = "python {script} --dha {deploy_file} --network {net_file} --install \'yes\'".format(
        script=os.path.join(remote_dir, 'deploy/tempest.py'),
        deploy_file=os.path.join(remote_dir, deploy_file_name),
        net_file=os.path.join(remote_dir, net_file_name))
    DaisyServerInst.install_virtual_nodes()
    DaisyServerInst.ssh_run.assert_called_once_with(cmd, check=True)
    tmpdir.remove()


@mock.patch.object(daisy_server.DaisyServer, 'ssh_run')
def test_check_os_installation_DaisyServer(mock_ssh_run, tmpdir):
    bin_file = os.path.join(tmpdir.dirname, tmpdir.basename, bin_file_name)
    adapter = 'libvirt'
    DaisyServerInst = DaisyServer(daisy_server_info['name'],
                                  daisy_server_info['address'],
                                  daisy_server_info['password'],
                                  remote_dir,
                                  bin_file,
                                  adapter,
                                  scenario,
                                  deploy_file_name,
                                  net_file_name)
    mock_ssh_run.return_value = 0
    nodes_num = 5
    cmd = '{script} -d {is_bare} -n {nodes_num}'.format(
        script=os.path.join(remote_dir, 'deploy/check_os_progress.sh'),
        is_bare=1 if adapter == 'ipmi' else 0,
        nodes_num=nodes_num)
    DaisyServerInst.check_os_installation(nodes_num)
    DaisyServerInst.ssh_run.assert_called_once_with(cmd, check=True)
    tmpdir.remove()


@mock.patch.object(daisy_server.DaisyServer, 'ssh_run')
def test_check_openstack_installation_DaisyServer(mock_ssh_run, tmpdir):
    bin_file = os.path.join(tmpdir.dirname, tmpdir.basename, bin_file_name)
    adapter = 'libvirt'
    DaisyServerInst = DaisyServer(daisy_server_info['name'],
                                  daisy_server_info['address'],
                                  daisy_server_info['password'],
                                  remote_dir,
                                  bin_file,
                                  adapter,
                                  scenario,
                                  deploy_file_name,
                                  net_file_name)
    mock_ssh_run.return_value = 0
    nodes_num = 5
    cmd = '{script} -n {nodes_num}'.format(
        script=os.path.join(remote_dir, 'deploy/check_openstack_progress.sh'),
        nodes_num=nodes_num)
    DaisyServerInst.check_openstack_installation(nodes_num)
    DaisyServerInst.ssh_run.assert_called_once_with(cmd, check=True)
    tmpdir.remove()


@mock.patch.object(daisy_server.DaisyServer, 'ssh_run')
def test_post_deploy_DaisyServer(mock_ssh_run, tmpdir):
    bin_file = os.path.join(tmpdir.dirname, tmpdir.basename, bin_file_name)
    adapter = 'libvirt'
    DaisyServerInst = DaisyServer(daisy_server_info['name'],
                                  daisy_server_info['address'],
                                  daisy_server_info['password'],
                                  remote_dir,
                                  bin_file,
                                  adapter,
                                  scenario,
                                  deploy_file_name,
                                  net_file_name)
    mock_ssh_run.return_value = 0
    cmd = 'export PYTHONPATH={python_path}; python {script} -nw {net_file}'.format(
        python_path=remote_dir,
        script=os.path.join(remote_dir, 'deploy/post/execute.py'),
        net_file=os.path.join(remote_dir, net_file_name))
    DaisyServerInst.post_deploy()
    DaisyServerInst.ssh_run.assert_called_once_with(cmd, check=False)
    tmpdir.remove()
