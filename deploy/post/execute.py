##############################################################################
# Copyright (c) 2017 ZTE Coreporation and others.
# feng.xiaowei@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import neutron


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


def main():
    neutron.Neutron().list_networks()
    neutron.Neutron().create_network(*(_config_admin_external_network()))

if __name__ == '__main__':
    main()
