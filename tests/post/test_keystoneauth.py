##############################################################################
# Copyright (c) 2017 ZTE Corp and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import os

import pytest

from deploy.post.keystoneauth import Keystoneauth


@pytest.mark.parametrize('openrc, expected', [
    ('/etc/kolla/admin-openrc.sh', '/etc/kolla/admin-openrc.sh'),
    (None, '/etc/kolla/admin-openrc.sh')])
def test_create_Keystoneauth_instance(openrc, expected):
    KeystoneClient = Keystoneauth(openrc)
    assert KeystoneClient.openrc == expected


@pytest.mark.parametrize('raws, expected', [
    (
        {
            'OS_USERNAME': 'admin',
            'OS_PASSWORD': 'keystone',
            'OS_AUTH_URL': 'http://10.20.11.11:35357/v3',
            'OS_TENANT_NAME': 'admin',
            'OS_USER_DOMAIN_NAME': 'Default',
            'OS_PROJECT_DOMAIN_NAME': 'Default',
            'OS_PROJECT_NAME': 'admin',
            'OS_INTERFACE': 'internal',
            'OS_IDENTITY_API_VERSION': 'region_name'
        },
        {
            'username': 'admin',
            'password': 'keystone',
            'auth_url': 'http://10.20.11.11:35357/v3',
            'tenant_name': 'admin',
            'user_domain_name': 'Default',
            'project_domain_name': 'Default',
            'project_name': 'admin'
        }),
    (
        {
            'OS_USERNAME': 'admin',
            'OS_PASSWORD': 'keystone',
            'OS_AUTH_URL': 'http://10.20.11.11:35357/v3',
            'OS_TENANT_NAME': 'admin',
            'OS_USER_DOMAIN_NAME': 'Default',
            'OS_PROJECT_DOMAIN_NAME': 'Default',
            'OS_PROJECT_NAME': 'admin',
            'OS_ENDPOINT_TYPE': 'Default',
            'OS_REGION_NAME': 'Default'
        },
        {
            'username': 'admin',
            'password': 'keystone',
            'auth_url': 'http://10.20.11.11:35357/v3',
            'tenant_name': 'admin',
            'user_domain_name': 'Default',
            'project_domain_name': 'Default',
            'project_name': 'admin',
            'endpoint_type': 'Default',
            'region_name': 'Default'
        }
    )])
def test__parse_credentials_in_Keystoneauth(raws, expected):
    assert Keystoneauth._parse_credentials(raws) == expected


@pytest.fixture(scope="session")
def openrc_conf_file_dir(data_root):
    return os.path.join(data_root, 'openrc_conf')


def test_session(openrc_conf_file_dir):
    openrc = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    KeystoneClient = Keystoneauth(openrc)
    assert KeystoneClient.session
