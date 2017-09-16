##############################################################################
# Copyright (c) 2017 ZTE Corp and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import os

import yaml
import pytest

from deploy.config.schemas import (
    deploy_schema_validate
)


@pytest.fixture(scope="session")
def conf_file_dir(data_root):
    return os.path.join(data_root, 'lab_conf')


@pytest.mark.parametrize('deploy_file_name, tell_result', [
    ('deploy_virtual1.yml', lambda x: x == []),
    ('deploy_virtual_error.yml', lambda x: x != []),
    ('deploy_baremetal.yml', lambda x: x == [])])
def test_deploy_schema_validate(conf_file_dir, deploy_file_name, tell_result):
    data = yaml.safe_load(open(os.path.join(conf_file_dir, deploy_file_name), 'r'))
    errors = deploy_schema_validate(data)
    assert tell_result(errors)
