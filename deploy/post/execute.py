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
import neutron
import nova


def _config_admin_external_network():
    name = 'admin_external'
    body = {
        'network': {
            'name': name,
            'admin_state_up': True,
            'shared': False,
            'provider:network_type': 'flat',
            'provider:physical_network': 'physnet1',
            'router:external': True
        }
    }

    return name, body


def _config_admin_external_subnet(nid):
    return {
        'subnets': [
            {
                'name': 'admin_external_subnet',
                'cidr': '172.10.101.0/24',
                'ip_version': 4,
                'network_id': nid,
                'gateway_ip': '172.10.101.1',
                'allocation_pools': [{
                    'start': '172.10.101.2',
                    'end': '172.10.101.12'
                }],
                'enable_dhcp': False
            }
        ]
    }


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
    url = 'http://download.cirros-cloud.net'
    version = '0.3.5'
    name = 'cirros-{}-x86_64-disk.img'.format(version)
    img = os.path.join("/var/lib/daisy/images", name)
    if not os.path.isfile(img):
        cmd = "wget %(url)s/%(version)s/%(name)s -O %(path)s" % {
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
    neutronclient = neutron.Neutron()
    nid = neutronclient.create_network(*(_config_admin_external_network()))
    neutronclient.create_subnet(_config_admin_external_subnet(nid))
    _create_flavor_m1_micro()
    _create_image_TestVM()


if __name__ == '__main__':
    main()
