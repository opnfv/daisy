##############################################################################
# Copyright (c) 2017 ZTE Coreporation and others.
# feng.xiaowei@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
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
