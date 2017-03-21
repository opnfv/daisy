##############################################################################
# Copyright (c) 2017 ZTE Coreporation and others.
# feng.xiaowei@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import yaml

from deploy.common import query


class NetworkConfig(object):
    def __init__(self, network_file):
        self._file = network_file
        self._get_config()

    def _get_config(self):
        self.config = yaml.safe_load(file(self._file))

    def _get_network(self, name):
        return query.find(lambda item: item['name'] == name,
                          self.config['networks'])

    @property
    def external_network(self):
        return self._get_network('EXTERNAL')
