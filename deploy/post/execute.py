##############################################################################
# Copyright (c) 2017 ZTE Coreporation and others.
# feng.xiaowei@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import os

import neutron
import glance


def _config_admin_external_network():
    name = 'admin_external'
    body = {
        'network': {
            'name': name,
            'admin_state_up': True,
            'shared': True,
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


def _create_image_TestVM():
    glanceclient = glance.Glance()
    image = 'TestVM1'
    if not glanceclient.get_by_name(image):
        url = 'http://download.cirros-cloud.net'
        version = '0.3.5'
        name = 'cirros-{}-x86_64-disk.img'.format(version)
        path = os.path.join(os.path.abspath(os.path.dirname(__file__)), name)
        if not os.path.isfile(path):
            cmd = "wget %(url)s/%(version)s/%(name)s %(path)s" % {
                'url': url,
                'version': version,
                'name': name,
                'path': path}
            os.system(cmd)
            pass
        try:
            glanceclient.create(image, path)
        except Exception as error:
            print ('create_TestVM failed: {}'.format(str(error)))
    else:
        print ('Use existing TestVM image')


def main():
    neutronclient = neutron.Neutron()
    nid = neutronclient.create_network(*(_config_admin_external_network()))
    neutronclient.create_subnet(_config_admin_external_subnet(nid))
    _create_image_TestVM()

if __name__ == '__main__':
    main()
