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
DHA=/home/daisy/$1
NETWORK=/home/daisy/$2
deploy_path=/home/daisy/deploy
create_qcow2_path=$WORKSPACE/tools
net_daisy1=$WORKSPACE/deploy/templates/virtual_environment/networks/daisy1.xml
net_daisy2=$WORKSPACE/deploy/templates/virtual_environment/networks/daisy2.xml
pod_daisy=$WORKSPACE/deploy/templates/virtual_environment/vms/daisy.xml
pod_all_in_one=$WORKSPACE/deploy/templates/virtual_environment/vms/all_in_one.xml

daisy_ip=10.20.11.2
daisy_gateway=10.20.11.1
daisy_passwd=r00tme

echo "=======create daisy node================"
$create_qcow2_path/daisy-img-modify.sh $create_qcow2_path/centos-img-modify.sh $daisy_ip $daisy_gateway
virsh net-define $net_daisy1
virsh net-autostart daisy1
virsh net-start daisy1
virsh define $pod_daisy
virsh start daisy 
sleep 20

echo "====== install daisy==========="
$deploy_path/trustme.sh $daisy_ip $daisy_passwd
scp -r $WORKSPACE root@$daisy_ip:/home

ssh $daisy_ip -o UserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no "mkdir -p /home/daisy_install"
scp $WORKSPACE/deploy/daisy.conf root@$daisy_ip:/home/daisy_install
ssh $daisy_ip -o UserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no "/home/daisy/opnfv.bin  install"
rc=$?
if [ $rc -ne 0 ]; then
    echo "daisy install failed"
    exit 1
else
    echo "daisy install successfully"
fi

echo "===prepare cluster and pxe==="
ssh $daisy_ip -o UserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no "python /home/daisy/deploy/tempest.py --dha $DHA --network $NETWORK --cluster "yes""

echo "=====create all-in-one node======"
qemu-img create -f qcow2 /home/qemu/vms/all_in_one.qcow2 200G
virsh net-define $net_daisy2
virsh net-autostart daisy2
virsh net-start daisy2
virsh define $pod_all_in_one
virsh start all_in_one
sleep 20

echo "======prepare host and pxe==========="
ssh $daisy_ip -o UserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no "python /home/daisy/deploy/tempest.py  --dha $DHA --network $NETWORK --host "yes""

echo "======daisy deploy os and openstack==========="
virsh destroy all_in_one
virsh start all_in_one

echo "===========check install progress==========="
ssh $daisy_ip -o UserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no "/home/daisy/deploy/check_os_progress.sh"
virsh reboot all_in_one
ssh $daisy_ip -o UserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no "/home/daisy/deploy/check_openstack_progress.sh"

exit 0
