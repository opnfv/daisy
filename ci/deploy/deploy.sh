#!/bin/bash
##############################################################################
# Copyright (c) 2016 ZTE Coreporation and others.
# hu.zhijiang@zte.com.cn
# lu.yao135@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
#daisy host discover
######exit before finish test#######
exit 0

##########TODO after test##########
DHA=$1
NETWORK=$2
tempest_path=$WORKSPACE/deploy

echo "====== clean && install daisy==========="
.$WORKSPACE/opnfv.bin  clean
rc=$?
if [ $rc -ne 0 ]; then
    echo "daisy clean failed"
    exit 1
else
    echo "daisy clean successfully"
fi
.$WORKSPACE/opnfv.bin  install
rc=$?
if [ $rc -ne 0 ]; then
    echo "daisy install failed"
    exit 1
else
    echo "daisy install successfully"
fi

source ~/daisyrc_admin

echo "======prepare install openstack==========="
python $tempest_path/tempest.py --dha $DHA --network $NETWORK

echo "======daisy install kolla(openstack)==========="
cluster_id=`daisy cluster-list | awk -F "|" '{print $2}' | sed -n '4p'`
daisy install $cluster_id
echo "check installing process..."
var=1
while [ $var -eq 1 ]; do
    echo "loop for judge openstack installing  progress..."
    openstack_install_active=`daisy host-list --cluster-id $cluster_id | awk -F "|" '{print $12}' | grep -c "active" `
    openstack_install_failed=`daisy host-list --cluster-id $cluster_id | awk -F "|" '{print $12}' | grep -c "install-failed" `
    if [ $openstack_install_active -eq 1 ]; then
        echo "openstack installing successful ..."
        break
    elif [ $openstack_install_failed -gt 0 ]; then
        echo "openstack installing have failed..."
        tail -n 200 /var/log/daisy/kolla_$cluster_id*
        exit 1
    else
        echo " openstack in installing , please waiting ..."
    fi
done
exit 0
