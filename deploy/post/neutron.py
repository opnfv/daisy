##############################################################################
# Copyright (c) 2017 ZTE Coreporation and others.
# feng.xiaowei@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from neutronclient.neutron import client

from deploy.common import query
import keystoneauth


class Neutron(keystoneauth.ClientBase):
    def __init__(self, version='2', openrc=None):
        super(Neutron, self).__init__(client.Client, version, openrc)

    def create_network(self, name, body):
        if not self.get_network_by_name(name):
            return self._create_network(name, body)
        else:
            print('admin_ext [{}] already exist'.format(name))
            return None

    def create_subnet(self, body=None):
        if not self.get_subnet_by_name(body):
            return self._create_subnet(body)
        else:
            print ('subnet [{}] already exist'.format(body))
            return None

    def list_networks(self):
        return self.client.list_networks()['networks']

    def list_subnets(self):
        return self.client.list_subnets()['subnets']

    def get_network_by_name(self, name):
        return query.find(lambda nw: nw['name'] == name, self.list_networks())

    def get_subnet_by_name(self, body):
        def _same_subnet(this, that):
            for item in ['name', 'network_id']:
                if this[item] != that[item]:
                    return False
            return True

        return query.find(lambda n: _same_subnet(n, body['subnets'][0]),
                          self.list_subnets())

    def _create_network(self, name, body):
        try:
            nid = self.client.create_network(body=body)['network']['id']
            print('_create_admin_ext_net [{}] with id: {}'.format(name, nid))
            return nid
        except Exception, e:
            print('_create_admin_ext_net [{}] fail with: {}'.format(name, e))
            return None

    def _create_subnet(self, body):
        print('_create_subnet with body: {}'.format(body))
        try:
            snid = self.client.create_subnet(body)['subnets'][0]['id']
            print('_create_subnet success with id={}'.format(snid))
            return snid
        except Exception, e:
            print('_create_subnet fail with: {}'.format(e))
            return None

