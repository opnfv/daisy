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

imagebranch="ocata"
imageversion="170420124331"
imageserver="http://120.24.17.215"
imagename="kolla-image-$imagebranch-$imageversion.tgz"

isoname="CentOS-7-x86_64-Minimal-1611.iso"
isourl="http://buildlogs.centos.org/rolling/7/isos/x86_64/${isoname}"

cirros_server="http://download.cirros-cloud.net"
cirros_ver="0.3.5"
cirros_filename="cirros-${cirros_ver}-x86_64-disk.img"
cirros_url=${cirros_server}/${cirros_ver}/${cirros_filename}

function check_or_download_file()
{
    file_path=$1
    file_url=$2
    file_name=$(basename $2)

    if [ ! -f ${file_path}/${file_name} ]; then
        wget -P ${file_path} --progress=dot:giga ${file_url}
    else
        wget --spider $file_url -o tmp_filesize
        origin_size=$(cat tmp_filesize | grep Length | awk '{print $2}')
        rm tmp_filesize
        local_size=$(stat -c %s ${file_path}/${file_name} | tr -d '\n')

        if [ $local_size -ne $origin_size ]; then
            echo "The local file is incomplete. Re-download it."
            rm -f $file_path/$file_name
            wget -P ${file_path} --progress=dot:giga ${file_url}
        else
            echo "File $file_path/$file_name is ok."
        fi
    fi
}

if [ ! -d $CACHE_PATH ]; then mkdir -p $CACHE_PATH ; fi
check_or_download_file $CACHE_PATH $isourl
check_or_download_file $CACHE_PATH $imageserver/$imagename
check_or_download_file $CACHE_PATH "http://daisycloud.org/static/files/registry-server.tar"
check_or_download_file $CACHE_PATH ${cirros_url}

cp $CACHE_PATH/${isoname} $TOOLS_PATH/setup/bin_temp/
cp $CACHE_PATH/$imagename $TOOLS_PATH/setup/bin_temp/
cp $CACHE_PATH/registry-server.tar $TOOLS_PATH/setup/bin_temp/
cp $CACHE_PATH/${cirros_filename} $TOOLS_PATH/setup/bin_temp/

cp $TOOLS_PATH/setup/install_interface_patch.sh $TOOLS_PATH/setup/bin_temp/
chmod +x $TOOLS_PATH/setup/bin_temp/install_interface_patch.sh
