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

from deploy.post.keystoneauth import *


@pytest.mark.parametrize('openrc, expected', [
    ('/etc/kolla/admin-openrc.sh', '/etc/kolla/admin-openrc.sh'),
    (None, '/etc/kolla/admin-openrc.sh')])
def test_create_Keystoneauth_instance_(openrc, expected):
    KeystoneClient = Keystoneauth(openrc)
    assert KeystoneClient.openrc == expected