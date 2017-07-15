##############################################################################
# Copyright (c) 2017 ZTE Coreporation and others.
# feng.xiaowei@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import os

import glance
import argparse
import yaml
import neutron
import nova
from deploy.config.network import NetworkConfig


def _config_kolla_admin_openrc(kolla_config_path):
    with open('%s/globals.yml' % kolla_config_path, 'r') as f:
        kolla_config = yaml.safe_load(f.read())
    if kolla_config.get('opendaylight_leader_ip_address'):
        sdn_controller_ip = kolla_config.get('opendaylight_leader_ip_address')
        openrc_file = file('%s/admin-openrc.sh' % kolla_config_path, 'a')
        sdn_ctl_ip = 'export SDN_CONTROLLER_IP=' + sdn_controller_ip + '\n'
        openrc_file.write(sdn_ctl_ip)
        openrc_file.close()


def _config_external_network(ext_name, physnet):
    body = {
        'network': {
            'name': ext_name,
            'admin_state_up': True,
            'shared': False,
            'provider:network_type': 'flat',
            'provider:physical_network': physnet,
            'router:external': True
        }
    }

    return body


def _config_external_subnet(ext_id, network_conf):
    return {
        'subnets': [
            {
                'name': '{}_subnet'.format(network_conf.ext_network_name),
                'cidr': network_conf.ext_cidr,
                'ip_version': 4,
                'network_id': ext_id,
                'gateway_ip': network_conf.ext_gateway,
                'allocation_pools': network_conf.ext_ip_ranges,
                'enable_dhcp': False
            }
        ]
    }


def _create_external_network(network_file):
    network_conf = NetworkConfig(network_file=network_file)
    ext_name = network_conf.ext_network_name
    physnet = network_conf.ext_mapping if hasattr(network_conf, 'ext_mapping') else 'physnet1'
    neutronclient = neutron.Neutron()
    ext_id = neutronclient.create_network(ext_name,
                                          _config_external_network(ext_name, physnet))
    if ext_id:
        neutronclient.create_subnet(_config_external_subnet(ext_id, network_conf))


def _create_flavor_m1_micro():
    name = 'm1.micro'
    novaclient = nova.Nova()
    if not novaclient.get_flavor_by_name(name):
        try:
            return novaclient.create_flavor(name, ram=64, vcpus=1, disk=0)
        except Exception as error:
            print ('_create_flavor_m1_micro failed: {}'.format(str(error)))
    else:
        print ('Use existing m1.micro flavor')


def _prepare_cirros():
    url = 'https://download.cirros-cloud.net'
    version = '0.3.5'
    name = 'cirros-{}-x86_64-disk.img'.format(version)
    img = os.path.join("/var/lib/daisy/images", name)
    imgmd5 = "/var/lib/daisy/images/cirros.md5"
    if not os.path.isfile(img):
        cmd = "curl -sSL %(url)s/%(version)s/%(name)s -o %(path)s" % {
            'url': url,
            'version': version,
            'name': name,
            'path': img}
        try:
            print ('Downloading cirros: {}'.format(cmd))
            os.system(cmd)
        except Exception as error:
            print ('Download cirros failed: {}'.format(str(error)))
            img = None

        cmd = "curl -sSL %(url)s/%(version)s/MD5SUMS -o %(md5path)s" % {
            'url': url,
            'version': version,
            'md5path': imgmd5}
        try:
            print ('Downloading MD5SUM for cirros: {}'.format(cmd))
            os.system(cmd)
        except Exception as error:
            print ('Download cirros MD5SUM failed: {}'.format(str(error)))
            img = None

        cmd = "cat  %(md5path)s | grep %(name)s | md5sum -c" % {
            'md5path': imgmd5,
            'name': name}
        try:
            print ('md5sum check cirros: {}'.format(cmd))
            os.system(cmd)
        except Exception as error:
            print ('md5sum check cirros failed: {}'.format(str(error)))
            img = None

    return img


def _create_image_TestVM():
    glanceclient = glance.Glance()
    image = 'TestVM'
    if not glanceclient.get_by_name(image):
        img = _prepare_cirros()
        if img:
            try:
                glanceclient.create(image, img)
            except Exception as error:
                print ('Create image failed: {}'.format(str(error)))
    else:
        print ('Use existing TestVM image')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-nw', '--network-file',
                        type=str,
                        required=True,
                        help='network configuration file')
    args = parser.parse_args()
    _create_external_network(args.network_file)
    _create_flavor_m1_micro()
    _create_image_TestVM()
    _config_kolla_admin_openrc('/etc/kolla/')


if __name__ == '__main__':
    main()
