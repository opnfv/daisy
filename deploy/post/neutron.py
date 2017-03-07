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

    def create_network(self, name, body):
        if not self.is_network_exist(name):
            return self._create_network(name, body)
        else:
            print('admin_ext [{}] already exist'.format(name))
            return None

    def create_subnet(self, body=None):
        if not self.is_subnet_exist(body):
            return self._create_subnet(body)
        else:
            print ('subnet [{}] already exist'.format(body))
            return None
        
    def list_networks(self):
        return self.client.list_networks()['networks']

    def list_subnets(self):
        return self.client.list_subnets()['subnets']

    def is_network_exist(self, name):
        return [] != filter(lambda n: n['name'] == name, self.list_networks())

    def is_subnet_exist(self, body):
        print 'body: {}'.format(body)

        def same_subnet(n):
            print 'n: {}'.format(n)
            for item in ['name', 'network_id']:
                if n[item] != body['subnets'][0][item]:
                    return False
            return True

        return [] != filter(lambda n: same_subnet(n), self.list_subnets())

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