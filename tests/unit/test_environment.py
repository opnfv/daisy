import os
import copy
import mock
import yaml
import pytest
from deepdiff import DeepDiff

from deploy.utils import WORKSPACE
from deploy import environment
from deploy import daisy_server
from deploy.daisy_server import DaisyServer
from deploy.environment import (
    DaisyEnvironmentBase,
    BareMetalEnvironment,
    VirtualEnvironment,
    BMDEPLOY_DAISY_SERVER_VM,
    VMDEPLOY_DAISY_SERVER_NET,
    VMDEPLOY_DAISY_SERVER_VM,
)


def get_conf_file_dir():
    return os.path.join(WORKSPACE, 'tests/data/lab_conf')


def get_conf_info_from_file(file_dir, conf_file_name):
    conf_file_path = os.path.join(file_dir, conf_file_name)
    with open(conf_file_path) as f:
        conf_info = yaml.safe_load(f)
        return conf_info


deploy_struct = get_conf_info_from_file(get_conf_file_dir(), 'deploy_baremetal.yml')
deploy_virtual_struct = get_conf_info_from_file(get_conf_file_dir(), 'deploy_virtual1.yml')
deploy_virtual2_struct = get_conf_info_from_file(get_conf_file_dir(), 'deploy_virtual2.yml')
net_struct = get_conf_info_from_file(get_conf_file_dir(), 'network_baremetal.yml')
adapter = 'ipmi'
adapter_virtual = 'libvirt'
pxe_bridge = 'br7'
pxe_bridge_virtual = 'daisy1'
daisy_server_info = {
    'name': 'daisy',
    'image': 'daisy.qcow2',
    'address': '10.20.0.2',
    'gateway': '10.20.0.1',
    'password': 'r00tme',
    'disk_size': 50
}
work_dir_name = 'workdir'
storage_dir_name = 'vms'
scenario = 'os-odl-nofeature-ha'


def test_create_DaisyEnvironmentBase_instance(tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    DaisyEnvBaseInst = DaisyEnvironmentBase(
        deploy_struct, net_struct, adapter, pxe_bridge,
        daisy_server, work_dir, storage_dir, scenario)
    assert (DaisyEnvBaseInst.deploy_struct == deploy_struct and
            DaisyEnvBaseInst.net_struct == net_struct and
            DaisyEnvBaseInst.adapter == adapter and
            DaisyEnvBaseInst.pxe_bridge == pxe_bridge and
            DaisyEnvBaseInst.daisy_server_info == daisy_server and
            DaisyEnvBaseInst.work_dir == work_dir and
            DaisyEnvBaseInst.storage_dir == storage_dir and
            DaisyEnvBaseInst.scenario == scenario)
    tmpdir.remove()


def test_delete_daisy_server_DaisyEnvironmentBase(tmpdir, mocker):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    DaisyEnvBaseInst = DaisyEnvironmentBase(
        deploy_struct, net_struct, adapter, pxe_bridge,
        daisy_server, work_dir, storage_dir, scenario)
    mocker.patch('deploy.environment.delete_vm_and_disk')
    DaisyEnvBaseInst.delete_daisy_server()
    environment.delete_vm_and_disk.assert_called_once_with('daisy')
    tmpdir.remove()


@pytest.mark.parametrize('ret_run_shell, ret_access', [
    (0, 1),
    (1, 0)])
@mock.patch('deploy.environment.os.access')
@mock.patch('deploy.environment.os.remove')
@mock.patch('deploy.environment.shutil.move')
@mock.patch('deploy.environment.err_exit')
@mock.patch('deploy.environment.run_shell')
def test_create_daisy_server_image_DaisyEnvironmentBase(mock_run_shell, mock_err_exit,
                                                        mock_move, mock_remove,
                                                        mock_access, tmpdir,
                                                        ret_run_shell, ret_access):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    os.makedirs(work_dir, 0755)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    os.makedirs(storage_dir, 0755)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    DaisyEnvBaseInst = DaisyEnvironmentBase(
        deploy_struct, net_struct, adapter, pxe_bridge,
        daisy_server, work_dir, storage_dir, scenario)
    mock_run_shell.return_value = ret_run_shell
    mock_access.return_value = ret_access
    mock_err_exit.return_value = 0

    DaisyEnvBaseInst.create_daisy_server_image()
    if ret_run_shell:
        mock_err_exit.assert_called_once_with('Failed to create Daisy Server image')
    else:
        if ret_access:
            mock_remove.assert_called_once_with(DaisyEnvBaseInst.daisy_server_info['image'])
        else:
            mock_move.assert_called_once()
    tmpdir.remove()


@mock.patch.object(daisy_server.DaisyServer, 'connect')
@mock.patch.object(daisy_server.DaisyServer, 'install_daisy')
def test_install_daisy_DaisyEnvironmentBase(mock_install_daisy, mock_connect, tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    os.makedirs(work_dir, 0755)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    os.makedirs(storage_dir, 0755)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    remote_dir = '/home/daisy'
    bin_file = os.path.join(tmpdir.dirname, tmpdir.basename, 'opnfv.bin')
    deploy_file_name = 'final_deploy.yml'
    net_file_name = 'network_baremetal.yml'
    DaisyEnvBaseInst = DaisyEnvironmentBase(
        deploy_struct, net_struct, adapter, pxe_bridge,
        daisy_server, work_dir, storage_dir, scenario)
    DaisyEnvBaseInst.install_daisy(remote_dir, bin_file, deploy_file_name, net_file_name)
    mock_install_daisy.assert_called_once_with()
    mock_connect.assert_called_once_with()
    tmpdir.remove()


def test_create_BareMetalEnvironment_instance(tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    BareMetalEnvironmentInst = BareMetalEnvironment(
        deploy_struct, net_struct, adapter, pxe_bridge,
        daisy_server, work_dir, storage_dir, scenario)
    assert (BareMetalEnvironmentInst.deploy_struct == deploy_struct and
            BareMetalEnvironmentInst.net_struct == net_struct and
            BareMetalEnvironmentInst.adapter == adapter and
            BareMetalEnvironmentInst.pxe_bridge == pxe_bridge and
            BareMetalEnvironmentInst.daisy_server_info == daisy_server and
            BareMetalEnvironmentInst.work_dir == work_dir and
            BareMetalEnvironmentInst.storage_dir == storage_dir and
            BareMetalEnvironmentInst.scenario == scenario)
    tmpdir.remove()


@mock.patch.object(environment.DaisyEnvironmentBase, 'delete_daisy_server')
def test_delete_old_environment_BareMetalEnvironment(mock_delete_daisy_server, tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    mock_delete_daisy_server.return_value = None
    BareMetalEnvironmentInst = BareMetalEnvironment(
        deploy_struct, net_struct, adapter, pxe_bridge,
        daisy_server, work_dir, storage_dir, scenario)
    BareMetalEnvironmentInst.delete_old_environment()
    BareMetalEnvironmentInst.delete_daisy_server.assert_called_once_with()
    tmpdir.remove()


def test_create_daisy_server_vm_BareMetalEnvironment(mocker, tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    mocker.patch('deploy.environment.create_vm')
    BareMetalEnvironmentInst = BareMetalEnvironment(
        deploy_struct, net_struct, adapter, pxe_bridge,
        daisy_server, work_dir, storage_dir, scenario)
    BareMetalEnvironmentInst.create_daisy_server_vm()
    environment.create_vm.assert_called_once_with(BMDEPLOY_DAISY_SERVER_VM,
                                                  name=daisy_server['name'],
                                                  disks=[daisy_server['image']],
                                                  physical_bridge=pxe_bridge)
    tmpdir.remove()


@pytest.mark.parametrize('deploy_struct_info', [
    (deploy_struct)])
@mock.patch('deploy.environment.ipmi_reboot_node')
def test_reboot_nodes_BareMetalEnvironment(mock_ipmi_reboot_node,
                                           deploy_struct_info, tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    mock_ipmi_reboot_node.return_value = True
    BareMetalEnvironmentInst = BareMetalEnvironment(
        deploy_struct_info, net_struct, adapter, pxe_bridge,
        daisy_server, work_dir, storage_dir, scenario)
    BareMetalEnvironmentInst.reboot_nodes()
    assert mock_ipmi_reboot_node.call_count == 5
    tmpdir.remove()


@pytest.mark.parametrize('deploy_struct_info', [
    (deploy_virtual_struct)])
def test_reboot_nodes_err_BareMetalEnvironment(deploy_struct_info, tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    BareMetalEnvironmentInst = BareMetalEnvironment(
        deploy_struct_info, net_struct, adapter, pxe_bridge,
        daisy_server, work_dir, storage_dir, scenario)
    with pytest.raises(SystemExit):
        BareMetalEnvironmentInst.reboot_nodes()
    tmpdir.remove()


@mock.patch.object(environment.DaisyEnvironmentBase, 'create_daisy_server_image')
@mock.patch.object(environment.BareMetalEnvironment, 'create_daisy_server_vm')
def test_create_daisy_server_BareMetalEnvironment(mock_create_daisy_server_vm, mock_create_daisy_server_image, tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    mock_create_daisy_server_vm.return_value = None
    mock_create_daisy_server_image.return_value = None
    BareMetalEnvironmentInst = BareMetalEnvironment(
        deploy_struct, net_struct, adapter, pxe_bridge,
        daisy_server, work_dir, storage_dir, scenario)
    BareMetalEnvironmentInst.create_daisy_server()
    BareMetalEnvironmentInst.create_daisy_server_image.assert_called_once_with()
    BareMetalEnvironmentInst.create_daisy_server_vm.assert_called_once_with()
    tmpdir.remove()


@mock.patch.object(daisy_server.DaisyServer, 'prepare_cluster')
@mock.patch.object(environment.BareMetalEnvironment, 'reboot_nodes')
@mock.patch.object(daisy_server.DaisyServer, 'prepare_host_and_pxe')
@mock.patch.object(daisy_server.DaisyServer, 'check_os_installation')
@mock.patch.object(daisy_server.DaisyServer, 'check_openstack_installation')
@mock.patch.object(daisy_server.DaisyServer, 'post_deploy')
def test_deploy_BareMetalEnvironment(mock_post_deploy, mock_check_openstack_installation,
                                     mock_check_os_installation, mock_prepare_host_and_pxe,
                                     mock_reboot_nodes, mock_prepare_cluster,
                                     tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    deploy_file = os.path.join(get_conf_file_dir(), 'deploy_baremetal.yml')
    net_file = os.path.join(get_conf_file_dir(), 'network_baremetal.yml')
    remote_dir = '/home/daisy'
    bin_file = os.path.join(tmpdir.dirname, tmpdir.basename, 'opnfv.bin')
    deploy_file_name = 'final_deploy.yml'
    net_file_name = 'network_baremetal.yml'
    BareMetalEnvironmentInst = BareMetalEnvironment(
        deploy_struct, net_struct, adapter, pxe_bridge,
        daisy_server, work_dir, storage_dir, scenario)
    BareMetalEnvironmentInst.server = DaisyServer(
        daisy_server['name'],
        daisy_server['address'],
        daisy_server['password'],
        remote_dir,
        bin_file,
        adapter,
        scenario,
        deploy_file_name,
        net_file_name)
    BareMetalEnvironmentInst.deploy(deploy_file, net_file)
    mock_prepare_cluster.assert_called_once_with(deploy_file, net_file)
    mock_reboot_nodes.assert_called_once_with(boot_dev='pxe')
    mock_prepare_host_and_pxe.assert_called_once_with()
    mock_check_os_installation.assert_called_once_with(len(BareMetalEnvironmentInst.deploy_struct['hosts']))
    mock_check_openstack_installation.assert_called_once_with(len(BareMetalEnvironmentInst.deploy_struct['hosts']))
    mock_post_deploy.assert_called_once_with()
    tmpdir.remove()


def test_create_VirtualEnvironment_instance(tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    VirtualEnvironmentInst = VirtualEnvironment(
        deploy_virtual_struct, net_struct, adapter_virtual, pxe_bridge_virtual,
        daisy_server, work_dir, storage_dir, scenario)
    assert (DeepDiff(VirtualEnvironmentInst.deploy_struct, deploy_virtual_struct, ignore_order=True) == {} and
            VirtualEnvironmentInst.net_struct == net_struct and
            VirtualEnvironmentInst.adapter == adapter_virtual and
            VirtualEnvironmentInst.pxe_bridge == pxe_bridge_virtual and
            VirtualEnvironmentInst.daisy_server_info == daisy_server and
            VirtualEnvironmentInst.work_dir == work_dir and
            VirtualEnvironmentInst.storage_dir == storage_dir and
            VirtualEnvironmentInst.scenario == scenario and
            VirtualEnvironmentInst._daisy_server_net is None and
            VirtualEnvironmentInst._daisy_os_net is None and
            VirtualEnvironmentInst._daisy_keepalived_net is None)
    tmpdir.remove()


@mock.patch.object(environment.VirtualEnvironment, 'check_nodes_template')
def test_check_configuration_VirtualEnvironment(mock_check_nodes_template, tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    VirtualEnvironment(
        deploy_virtual_struct, net_struct, adapter_virtual, pxe_bridge_virtual,
        daisy_server, work_dir, storage_dir, scenario)
    mock_check_nodes_template.assert_called_once_with()
    tmpdir.remove()


deploy_virtual_invalid_struct = get_conf_info_from_file(get_conf_file_dir(), 'deploy_virtual_invalid_template.yml')


@pytest.mark.parametrize('deploy_struct_info', [
    (deploy_struct),
    (deploy_virtual_struct),
    (deploy_virtual_invalid_struct)])
@mock.patch('deploy.environment.err_exit')
def test_check_nodes_template_VirtualEnvironment(mock_err_exit, deploy_struct_info, tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    mock_err_exit.return_value = 0
    VirtualEnvironment(
        deploy_struct_info, net_struct, adapter_virtual, pxe_bridge_virtual,
        daisy_server, work_dir, storage_dir, scenario)
    if deploy_struct_info == deploy_struct:
        mock_err_exit.assert_not_called()
    elif deploy_struct_info == deploy_virtual_struct:
        mock_err_exit.assert_not_called()
    elif deploy_struct_info == deploy_virtual_invalid_struct:
        assert mock_err_exit.call_count == 5
    tmpdir.remove()


@pytest.mark.parametrize('net_name', [
    (pxe_bridge_virtual)])
@mock.patch('deploy.environment.create_virtual_network')
@mock.patch('deploy.environment.err_exit')
def test_create_daisy_server_network_VirtualEnvironment(mock_err_exit, mock_create_virtual_network,
                                                        net_name, tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    mock_create_virtual_network.return_value = net_name
    mock_err_exit.return_value = 0
    VirtualEnvironmentInst = VirtualEnvironment(
        deploy_virtual_struct, net_struct, adapter_virtual, pxe_bridge_virtual,
        daisy_server, work_dir, storage_dir, scenario)
    VirtualEnvironmentInst.create_daisy_server_network()
    mock_create_virtual_network.assert_called_once_with(VMDEPLOY_DAISY_SERVER_NET)
    if net_name == pxe_bridge_virtual:
        mock_err_exit.assert_not_called()
        assert VirtualEnvironmentInst._daisy_server_net == pxe_bridge_virtual
    elif net_name == pxe_bridge:
        mock_err_exit.assert_called_once()
    tmpdir.remove()


@mock.patch('deploy.environment.create_vm')
def test_create_daisy_server_vm_VirtualEnvironment(mock_create_vm, tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    mock_create_vm.return_value = True
    VirtualEnvironmentInst = VirtualEnvironment(
        deploy_virtual_struct, net_struct, adapter_virtual, pxe_bridge_virtual,
        daisy_server, work_dir, storage_dir, scenario)
    VirtualEnvironmentInst.create_daisy_server_vm()
    environment.create_vm.assert_called_once_with(VMDEPLOY_DAISY_SERVER_VM,
                                                  name=daisy_server['name'],
                                                  disks=[daisy_server['image']])
    tmpdir.remove()


@mock.patch.object(environment.DaisyEnvironmentBase, 'create_daisy_server_image')
@mock.patch.object(environment.VirtualEnvironment, 'create_daisy_server_network')
@mock.patch.object(environment.VirtualEnvironment, 'create_daisy_server_vm')
def test_create_daisy_server_VirtualEnvironment(mock_create_daisy_server_vm,
                                                mock_create_daisy_server_network,
                                                mock_create_daisy_server_image,
                                                tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    VirtualEnvironmentInst = VirtualEnvironment(
        deploy_virtual_struct, net_struct, adapter_virtual, pxe_bridge_virtual,
        daisy_server, work_dir, storage_dir, scenario)
    VirtualEnvironmentInst.create_daisy_server()
    VirtualEnvironmentInst.create_daisy_server_vm.assert_called_once_with()
    VirtualEnvironmentInst.create_daisy_server_network.assert_called_once_with()
    VirtualEnvironmentInst.create_daisy_server_image.assert_called_once_with()
    tmpdir.remove()


@pytest.mark.parametrize('deploy_info_struct, node_num', [
    (deploy_virtual_struct, 0),
    (deploy_virtual_struct, 3),
    (deploy_virtual2_struct, 0)])
@mock.patch('deploy.environment.create_vm')
@mock.patch('deploy.environment.create_virtual_disk')
def test_create_virtual_node_VirtualEnvironment(mock_create_virtual_disk, mock_create_vm,
                                                deploy_info_struct, node_num, tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    VirtualEnvironmentInst = VirtualEnvironment(
        deploy_info_struct, net_struct, adapter_virtual, pxe_bridge_virtual,
        daisy_server, work_dir, storage_dir, scenario)
    VirtualEnvironmentInst.create_virtual_node(deploy_info_struct['hosts'][node_num])
    name = deploy_info_struct['hosts'][node_num]['name']
    template = deploy_info_struct['hosts'][node_num]['template']
    if deploy_info_struct == deploy_virtual_struct:
        files = [os.path.join(storage_dir, name + '.qcow2'), os.path.join(storage_dir, name + '_data.qcow2')]
        assert environment.create_virtual_disk.call_count == 2
    elif deploy_info_struct == deploy_virtual2_struct:
        files = [os.path.join(storage_dir, name + '.qcow2')]
        assert environment.create_virtual_disk.call_count == 1
    environment.create_vm.assert_called_once_with(template, name, files)
    tmpdir.remove()


@mock.patch('deploy.environment.create_virtual_network')
@mock.patch('deploy.environment.get_vm_mac_addresses')
@mock.patch.object(environment.VirtualEnvironment, 'create_virtual_node')
def test_create_nodes_VirtualEnvironment(mock_create_virtual_node,
                                         mock_get_vm_mac_addresses,
                                         mock_create_virtual_network,
                                         tmpdir):
    keepalived_net_name = 'daisy3'
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    mock_create_virtual_network.return_value = keepalived_net_name
    mock_get_vm_mac_addresses.return_value = '02:42:b6:90:7c:b2'
    mock_create_virtual_node.return_value = 'test-domain'

    VirtualEnvironmentInst = VirtualEnvironment(
        deploy_virtual_struct, net_struct, adapter_virtual, pxe_bridge_virtual,
        daisy_server, work_dir, storage_dir, scenario)
    VirtualEnvironmentInst.create_nodes()
    assert (environment.create_virtual_network.call_count == 2 and
            environment.get_vm_mac_addresses.call_count == 5 and
            VirtualEnvironmentInst.create_virtual_node.call_count == 5)
    environment.get_vm_mac_addresses.assert_called_with('test-domain')
    assert VirtualEnvironmentInst._daisy_keepalived_net == keepalived_net_name
    tmpdir.remove()


@mock.patch('deploy.environment.delete_vm_and_disk')
def test_delete_nodes_VirtualEnvironment(mock_delete_vm_and_disk, tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    VirtualEnvironmentInst = VirtualEnvironment(
        deploy_virtual_struct, net_struct, adapter_virtual, pxe_bridge_virtual,
        daisy_server, work_dir, storage_dir, scenario)
    VirtualEnvironmentInst.delete_nodes()
    assert environment.delete_vm_and_disk.call_count == 5
    tmpdir.remove()


@mock.patch('deploy.environment.reboot_vm')
def test_reboot_nodes_VirtualEnvironment(mock_reboot_vm, tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    VirtualEnvironmentInst = VirtualEnvironment(
        deploy_virtual_struct, net_struct, adapter_virtual, pxe_bridge_virtual,
        daisy_server, work_dir, storage_dir, scenario)
    VirtualEnvironmentInst.reboot_nodes()
    assert environment.reboot_vm.call_count == 5
    tmpdir.remove()


@pytest.mark.parametrize('isdir', [
    (True),
    (False)])
@mock.patch('deploy.environment.delete_virtual_network')
@mock.patch('deploy.environment.os.path.isdir')
def test_delete_networks_VirtualEnvironment(mock_isdir, mock_delete_virtual_network, isdir, tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    mock_isdir.return_value = isdir
    VirtualEnvironmentInst = VirtualEnvironment(
        deploy_virtual_struct, net_struct, adapter_virtual, pxe_bridge_virtual,
        daisy_server, work_dir, storage_dir, scenario)
    VirtualEnvironmentInst.delete_networks()
    if isdir is True:
        assert mock_delete_virtual_network.call_count == 3
    else:
        mock_delete_virtual_network.assert_not_called()
    tmpdir.remove()


@mock.patch.object(environment.DaisyEnvironmentBase, 'delete_daisy_server')
@mock.patch.object(environment.VirtualEnvironment, 'delete_networks')
@mock.patch.object(environment.VirtualEnvironment, 'delete_nodes')
def test_delete_old_environment_VirtualEnvironment(mock_delete_daisy_server,
                                                   mock_delete_networks,
                                                   mock_delete_nodes,
                                                   tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    VirtualEnvironmentInst = VirtualEnvironment(
        deploy_virtual_struct, net_struct, adapter_virtual, pxe_bridge_virtual,
        daisy_server, work_dir, storage_dir, scenario)
    VirtualEnvironmentInst.delete_old_environment()
    VirtualEnvironmentInst.delete_daisy_server.assert_called_once_with()
    VirtualEnvironmentInst.delete_networks.assert_called_once_with()
    VirtualEnvironmentInst.delete_nodes.assert_called_once_with()
    tmpdir.remove()


@mock.patch.object(environment.DaisyServer, 'post_deploy')
@mock.patch.object(environment.DaisyServer, 'check_openstack_installation')
@mock.patch.object(environment.DaisyServer, 'check_os_installation')
@mock.patch.object(environment.DaisyServer, 'install_virtual_nodes')
@mock.patch.object(environment.DaisyServer, 'prepare_host_and_pxe')
@mock.patch.object(environment.DaisyServer, 'copy_new_deploy_config')
@mock.patch.object(environment.DaisyServer, 'prepare_cluster')
@mock.patch.object(environment.VirtualEnvironment, '_post_deploy')
@mock.patch.object(environment.VirtualEnvironment, 'reboot_nodes')
@mock.patch.object(environment.VirtualEnvironment, 'create_nodes')
def test_deploy_VirtualEnvironment(mock_create_nodes, mock_reboot_nodes,
                                   mock__post_deploy, mock_prepare_cluster,
                                   mock_copy_new_deploy_config, mock_prepare_host_and_pxe,
                                   mock_install_virtual_nodes, mock_check_os_installation,
                                   mock_check_openstack_installation, mock_post_deploy,
                                   tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    remote_dir = '/home/daisy'
    bin_file = os.path.join(tmpdir.dirname, tmpdir.basename, 'opnfv.bin')
    deploy_file_name = 'final_deploy.yml'
    net_file_name = 'network_virtual1.yml'
    deploy_file = os.path.join(get_conf_file_dir(), 'deploy_virtual1.yml')
    net_file = os.path.join(get_conf_file_dir(), 'network_virtual1.yml')
    VirtualEnvironmentInst = VirtualEnvironment(
        deploy_virtual_struct, net_struct, adapter_virtual, pxe_bridge_virtual,
        daisy_server, work_dir, storage_dir, scenario)
    VirtualEnvironmentInst.server = DaisyServer(
        daisy_server['name'],
        daisy_server['address'],
        daisy_server['password'],
        remote_dir,
        bin_file,
        adapter,
        scenario,
        deploy_file_name,
        net_file_name)
    VirtualEnvironmentInst.deploy(deploy_file, net_file)
    mock_create_nodes.assert_called_once()
    assert mock_reboot_nodes.call_count == 2
    mock__post_deploy.assert_called_once()
    mock_prepare_cluster.assert_called_once()
    mock_copy_new_deploy_config.assert_called_once()
    mock_prepare_host_and_pxe.assert_called_once()
    mock_install_virtual_nodes.assert_called_once()
    mock_check_os_installation.assert_called_once()
    mock_check_openstack_installation.assert_called_once()
    mock_post_deploy.assert_called_once()
    tmpdir.remove()


@pytest.mark.parametrize('status', [
    (True),
    (False)])
@mock.patch('deploy.environment.commands.getstatusoutput')
@mock.patch('deploy.environment.LW')
@mock.patch('deploy.environment.LI')
def test__post_deploy_VirtualEnvironment(mock_LI, mock_LW,
                                         mock_getstatusoutput, status, tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    mock_getstatusoutput.return_value = (status, 'success')
    VirtualEnvironmentInst = VirtualEnvironment(
        deploy_virtual_struct, net_struct, adapter_virtual, pxe_bridge_virtual,
        daisy_server, work_dir, storage_dir, scenario)
    VirtualEnvironmentInst._post_deploy()
    VirtualEnvironmentInst._daisy_server_net = 'daisy1'
    VirtualEnvironmentInst._daisy_os_net = 'daisy2'
    assert environment.commands.getstatusoutput.call_count == 4
    if status:
        mock_LW.assert_called()
    else:
        mock_LI.assert_called()
    tmpdir.remove()
