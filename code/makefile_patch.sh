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
TOOLS_PATH=$1
CACHE_PATH=/home/cache
if [ ! -d $CACHE_PATH ]; then mkdir -p $CACHE_PATH ; fi
if [ ! -f $CACHE_PATH/CentOS-7-x86_64-Minimal-1511.iso ]; then
    wget -P $CACHE_PATH "http://ftp.osuosl.org/pub/centos/7/isos/x86_64/CentOS-7-x86_64-Minimal-1511.iso"
fi
if [ ! -f $CACHE_PATH/registry-mitaka-latest.tgz ]; then
    wget -P $CACHE_PATH "http://daisycloud.org/static/files/registry-mitaka-latest.tgz"
fi
if [ ! -f $CACHE_PATH/registry-server.tar ]; then
    wget -P $CACHE_PATH "http://daisycloud.org/static/files/registry-server.tar"
fi
cp $CACHE_PATH/CentOS-7-x86_64-Minimal-1511.iso $TOOLS_PATH/setup/bin_temp/
cp $CACHE_PATH/registry-mitaka-latest.tgz $TOOLS_PATH/setup/bin_temp/
cp $CACHE_PATH/registry-server.tar $TOOLS_PATH/setup/bin_temp/
cp $TOOLS_PATH/setup/install_interface_patch.sh $TOOLS_PATH/setup/bin_temp/
chmod +x $TOOLS_PATH/setup/bin_temp/install_interface_patch.sh
