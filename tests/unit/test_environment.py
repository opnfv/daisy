import os
import copy
import mock
import yaml
from deepdiff import DeepDiff

from deploy.utils import WORKSPACE
from deploy import environment
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


def test_create_daisy_server_image_DaisyEnvironmentBase(tmpdir, monkeypatch):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    os.makedirs(work_dir, 0755)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    os.makedirs(storage_dir, 0755)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    DaisyEnvBaseInst = DaisyEnvironmentBase(
        deploy_struct, net_struct, adapter, pxe_bridge,
        daisy_server, work_dir, storage_dir, scenario)

    def create_server_image_sucess(cmd):
        os.makedirs(os.path.join(work_dir, 'daisy'))
        with open(os.path.join(work_dir, 'daisy', 'centos7.qcow2'), 'w') as f:
            f.write('image-data')
        return 0
    monkeypatch.setattr(environment, 'run_shell', create_server_image_sucess)
    DaisyEnvBaseInst.create_daisy_server_image()
    assert os.path.isfile(DaisyEnvBaseInst.daisy_server_info['image'])
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


@mock.patch('deploy.environment.ipmi_reboot_node')
def test_reboot_nodes_BareMetalEnvironment(mock_ipmi_reboot_node, tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    mock_ipmi_reboot_node.return_value = True
    BareMetalEnvironmentInst = BareMetalEnvironment(
        deploy_struct, net_struct, adapter, pxe_bridge,
        daisy_server, work_dir, storage_dir, scenario)
    BareMetalEnvironmentInst.reboot_nodes()
    assert environment.ipmi_reboot_node.call_count == 5
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


@mock.patch('deploy.environment.create_virtual_network')
def test_create_daisy_server_network_VirtualEnvironment(mock_create_virtual_network, tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    mock_create_virtual_network.return_value = pxe_bridge_virtual
    VirtualEnvironmentInst = VirtualEnvironment(
        deploy_virtual_struct, net_struct, adapter_virtual, pxe_bridge_virtual,
        daisy_server, work_dir, storage_dir, scenario)
    VirtualEnvironmentInst.create_daisy_server_network()
    environment.create_virtual_network.assert_called_once_with(VMDEPLOY_DAISY_SERVER_NET)
    assert VirtualEnvironmentInst._daisy_server_net == pxe_bridge_virtual
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


@mock.patch('deploy.environment.create_vm')
@mock.patch('deploy.environment.create_virtual_disk')
def test_create_virtual_node_VirtualEnvironment(mock_create_virtual_disk,
                                                mock_create_vm,
                                                tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    VirtualEnvironmentInst = VirtualEnvironment(
        deploy_virtual_struct, net_struct, adapter_virtual, pxe_bridge_virtual,
        daisy_server, work_dir, storage_dir, scenario)
    VirtualEnvironmentInst.create_virtual_node(deploy_virtual_struct['hosts'][0])
    environment.create_virtual_disk.call_count == 2
    name = deploy_virtual_struct['hosts'][0]['name']
    template = deploy_virtual_struct['hosts'][0]['template']
    files = [os.path.join(storage_dir, name + '.qcow2'), os.path.join(storage_dir, name + '_data.qcow2')]
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


@mock.patch('deploy.environment.delete_virtual_network')
def test_delete_networks_VirtualEnvironment(mock_delete_virtual_network, tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    VirtualEnvironmentInst = VirtualEnvironment(
        deploy_virtual_struct, net_struct, adapter_virtual, pxe_bridge_virtual,
        daisy_server, work_dir, storage_dir, scenario)
    VirtualEnvironmentInst.delete_networks()
    assert environment.delete_virtual_network.call_count == 3


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


@mock.patch('deploy.environment.commands.getstatusoutput')
def test_post_deploy_VirtualEnvironment(mock_getstatusoutput, tmpdir):
    work_dir = os.path.join(tmpdir.dirname, tmpdir.basename, work_dir_name)
    storage_dir = os.path.join(tmpdir.dirname, tmpdir.basename, storage_dir_name)
    daisy_server = copy.deepcopy(daisy_server_info)
    daisy_server['image'] = os.path.join(storage_dir, daisy_server['image'])
    mock_getstatusoutput.return_value = (0, 'sucess')
    VirtualEnvironmentInst = VirtualEnvironment(
        deploy_virtual_struct, net_struct, adapter_virtual, pxe_bridge_virtual,
        daisy_server, work_dir, storage_dir, scenario)
    VirtualEnvironmentInst._post_deploy()
    VirtualEnvironmentInst._daisy_server_net = 'daisy1'
    VirtualEnvironmentInst._daisy_os_net = 'daisy2'
    assert environment.commands.getstatusoutput.call_count == 4
