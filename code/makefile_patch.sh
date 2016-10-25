#!/bin/bash
TOOLS_PATH=$1
CACHE_PATH=/home/cache
if [ ! -d $CACHE_PATH ]; then mkdir $CACHE_PATH ; fi
if [ ! -f $CACHE_PATH/CentOS-7-x86_64-Minimal-1511.iso ]; then
    wget -P $CACHE_PATH "http://mirrors.163.com/centos/7/isos/x86_64/CentOS-7-x86_64-Minimal-1511.iso"
fi
if [ ! -f $CACHE_PATH/registry-2.0.3.tgz ]; then
    wget -P $CACHE_PATH "ftp://openuser:123@120.76.145.166/registry-2.0.3.tgz"
fi
if [ ! -f $CACHE_PATH/registry-server.tar ]; then
    wget -P $CACHE_PATH "ftp://openuser:123@120.76.145.166/registry-server.tar"
fi
cp $CACHE_PATH/CentOS-7-x86_64-Minimal-1511.iso $TOOLS_PATH/setup/bin_temp/
cp $CACHE_PATH/registry-2.0.3.tgz $TOOLS_PATH/setup/bin_temp/
cp $CACHE_PATH/registry-server.tar $TOOLS_PATH/setup/bin_temp/
cp $TOOLS_PATH/setup/install_interface_patch.sh $TOOLS_PATH/setup/bin_temp/
chmod +x $TOOLS_PATH/setup/bin_temp/install_interface_patch.sh
