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
imageversion="170621131826"
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
    if [ $# -eq 3 ]; then  md5_url=$3; else md5_url=""; fi

    pushd $file_path  >/dev/null

    count=0
    MAX_DOWNLOAD_TIMES=2
    while [ $count -lt ${MAX_DOWNLOAD_TIMES} ]; do
        count=$[count + 1]

        if [ ! -f ${file_name} ]; then
            echo "Begin to download ${file_name}"
            wget --progress=dot:giga ${file_url}
        fi

        if [ ! -z ${md5_url} ]; then
            rm -f $(basename ${md5_url})
            wget ${md5_url}
            md5sum -c $(basename ${md5_url})
            if [ $? -ne 0 ]; then
                echo "MD5 check failed !"
                rm -f ${file_name}
            else
                echo "MD5 check succeeded !"
                count=${MAX_DOWNLOAD_TIMES}
            fi
        else
            wget --spider $file_url -o tmp_filesize
            origin_size=$(cat tmp_filesize | grep Length | awk '{print $2}')
            rm tmp_filesize
            local_size=$(stat -c %s ${file_path}/${file_name} | tr -d '\n')
            if [ ${local_size} -ne ${origin_size} ]; then
                echo "The local ${file_name} is incomplete."
                rm -f ${file_name}
            else
                echo "File ${file_path}/${file_name} is ok."
                count=${MAX_DOWNLOAD_TIMES}
            fi
        fi
    done

    popd > /dev/null
}

if [ ! -d $CACHE_PATH ]; then mkdir -p $CACHE_PATH ; fi
check_or_download_file $CACHE_PATH $isourl
check_or_download_file $CACHE_PATH $imageserver/${imagename} ${imageserver}/${imagename}.md5
check_or_download_file $CACHE_PATH "http://daisycloud.org/static/files/registry-server.tar"
check_or_download_file $CACHE_PATH ${cirros_url}

cp $CACHE_PATH/${isoname} $TOOLS_PATH/setup/bin_temp/
cp $CACHE_PATH/$imagename $TOOLS_PATH/setup/bin_temp/
cp $CACHE_PATH/registry-server.tar $TOOLS_PATH/setup/bin_temp/
cp $CACHE_PATH/${cirros_filename} $TOOLS_PATH/setup/bin_temp/

cp $TOOLS_PATH/setup/install_interface_patch.sh $TOOLS_PATH/setup/bin_temp/
chmod +x $TOOLS_PATH/setup/bin_temp/install_interface_patch.sh
