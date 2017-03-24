##############################################################################
# Copyright (c) 2017 ZTE Coreporation and others.
# feng.xiaowei@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from collections import defaultdict
import re

from keystoneauth1 import loading
from keystoneauth1 import session


class Keystoneauth(object):
    def __init__(self, openrc=None):
        self.openrc = openrc if openrc else '/etc/kolla/admin-openrc.sh'

    @property
    def session(self):
        auth = self._get_auth()
        return session.Session(auth=auth)

    def _get_auth(self):
        loader = loading.get_plugin_loader('password')
        creds = self._parse_credentials(self._parse_openrc())
        return loader.load_from_options(**creds)

    def _parse_openrc(self):

        def parse_line(creds, line):
            var = line.rstrip('"\n').replace('export ', '').split("=")
            # The two next lines should be modified as soon as rc_file
            # conforms with common rules. Be aware that it could induce
            # issues if value starts with '
            key = re.sub(r'^["\' ]*|[ \'"]*$', '', var[0])
            value = re.sub(r'^["\' ]*|[ \'"]*$', '', "".join(var[1:]))
            creds[key] = value
            return creds

        with open(self.openrc, "r") as f:
            return reduce(parse_line, f.readlines(), defaultdict(dict))

    @staticmethod
    def _parse_credentials(raws):
        maps = {
            'OS_USERNAME': 'username',
            'OS_PASSWORD': 'password',
            'OS_AUTH_URL': 'auth_url',
            'OS_TENANT_NAME': 'tenant_name',
            'OS_USER_DOMAIN_NAME': 'user_domain_name',
            'OS_PROJECT_DOMAIN_NAME': 'project_domain_name',
            'OS_PROJECT_NAME': 'project_name',
            'OS_ENDPOINT_TYPE': 'endpoint_type',
            'OS_REGION_NAME': 'region_name'
        }

        def parse_credential(creds, kv):
            (cred_k, cred_v) = kv
            creds[maps[cred_k]] = cred_v
            return creds

        return reduce(parse_credential,
                      [(k, v) for (k, v) in raws.iteritems() if k in maps],
                      defaultdict(dict))


class ClientBase(Keystoneauth):
    def __init__(self, klass, version, openrc):
        super(ClientBase, self).__init__(openrc)
        self.client = klass(version, session=self.session)
