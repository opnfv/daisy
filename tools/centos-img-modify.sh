#!/bin/bash

##############################################################################
# Copyright (c) 2016 ZTE Coreporation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

set -x

echo "r00tme" | passwd --stdin root

sed -i 's/^SELINUX=enforcing/SELINUX=permissive/g' /etc/selinux/config

sed -i 's/#PermitRootLogin yes/PermitRootLogin yes/g' /etc/ssh/sshd_config
sed -i 's/#UseDNS yes/UseDNS no/g' /etc/ssh/sshd_config

if [ -z $ipaddr ] || [ -z $gwaddr ]; then
    cat << EOF > /etc/sysconfig/network-scripts/ifcfg-ens3
DEVICE="ens3"
BOOTPROTO="dhcp"
ONBOOT="yes"
TYPE="Ethernet"
USERCTL="yes"
PEERDNS="yes"
IPV6INIT="no"
PERSISTENT_DHCLIENT="1"
EOF

    cat << EOF > /etc/resolv.conf
nameserver 8.8.8.8
EOF

else
    cat << EOF > /etc/sysconfig/network-scripts/ifcfg-ens3
DEVICE="ens3"
NAME="ens3"
BOOTPROTO="static"
ONBOOT="yes"
TYPE="Ethernet"
IPADDR="${ipaddr}"
NETMASK="255.255.255.0"
GATEWAY="${gwaddr}"
IPV6INIT="no"
EOF

    cat << EOF > /etc/resolv.conf
nameserver ${gwaddr}
nameserver 8.8.8.8
EOF

fi

host_name=daisy
echo ${host_name} > /etc/hostname
sed -i "/^127.0.0.1/s/ localhost / ${host_name} localhost /g" /etc/hosts

# required by daisycloud-core daisy/api/backends/osinstall/pxe/install.py
# This can be removed when upstream fix it.
mkdir -p -m 700 /root/.ssh
touch /root/.ssh/known_hosts
chmod 600 /root/.ssh/known_hosts

# Allow console access via pwd
cat << EOF > /etc/cloud/cloud.cfg.d/default.cfg
disable_root: False
ssh_pwauth: True
EOF

cd /etc
if [ ! -z $localtime_file ] && [ -f $localtime_file ]; then
    ln -s -f $localtime_file /etc/localtime
fi

# https://review.openstack.org/#/c/568180/
test -e /etc/yum/vars/contentdir || echo centos > /etc/yum/vars/contentdir
