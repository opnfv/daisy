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

rpm_build_dir=/opt/daisy4nfv
rpm_output_dir=$rpm_build_dir/build_output
tmp_rpm_build_dir=/root/daisy4nfv
tmp_rpm_output_dir=$tmp_rpm_build_dir/build_output

cp -r $rpm_build_dir $tmp_rpm_build_dir
cd $tmp_rpm_build_dir

echo "#########################################################"
echo "               systemctl info:                   "
echo "#########################################################"
echo "###Uname: $(uname)"
echo "###Hostname: $(hostname)"

maxcount=3
cnt=0
rc=1
while [ $cnt -lt $maxcount ] && [ $rc -ne 0 ]
do
    cnt=$[cnt + 1]
    echo -e "\n\n\n*** Starting build attempt # $cnt"

    git clone https://git.openstack.org/openstack/daisycloud-core
    cp $tmp_rpm_build_dir/code/makefile_patch.sh daisycloud-core/tools/setup
    cp $tmp_rpm_build_dir/code/install_interface_patch.sh daisycloud-core/tools/setup
    cd daisycloud-core/make
    make allrpm
    rc=$?

    echo "######################################################"
    echo "          done              "
    echo "######################################################"
    if [ $rc -ne 0 ]; then
        echo "### Build failed with rc $rc ###"
    else
        echo "### Build successfully at attempt # $cnt"
    fi
done
cd ..
cp target/el7/noarch/installdaisy_el7_noarch.bin $rpm_output_dir
exit $rc
