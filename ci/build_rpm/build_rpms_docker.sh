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
tmp_rpm_build_dir=/root/daisy4nfv
rpm_build_dir=/opt/daisy4nfv
tmp_rpm_output_dir=$tmp_rpm_build_dir/build_output
rpm_output_dir=$rpm_build_dir/build_output
cp -r $rpm_build_dir $tmp_rpm_build_dir

# Build daisy rpm packages
cd $tmp_rpm_build_dir/
#make clean
./ci/build_rpm/daisy_rpm_build.sh build_output


# Move daisy bin file from tmp_output_dir to output_dir
mv $tmp_rpm_output_dir/installdaisy_el7_noarch.bin $rpm_output_dir
