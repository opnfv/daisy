import novaclient.client

import keystoneauth


class Nova(keystoneauth.Keystoneauth):
    def __init__(self, version='2', openrc=None):
        super(Nova, self).__init__(openrc)
        self.client = novaclient.client.Client(version, session=self.session)
        self.flavors = self.client.flavors

    def create_flavor(self, name, ram, vcpus, disk, is_public=True):
        flavor = self.flavors.create(name, ram, vcpus, disk,
                                     is_public=is_public)
        return flavor.id

    def get_flavor_by_name(self, name):
        for flavor in self.list_flavors():
            if flavor.name == name:
                return flavor.id

        return None

    def list_flavors(self):
        return self.flavors.list(detailed=True)
