import yaml

from deploy.common import query


class NetworkConfig(object):
    type2name = {
        'EXTERNAL': 'ext',
        'MANAGEMENT': 'man',
        'STORAGE': 'stor',
        'PUBLICAPI': 'pub',
        'TENANT': 'tenant',
    }

    def __init__(self, network_file):
        self._parsers = {
            'network-config-metadata': self._parse_metadata,
            'networks': self._parse_networks,
            'interfaces': self._parse_interfaces
        }

        self._file = network_file
        self._get_config()
        self._parse()

    def _get_config(self):
        self.config = yaml.safe_load(file(self._file))

    def _get_network(self, name):
        return query.find(lambda item: item['name'] == name,
                          self.config['networks'])

    def _parse(self):
        for conf_k, conf_v in self.config.iteritems():
            self._parsers.get(conf_k,
                              lambda x: setattr(self, conf_k, conf_v))(conf_v)

    def _parse_metadata(self, metadatas):
        for meta_k, meta_v in metadatas.iteritems():
            setattr(self, meta_k, meta_v)

    def _parse_networks(self, networks):
        for network in networks:
            name = network['name']
            self._setattr(name, '', network)
            for network_k, network_v in network.iteritems():
                self._setattr(name, network_k, network_v)

    def _parse_interfaces(self, interfaces):
        for interface in interfaces:
            self._setattr(interface['name'],
                          'iterface',
                          interface['interface'])

    def _setattr(self, network_type, field, value):
        prefix = self.type2name[network_type]
        name = '{}_{}'.format(prefix, field) if field else prefix
        setattr(self, name, value)

    @property
    def external_network(self):
        return self._get_network('EXTERNAL')

    @property
    def external_name(self):
        return self.external_network['network_name']
