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
        networks = self.client.list_networks()['networks']
        for network in networks:
            print network

    def create_admin_ext_net(self):
        pass
