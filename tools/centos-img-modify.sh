#!/bin/bash

##############################################################################
# Copyright (c) 2016 ZTE Coreporation and others.
# 
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

echo "r00tme" | passwd --stdin root
sed -i 's/#PermitRootLogin yes/PermitRootLogin yes/g' /etc/ssh/sshd_config

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

echo daisy > /etc/hostname

