import os

import glanceclient

import keystoneauth


class Glance(keystoneauth.Keystoneauth):
    def __init__(self, version='2', openrc=None):
        super(Glance, self).__init__(openrc)
        self.client = glanceclient.Client(version, session=self.session)
        self.controller = self.client.images

    def create(self, name, path,
               disk_format="qcow2",
               container_format="bare",
               visibility="public"):
        if not os.path.isfile(path):
            raise Exception('Error: file {} not exist'.format(path))
        image = self.controller.create(name=name,
                                       visibility=visibility,
                                       disk_format=disk_format,
                                       container_format=container_format)
        id = image.id
        with open(path) as data:
            self.controller.upload(id, data)
        return id

    def get_by_name(self, name):
        for image in self.list():
            if image.name == name:
                return image.id

        return None

    def list(self):
        return self.controller.list()
