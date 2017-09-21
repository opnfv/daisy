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
import mock

from deploy.post.glance import Glance
from deploy.post import glance


@pytest.fixture(scope="module")
def openrc_conf_file_dir(data_root):
    return os.path.join(data_root, 'openrc_conf')


def test_create_Glance_instance(openrc_conf_file_dir):
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    glance = Glance(openrc=openrc_file)
    assert glance.controller == glance.client.images


@mock.patch('glanceclient.v2.images.Controller.create')
@mock.patch('glanceclient.v2.images.Controller.upload')
def test_create_in_Glance(mock_upload, mock_create,
                          openrc_conf_file_dir, tmpdir):
    class Test_image():
        def __init__(self, id):
            self.id = id
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    file_name = 'test_image.qcow2'
    file_path = os.path.join(tmpdir.dirname, tmpdir.basename, file_name)
    with open(file_path, 'w') as f:
        f.write('test_data')
    id = 0x1234
    glance = Glance(openrc=openrc_file)
    mock_create.return_value = Test_image(id)
    ret = glance.create(file_name, file_path)
    assert ret == id
    tmpdir.remove()


@mock.patch.object(glance.Glance, 'list')
def test_get_by_name_in_Glance(mock_list, openrc_conf_file_dir):
    class Test_image():
        def __init__(self, name):
            self.name = name
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    image_inst1 = Test_image('test_image1.qcow2')
    image_inst2 = Test_image('test_image2.qcow2')
    images_list = [image_inst1, image_inst2]
    mock_list.return_value = images_list
    glance = Glance(openrc=openrc_file)
    ret = glance.get_by_name('test_image1.qcow2')
    assert ret == image_inst1


@mock.patch('glanceclient.v2.images.Controller.list')
def test_list_in_Glance(mock_list, openrc_conf_file_dir):
    openrc_file = os.path.join(openrc_conf_file_dir, 'admin-openrc.sh')
    glance_list = ['test1']
    mock_list.return_value = glance_list
    glance = Glance(openrc=openrc_file)
    ret = glance.list()
    assert ret == glance_list
