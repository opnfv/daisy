#!/bin/bash
##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
# hu.zhijiang@zte.com.cn
# lu.yao135@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
mkdir -p /home/kolla_install/docker
if [ ! -e "/home/kolla_install/docker/registry-2.0.3.tgz" ];then
    cp registry-2.0.3.tgz /home/kolla_install/docker
fi
if [ ! -e "/home/kolla_install/docker/registry-server.tar" ];then
    cp registry-server.tar /home/kolla_install/docker
fi
cp CentOS-7-x86_64-Minimal-1511.iso /var/lib/daisy/kolla

