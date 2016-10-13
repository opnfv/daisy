#!/bin/bash

tmp_rpm_build_dir=/root/daisy4nfv
rpm_build_dir=/opt/daisy4nfv
tmp_rpm_output_dir=$tmp_rpm_build_dir/build_output
rpm_output_dir=$rpm_build_dir/build_output
cp -r $rpm_build_dir $tmp_rpm_build_dir

# Build daisy rpm packages
cd $tmp_rpm_build_dir/
make clean
./ci/build_rpm/daisy_rpm_build.sh build_output


# Move Kernel and Qemu Rpm builds from tmp_output_dir to output_dir
mv $tmp_rpm_output_dir/installdaisy_el7_noarch.bin $rpm_output_dir
