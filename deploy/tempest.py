from oslo_config import cfg
import sys
from daisyclient.v1 import client as daisy_client
import get_conf
import traceback
import time
import subprocess

daisy_version = 1.0
daisy_endpoint = "http://127.0.0.1:19292"
client = daisy_client.Client(version=daisy_version, endpoint=daisy_endpoint)
iso_path = "/var/lib/daisy/kolla/CentOS-7-x86_64-DVD-1511.iso"
deployment_interface = "virbr2"
cluster_name = "clustertest"

_CLI_OPTS = [
    cfg.StrOpt('dha',
               help='The dha file path'),
    cfg.StrOpt('network',
               help='The network file path'),
]


# ------------------------------------------------------------------------------------------
def parse(conf, args):
    conf.register_cli_opts(_CLI_OPTS)
    conf(args=args)


def print_bar(msg):
    print ("--------------------------------------------")
    print (msg)
    print ("--------------------------------------------")


def foo():
    try:
        print("get config...")
        conf = cfg.ConfigOpts()
        parse(conf, sys.argv[1:])
        host_interface_map, hosts_name, network_map, vip = \
            get_conf.config(conf['dha'], conf['network'])
        print("add cluster...")
        cluster_meta = {'name': cluster_name, 'description': ''}
        clusters_info = client.clusters.add(**cluster_meta)
        cluster_id = clusters_info.id
        print("cluster_id=%s." % cluster_id)
        print("update network...")
        update_network(cluster_id, network_map)   
        print("build pxe...")
        build_pxe(cluster_id)
        print("create host...")
        create_host(cluster_id)
        print("discover host...")
        discover_host(hosts_name)
        print("update hosts interface...")
        hosts_info = get_hosts()
        add_hosts_interface(cluster_id, hosts_info, host_interface_map, vip)
    except Exception:
        print("Deploy failed!!!.%s." % traceback.format_exc())
    else:
        print_bar("Everything is done!")


def build_pxe(cluster_id):
    cluster_meta =  {'cluster_id': cluster_id, 'deployment_interface': deployment_interface}   
    client.install.install(**cluster_meta)
   
 
def create_host(cluster_id):
    command = 'virsh define /home/daisy/test.xml'
    subprocess.call(command,
                    shell=True,
                    stdout=open('/dev/null', 'w'),
                    stderr=subprocess.STDOUT) 
    command = 'virsh start DaisyNode'
    subprocess.call(command,
                    shell=True,
                    stdout=open('/dev/null', 'w'),
                    stderr=subprocess.STDOUT)


def discover_host(hosts_name):
    while True:
        hosts_info = get_hosts()
        if len(hosts_info) == len(hosts_name):
            print('discover hosts success!')
            break
        else:
            time.sleep(10)


def update_network(cluster_id, network_map):
    network_meta = {'filters': {'cluster_id': cluster_id}}
    network_info_gernerator = client.networks.list(**network_meta)
    network_info_list = [net for net in network_info_gernerator]
    for net in network_info_list:
        network_id = net.id
        network_name = net.name
        if network_map.get(network_name):
            network_meta = network_map[network_name]
            client.networks.update(network_id, **network_meta)


def get_hosts():
    hosts_list_generator = client.hosts.list()
    hosts_list = [host for host in hosts_list_generator]
    hosts_info = []
    for host in hosts_list:
        host_info = client.hosts.get(host.id)
        hosts_info.append(host_info)
    return hosts_info


def add_hosts_interface(cluster_id, hosts_info, host_interface_map,
                        vip):
    for host in hosts_info:
        host = host.to_dict()
        host['cluster'] = cluster_id
        for interface in host['interfaces']:
            interface_name = interface['name']
            interface['assigned_networks'] = \
                host_interface_map[interface_name]
        host['os_version'] = iso_path
        client.hosts.update(host['id'], **host)
        print("update role...")
        add_host_role(cluster_id, host['id'], host['name'], vip)


def add_host_role(cluster_id, host_id, host_name, vip):
    role_meta = {'filters': {'cluster_id': cluster_id}}
    role_list_generator = client.roles.list(**role_meta)
    role_list = [role for role in role_list_generator]
    lb_role_id = [role.id for role in role_list if
                  role.name == "CONTROLLER_LB"][0]
    computer_role_id = [role.id for role in role_list if
                        role.name == "COMPUTER"][0]
    role_lb_update_meta = {'nodes': [host_id],
                           'cluster_id': cluster_id, 'vip': vip}
    client.roles.update(lb_role_id, **role_lb_update_meta)
    role_computer_update_meta = {'nodes': [host_id],
                                 'cluster_id': cluster_id}
    client.roles.update(computer_role_id, **role_computer_update_meta)


if __name__ == "__main__":
    foo()
