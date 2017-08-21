#!/bin/bash

##############################################################################
# Copyright (c) 2016 ZTE Coreporation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

IMAGE_NAME=TestVM

# Sanitize language settings to avoid commands bailing out
# with "unsupported locale setting" errors.
unset LANG
unset LANGUAGE
LC_ALL=C
export LC_ALL
for i in curl openstack; do
    if [[ ! $(type ${i} 2>/dev/null) ]]; then
        if [ "${i}" == 'curl' ]; then
            echo "Please install ${i} before proceeding"
        else
            echo "Please install python-${i}client before proceeding"
        fi
        exit
    fi
done

# Move to top level directory
REAL_PATH=$(python -c "import os,sys;print os.path.realpath('$0')")
cd "$(dirname "$REAL_PATH")/.."

# Test for credentials set
if [[ "${OS_USERNAME}" == "" ]]; then
    echo "No Keystone credentials specified.  Try running source openrc"
    exit
fi

echo "Configuring tenant network."

openstack network create --provider-network-type vxlan demo-net
openstack subnet create --subnet-range 10.0.0.0/24 --network demo-net \
    --gateway 10.0.0.1 --dns-nameserver 8.8.8.8 demo-subnet
DEMO_NET_ID=$(openstack network list | awk '/ demo-net / {print $2}')

openstack router create demo-router
openstack router add subnet demo-router demo-subnet
openstack router set --external-gateway admin_external demo-router

openstack floating ip create admin_external
DEMO_FIP=$(openstack floating ip list | awk '/ None / {print $4}')

openstack server create --image ${IMAGE_NAME} --flavor m1.micro \
    --nic net-id=${DEMO_NET_ID} demo1

# Wait for guest ready to accept FIP, seems need it.
sleep 10

openstack server add floating ip demo1 ${DEMO_FIP}

echo "Now you can test ping ${DEMO_FIP} from external network"
