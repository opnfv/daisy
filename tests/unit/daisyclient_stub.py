##############################################################################
# Copyright (c) 2017 ZTE Corp and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################


class StubTestInstall():
    def __init__(self):
        pass

    def install(self, **cluster_meta):
        self.cluster_meta = cluster_meta


class StubTestHost():
    def __init__(self, id, name, cluster_id, interfaces):
        self.id = id
        self.name = name
        self.cluster_id = cluster_id
        self.interfaces = interfaces
        self.metadata = None

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'cluster_id': self.cluster_id,
                'interfaces': self.interfaces}


class StubTestHosts():
    def __init__(self):
        self.hosts = []

    def add(self, host):
        self.hosts.append(host)

    def get(self, id):
        for host in self.hosts:
            if host.id == id:
                return host
        return None

    def list(self):
        return self.hosts

    def update(self, host_id, **metadata):
        for host in self.hosts:
            if host.id == host_id:
                host.metadata = metadata


class StubTestCluster():
    def __init__(self, id, name):
        self.id = id
        self.name = name


class StubTestClusters():
    def __init__(self):
        self.clusters = []

    def add(self, cluster):
        self.clusters.append(cluster)

    def get(self, id):
        for cluster in self.clusters:
            if cluster.id == id:
                return cluster.name
        return None

    def list(self):
        return self.clusters


class StubTestNet():
    def __init__(self, id, name, cluster_id, **metadata):
        self.id = id
        self.name = name
        self.cluster_id = cluster_id
        self.metadata = metadata


class StubTestNetworks():
    def __init__(self):
        self.networks = []

    def add(self, net):
        self.networks.append(net)

    def list(self, **filter):
        networks = []
        if filter:
            filter_item = filter.get('filters')
            for net in self.networks:
                cluster_id_is_match = False
                if filter_item.get('cluster_id'):
                    if filter_item.get('cluster_id') == net.cluster_id:
                        cluster_id_is_match = True
                else:
                    cluster_id_is_match = True
                if cluster_id_is_match is True:
                    networks.append(net)
        return networks

    def update(self, network_id, **network_meta):
        for net in self.networks:
            if net.id == network_id:
                net.metadata = network_meta


class StubTestRole():
    def __init__(self, id, name, cluster_id):
        self.id = id
        self.name = name
        self.cluster_id = cluster_id
        self.metadata = None


class StubTestRoles():
    def __init__(self):
        self.roles = []

    def add(self, role):
        self.roles.append(role)

    def list(self, **filter):
        roles = []
        if filter:
            filter_item = filter.get('filters')
            for role in self.roles:
                cluster_id_is_match = False
                if filter_item.get('cluster_id'):
                    if filter_item.get('cluster_id') == role.cluster_id:
                        cluster_id_is_match = True
                else:
                    cluster_id_is_match = True
                if cluster_id_is_match is True:
                    roles.append(role)
        return roles

    def update(self, role_id, **meta):
        for role in self.roles:
            if role.id == role_id:
                role.metadata = meta


class StubTestDisks():
    def __init__(self):
        self.disks = []

    def service_disk_add(self, **metadata):
        self.disks.append(metadata)


class StubTestClient():
    def __init__(self):
        self.install = StubTestInstall()
        self.hosts = StubTestHosts()
        self.networks = StubTestNetworks()
        self.clusters = StubTestClusters()
        self.roles = StubTestRoles()
        self.disk_array = StubTestDisks()
