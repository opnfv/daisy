import os
import pytest
import mock

from deploy import daisy_server
from deploy.daisy_server import (
    DaisyServer
)


@pytest.fixture(scope="session")
def conf_file_dir(data_root):
    return os.path.join(data_root, 'lab_conf')


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


@mock.patch.object(daisy_server.DaisyServer, 'delete_dir')
@mock.patch.object(daisy_server.DaisyServer, 'scp_put')
@mock.patch.object(daisy_server.DaisyServer, 'create_dir')
@mock.patch('deploy.daisy_server.update_config')
def test_prepare_files_DaisyServer(mock_update_config,
                                   mock_create_dir,
                                   mock_scp_put,
                                   mock_delete_dir,
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
    DaisyServerInst.prepare_files()
    DaisyServerInst.delete_dir.assert_called_once_with(remote_dir)
    DaisyServerInst.create_dir.assert_called_once_with('/home/daisy_install')
    assert DaisyServerInst.scp_put.call_count == 3
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


@mock.patch.object(daisy_server.DaisyServer, 'ssh_run')
def test_prepare_configurations_DaisyServer(mock_ssh_run, tmpdir):
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
    cmd = 'export PYTHONPATH={python_path}; python {script} -nw {net_file} -b {is_bare}'.format(
        python_path=remote_dir,
        script=os.path.join(remote_dir, 'deploy/prepare/execute.py'),
        net_file=os.path.join(remote_dir, net_file_name),
        is_bare=1 if adapter == 'ipmi' else 0)
    DaisyServerInst.prepare_configurations()
    DaisyServerInst.ssh_run.assert_called_once_with(cmd)
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
