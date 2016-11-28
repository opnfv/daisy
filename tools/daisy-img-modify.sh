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

set -e
set -x

die() {
    echo "error: $1" >&2
    exit 1
}

test $(id -u) -eq 0 || die "You need be root to run this script"

if [ $# -eq 1 ]; then
    cmd=$1
else
    cmd=$(cd "$(dirname "$0")"; pwd)/centos-img-modify.sh
fi

test -x $cmd

mountdir="/mnt/daisy/centos"
workdir=${WORKDIR:-"/tmp/workdir/daisy"}
host=${HOST:-"cloud.centos.org"}
filename=CentOS-7-x86_64-GenericCloud-1608.qcow2
image_xz_path="centos/7/images/$filename.xz"
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
        rm -f $filename.xz
        wget -nc --progress=dot:giga $image_xz_url
        xz -d -k CentOS-7-x86_64-GenericCloud-1608.qcow2.xz
        grep $filename$ sha256sum.txt | sha256sum -c
    fi

    for i in $(seq 0 9); do
        [ -a /dev/loop$i ] || mknod -m 660 /dev/loop$i b 7 $i
    done

    qemu-img convert $filename $raw_imgfile
    cd -
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
    cp $cmd $mountdir/$(basename $cmd)
}

# modify image running a script using in a chrooted environment
modify() {
    chroot $mountdir /$(basename $cmd)

    umount $mountdir

    if dmsetup table | grep $loopdevice; then
       dmsetup clear $loopdevice || true
    fi

    qemu-img convert -c -o compat=0.10 -O qcow2 $raw_imgfile $imgfile
}

# cleanup (umount) the image
cleanup() {
    mount | grep $mountdir && umount $mountdir
    if [ -f $raw_imgfile ]; then
        kpartx -dv $raw_imgfile || true
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
    setup
    modify

    trap - EXIT SIGTERM
    cleanup

    echo "the modified image is found here: $imgfile"
}

main

