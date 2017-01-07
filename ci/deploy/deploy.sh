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
WORKDIR=/tmp/workdir
DHA=$WORKSPACE/$1
NETWORK=$WORKSPACE/$2
deploy_path=$WORKSPACE/deploy
create_qcow2_path=$WORKSPACE/tools
net_daisy1=$WORKSPACE/templates/virtual_environment/networks/daisy.xml
net_daisy2=$WORKSPACE/templates/virtual_environment/networks/os-all_in_one.xml
pod_daisy=$WORKSPACE/templates/virtual_environment/vms/daisy.xml
pod_all_in_one=$WORKSPACE/templates/virtual_environment/vms/all_in_one.xml

parameter_from_deploy=`python $WORKSPACE/deploy/get_para_from_deploy.py --dha $DHA`

daisyserver_size=`echo $parameter_from_deploy | cut -d " " -f 1`
controller_node_size=`echo $parameter_from_deploy | cut -d " " -f 2`
compute_node_size=`echo $parameter_from_deploy | cut -d " " -f 3`
daisy_passwd=`echo $parameter_from_deploy | cut -d " " -f 4`
daisy_ip=`echo $parameter_from_deploy | cut -d " " -f 5`
daisy_gateway=`echo $parameter_from_deploy | cut -d " " -f 6`

function execute_on_jumpserver
{
    local jumpserver_ip=$1
    local cmd=$2
    ssh $jumpserver_ip -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no $cmd
}

function create_node
{
    local net_template=$1
    local net_name=$2
    local vms_template=$3
    local vms_name=$4
    virsh net-define $net_template
    virsh net-autostart $net_name
    virsh net-start $net_name
    virsh define $vms_template
    virsh start $vms_name
}

#update key = value config option in an conf or ini file
function update_config
{
    local file=$1
    local key=$2
    local value=$3

    [ ! -e $file ] && return

    #echo update key $key to value $value in file $file ...
    local exist=`grep "^[[:space:]]*[^#]" $file | grep -c "$key[[:space:]]*=[[:space:]]*.*"`
    #action：If a line is a comment, the beginning of the first character must be a #!!!
    local comment=`grep -c "^[[:space:]]*#[[:space:]]*$key[[:space:]]*=[[:space:]]*.*"  $file`

    if [[ $value == "#" ]];then
        if [ $exist -gt 0 ];then
            sed  -i "/^[^#]/s/$key[[:space:]]*=/\#$key=/" $file
        fi
        return
    fi

    if [ $exist -gt 0 ];then
        #if there have been a effective configuration line did not comment, update value directly
        sed  -i "/^[^#]/s#$key[[:space:]]*=.*#$key=$value#" $file

    elif [ $comment -gt 0 ];then
        #if there is a configuration line has been commented out, then remove the comments, update the value
        sed -i "s@^[[:space:]]*#[[:space:]]*$key[[:space:]]*=[[:space:]]*.*@$key=$value@" $file
    else
        #add effective configuration line at the end
        echo "$key=$value" >> $file
    fi
}

function clean_up
{
    local vm_name=$1
    local network_name=$2
    virsh destroy $vm_name
    virsh undefine $vm_name
    virsh net-destroy $network_name
    virsh net-undefine $network_name
}

echo "=====clean up all node and network======"
clean_up all_in_one daisy2
clean_up daisy daisy1
if [ -f $WORKDIR/daisy ]; then
    rm -rf $WORKDIR
fi

echo "=======create daisy node================"
$create_qcow2_path/daisy-img-modify.sh -c $create_qcow2_path/centos-img-modify.sh -a $daisy_ip -g $daisy_gateway -s $daisyserver_size
create_node $net_daisy1 daisy1 $pod_daisy daisy
sleep 20

echo "====== install daisy==========="
$deploy_path/trustme.sh $daisy_ip $daisy_passwd
scp -r $WORKSPACE root@$daisy_ip:/home
ssh root@$daisy_ip "touch /root/.ssh/know_hosts"
execute_on_jumpserver $daisy_ip "mkdir -p /home/daisy_install"
update_config $WORKSPACE/deploy/daisy.conf daisy_management_ip $daisy_ip
scp $WORKSPACE/deploy/daisy.conf root@$daisy_ip:/home/daisy_install
execute_on_jumpserver $daisy_ip "$WORKSPACE/opnfv.bin  install"
rc=$?
if [ $rc -ne 0 ]; then
    echo "daisy install failed"
    exit 1
else
    echo "daisy install successfully"
fi

echo "====== add relate config of kolla==========="
execute_on_jumpserver $daisy_ip "mkdir -p /etc/kolla/config/nova"
execute_on_jumpserver $daisy_ip "echo -e '[libvirt]\nvirt_type=qemu' > /etc/kolla/config/nova/nova-compute.conf"

echo "===prepare cluster and pxe==="
execute_on_jumpserver $daisy_ip "python $WORKSPACE/deploy/tempest.py --dha $DHA --network $NETWORK --cluster "yes""

echo "=====create all-in-one node======"
qemu-img create -f qcow2 $WORKSPACE/../qemu/vms/all_in_one.qcow2 200G
create_node $net_daisy2 daisy2 $pod_all_in_one all_in_one
sleep 20

echo "======prepare host and pxe==========="
execute_on_jumpserver $daisy_ip "python $WORKSPACE/deploy/tempest.py  --dha $DHA --network $NETWORK --host "yes""

echo "======daisy deploy os and openstack==========="
virsh destroy all_in_one
virsh start all_in_one

echo "===========check install progress==========="
execute_on_jumpserver $daisy_ip "systemctl restart daisy-api"
execute_on_jumpserver $daisy_ip "systemctl restart daisy-registry"
execute_on_jumpserver $daisy_ip "$WORKSPACE/deploy/check_os_progress.sh"
virsh reboot all_in_one
execute_on_jumpserver $daisy_ip "$WORKSPACE/deploy/check_openstack_progress.sh"

exit 0
