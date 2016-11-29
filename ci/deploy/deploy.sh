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
# exit 0

##########TODO after test##########
DHA=$WORKSPACE/$1
NETWORK=$WORKSPACE/$2
deploy_path=$WORKSPACE/deploy
create_qcow2_path=$WORKSPACE/tools
net_daisy1=$WORKSPACE/templates/virtual_environment/networks/daisy1.xml
net_daisy2=$WORKSPACE/templates/virtual_environment/networks/daisy2.xml
pod_daisy=$WORKSPACE/templates/virtual_environment/vms/daisy.xml
pod_all_in_one=$WORKSPACE/templates/virtual_environment/vms/all_in_one.xml

parameter_from_deploy=`python $WORKSPACE/deploy/get_para_from_deploy.py --dha $DHA`

daisyserver_size=`echo $parameter_from_deploy | cut -d " " -f 1`
controller_node_size=`echo $parameter_from_deploy | cut -d " " -f 2`
compute_node_size=`echo $parameter_from_deploy | cut -d " " -f 3`
daisy_passwd=`echo $parameter_from_deploy | cut -d " " -f 4`
daisy_ip=`echo $parameter_from_deploy | cut -d " " -f 5`
daisy_gateway=`echo $parameter_from_deploy | cut -d " " -f 6`

echo "=======create daisy node================"
$create_qcow2_path/daisy-img-modify.sh -c $create_qcow2_path/centos-img-modify.sh -a $daisy_ip -g $daisy_gateway -s $daisyserver_size
#qemu-img resize centos7.qcow2 100G
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
ssh $daisy_ip -o UserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no "$WORKSPACE/opnfv.bin  install"
rc=$?
if [ $rc -ne 0 ]; then
    echo "daisy install failed"
    exit 1
else
    echo "daisy install successfully"
fi

echo "====== add relate config of kolla==========="
ssh $daisy_ip -o UserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no "mkdir -p /etc/kolla/config/nova"
ssh $daisy_ip -o UserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no "echo -e "[libvirt]\nvirt_type=qemu" > /etc/kolla/config/nova/nova-compute.conf"

echo "===prepare cluster and pxe==="
ssh $daisy_ip -o UserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no "python $WORKSPACE/deploy/tempest.py --dha $DHA --network $NETWORK --cluster "yes""

echo "=====create all-in-one node======"
qemu-img create -f qcow2 $WORKSPACE/../qemu/vms/all_in_one.qcow2 200G
virsh net-define $net_daisy2
virsh net-autostart daisy2
virsh net-start daisy2
virsh define $pod_all_in_one
virsh start all_in_one
sleep 20

echo "======prepare host and pxe==========="
ssh $daisy_ip -o UserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no "python $WORKSPACE/deploy/tempest.py  --dha $DHA --network $NETWORK --host "yes""

echo "======daisy deploy os and openstack==========="
virsh destroy all_in_one
virsh start all_in_one

echo "===========check install progress==========="
ssh $daisy_ip -o UserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no "$WORKSPACE/deploy/check_os_progress.sh"
virsh reboot all_in_one
ssh $daisy_ip -o UserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no "$WORKSPACE/deploy/check_openstack_progress.sh"

exit 0
