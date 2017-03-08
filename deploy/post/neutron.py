##############################################################################
# Copyright (c) 2017 ZTE Coreporation and others.
# feng.xiaowei@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from neutronclient.neutron import client as neutronclient

import keystoneauth


class Neutron(object):
    def __init__(self, api_v='2', openrc=None):
        session = keystoneauth.Keystoneauth(openrc).session
        self.client = neutronclient.Client(api_v, session=session)

    def list_networks(self):
        return self.client.list_networks()['networks']

    def create_network(self, name, body):
        if not self.is_network_exist(name):
            self._create_network(name, body)
        else:
            print('admin_ext [{}] already exist'.format(name))
        pass

    def is_network_exist(self, name):
        return [] != filter(lambda n: n['name'] == name, self.list_networks())

    def _create_network(self, name, body):
        try:
            nid = self.client.create_network(body=body)['network']['id']
            print('_create_admin_ext_net [{}] with id: {}'.format(name, nid))
            return nid
        except Exception, e:
            print('_create_admin_ext_net [{}] fail with: {}'.format(name, e))
            return None
