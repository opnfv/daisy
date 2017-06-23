#!/bin/bash
##############################################################################
# Copyright (c) 2016 ZTE Corporation and others.
# hu.zhijiang@zte.com.cn
# lu.yao135@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
imagebranch="ocata"
imageversion="170621131826"
imageserver="http://120.24.17.215"
imagedir="/var/lib/daisy/versionfile/kolla"
imagename="kolla-image-$imagebranch-$imageversion.tgz"
mkdir -p $imagedir
if [ ! -e "$imagedir/$imagename" ];then
    cp $imagename $imagedir
fi
if [ ! -e "$imagedir/registry-server.tar" ];then
    cp registry-server.tar $imagedir
fi
cp CentOS*.iso /var/lib/daisy/kolla

mkdir -p /var/lib/daisy/images/
cp cirros*.img /var/lib/daisy/images/
