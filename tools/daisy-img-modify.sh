#!/bin/bash

##############################################################################
# Copyright (c) 2016 ZTE Coreporation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# This script refers to the yardstick project.

usage()
{
    cat << EOF
USAGE: `basename $0` [-c sub-Command] [-a IP Address] [-g Gateway IP address] [-s image Size in GB]

OPTIONS:
  -c sub-command to modify the content
  -a IP address for the sub-command to set in the image
  -g gateway IP address for the sub-command to set in the image
  -s image size of gigabytes. If it is absent, the image size will not be changed.

EXAMPLE:
    sudo `basename $0` -c centos-img-modify.sh -a 10.20.11.2 -g 10.20.11.1 -s 100
EOF
}

while getopts "c:a:g:s:h" OPTION
do
    case $OPTION in
        c)
            cmd=${OPTARG}
            if [ ! -x $cmd ]; then
                echo "The $cmd does not exist or is not executable."
                usage
                exit 1
            fi
            ;;
        a)
            ipaddr=${OPTARG}
            ;;
        g)
            gwaddr=${OPTARG}
            ;;
        s)
            img_size=${OPTARG}
            ;;
        h)
            usage
            exit 0
            ;;
        *)
            echo "${OPTION} is not a valid argument"
            usage
            exit 0
            ;;
    esac
done


set -e
set -x

die() {
    echo "error: $1" >&2
    exit 1
}

test $(id -u) -eq 0 || die "You need be root to run this script"

cmd=${cmd:-$(cd "$(dirname "$0")"; pwd)/centos-img-modify.sh}
test -x $cmd

if [[ -n $ipaddr ]]; then
    export ipaddr=$ipaddr
fi

if [[ -n $gwaddr ]]; then
    export gwaddr=$gwaddr
fi

mountdir="/mnt/daisy/centos"
workdir=${WORKDIR:-"/tmp/workdir/daisy"}
host=${HOST:-"cloud.centos.org"}
filename=CentOS-7-x86_64-GenericCloud-1608.qcow2
image_xz_path="centos/7/images/${filename}.xz"
image_xz_url=${IMAGE_XZ_URL:-"http://${host}/${image_xz_path}"}
sha256sum_path="centos/7/images/sha256sum.txt"
sha256sum_url=${SHA256SUM_URL:-"http://${host}/${sha256sum_path}"}
imgfile="${workdir}/centos7.qcow2"
raw_imgfile="${workdir}/centos7.raw"

# download and checksum base image, conditionally if local copy is outdated
download() {
    test -d $workdir || mkdir -p $workdir
    cd $workdir
    rm -f sha256sum.txt
    wget $sha256sum_url

    test -e $filename  &&  grep $filename$ sha256sum.txt | sha256sum -c
    if [ $? -ne 0 ]; then
        rm -f $filename
        rm -f ${filename}.xz
        wget -nc --progress=dot:giga $image_xz_url
        xz -d -k ${filename}.xz
        grep $filename$ sha256sum.txt | sha256sum -c
    fi

    for i in $(seq 0 9); do
        [[ -e /dev/loop$i ]] || mknod -m 660 /dev/loop$i b 7 $i
    done

    qemu-img convert $filename $raw_imgfile
    cd -
}

# install utils
install_utils()
{
    which kpartx ||
    if [ $? -ne 0 ]; then
        yum install -y kpartx
    fi

    which growpart ||
    if [ $? -ne 0 ]; then
        yum install -y cloud-utils-growpart
    fi

    which xfs_growfs ||
    if [ $? -ne 0 ]; then
        yum install -y xfsprogs
    fi
}

# Eliminate exceptions
eliminate()
{
    if [ ! -z $loopdevice ]; then
        if mount | grep "/dev/mapper/$loopdevice"; then
            umount /dev/mapper/$loopdevice || true
        fi

        if dmsetup ls | grep $loopdevice; then
            dmsetup remove $loopdevice || true
        fi
    fi
    return 0
}

# resize image
resize() {
    install_utils

    # resize the image
    qemu-img resize $raw_imgfile ${img_size}G
    qemu-img info $raw_imgfile
    loopdevice=$(kpartx -l $raw_imgfile | head -1 | cut -f1 -d ' ')
    kpartx -av $raw_imgfile
    sleep 2
    dmsetup ls
    fdisk -l /dev/${loopdevice:0:5} || true
    growpart /dev/${loopdevice:0:5} 1
    dmsetup clear $loopdevice
    kpartx -dv $raw_imgfile || eliminate
}

# mount image
setup() {
    mkdir -p $mountdir

    loopdevice=$(kpartx -l $raw_imgfile | head -1 | cut -f1 -d ' ')

    kpartx -av $raw_imgfile
    sleep 2
    dmsetup ls
    fdisk -l /dev/${loopdevice:0:5} || true
    mount /dev/mapper/$loopdevice $mountdir
    mount -t proc none ${mountdir}/proc

    if [[ -n $img_size ]]; then
        xfs_growfs /dev/mapper/$loopdevice
    fi

    chroot $mountdir df -h
    cp $cmd $mountdir/$(basename $cmd)
}

# modify image running a script using in a chrooted environment
modify() {
    chroot $mountdir /$(basename $cmd)
    rm -f $mountdir/$(basename $cmd)

    umount $mountdir/proc
    umount $mountdir

    if dmsetup table | grep $loopdevice; then
       dmsetup clear $loopdevice || true
    fi

    qemu-img convert -c -o compat=0.10 -O qcow2 $raw_imgfile $imgfile
}

# cleanup (umount) the image
cleanup() {
    mount | grep $mountdir/proc && umount $mountdir/proc
    mount | grep $mountdir && umount $mountdir
    if [ -f $raw_imgfile ]; then
        kpartx -dv $raw_imgfile || eliminate
    fi
    rm -f $raw_imgfile
    rm -rf $mountdir
}

exitcode=""
error_trap()
{
    local rc=$?

    set +e

    if [ -z "$exitcode" ]; then
        exitcode=$rc
    fi

    dmesg -T | tail -50

    cleanup

    echo "Image build failed with $exitcode"

    exit $exitcode
}

main() {
    cleanup

    trap "error_trap" EXIT SIGTERM

    download
    if [[ -n $img_size ]]; then
        echo img_size=$img_size
        resize
    fi
    setup
    modify

    trap - EXIT SIGTERM
    cleanup

    echo "the modified image is found here: $imgfile"
}

main

