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
