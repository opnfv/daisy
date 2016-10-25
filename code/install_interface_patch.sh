#!/bin/bash

mkdir -p /home/kolla_install/docker
if [ ! -e "/home/kolla_install/docker/registry-2.0.3.tgz" ];then
    cp registry-2.0.3.tgz /home/kolla_install/docker
fi
if [ ! -e "/home/kolla_install/docker/registry-server.tar" ];then
    cp registry-server.tar /home/kolla_install/docker
fi
 
cp CentOS-7-x86_64-Minimal-1511.iso /var/lib/daisy/kolla

