#!/bin/bash
##############################################################################
# Copyright (c) 2016 ZTE Coreporation and others.
# hu.zhijiang@zte.com.cn
# sun.jing22@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
output_dir = "$1"
_BUILD_DIR=`pwd`
echo "#########################################################"
echo "               systemctl info:                   "
echo "#########################################################"
echo "###Uname:"
uname
echo "###Hostname: $(hostname)"

maxcount=3
cnt=0
rc=1
while [ $cnt -lt $maxcount ] && [ $rc -ne 0 ]
do
    cnt=$[cnt + 1]
    echo -e "\n\n\n*** Starting build attempt # $cnt"

    mkdir daisy-dir
    cd daisy-dir
    git clone https://git.openstack.org/openstack/daisycloud-core
    cp $_BUILD_DIR/code/makefile_patch.sh daisycloud-core/tools/setup
    cp $_BUILD_DIR/code/install_interface_patch.sh daisycloud-core/tools/setup
    cd daisycloud-core/make
    make allrpm

    echo "######################################################"
    echo "          done              "
    echo "######################################################"
    rc=$?
    if [ $rc -ne 0 ]; then
        echo "### Build failed with rc $rc ###"
    else
        echo "### Build successful at attempt # $cnt"
    fi
done
cd ..
mv target/el7/noarch/installdaisy_el7_noarch.bin output_dir
exit $rc
