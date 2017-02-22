#!/bin/bash
##############################################################################
# Copyright (c) 2016 ZTE Corporation and others.
# hu.zhijiang@zte.com.cn
# lu.yao135@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
# TODO
# [x] 1. Pass full path for parameter for -d and -n
# [x] 2. Refactor para fetching procedure of paras_from_deploy
# [x] 3. Refactor execute_on_jumpserver
# [ ] 4. Refactor for names for var such like daisy_server_net, target_node_net
# [ ] 5. Store PODs' configruation files into securelab
# [ ] 6. Use POD name as the parameter instead of files
##############################################################################
#daisy host discover

############################################################################
# BEGIN of usage description
#
usage ()
{
cat << EOF
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
`basename $0`: Deploys the Daisy4NFV

usage: `basename $0` -d dha_conf -n network_con -l lab_name -p pod_name
                     -r remote_workspace -w workdir

OPTIONS:
  -b  Base configuration path, necessary
  -B  PXE Bridge for booting Daisy Master, optional
  -d  Configuration yaml file of DHA, optional, will be deleted later
  -D  Dry-run, does not perform deployment, will be deleted later
  -n  Configuration yaml file of network, optional
  -l  LAB name, necessary
  -p  POD name, necessary
  -r  Remote workspace in target server, optional
  -w  Workdir for temporary usage, optional
  -h  Print this message and exit

Description:
Deploys the Daisy4NFV on the indicated lab resource

Examples:
sudo `basename $0` -b base_path
                   -l zte -p pod2 -B pxebr
                   -d ./deploy/config/vm_environment/zte-virtual1/deploy.yml
                   -n ./deploy/config/vm_environment/zte-virtual1/network.yml
                   -r /opt/daisy -w /opt/daisy -l zte -p pod2
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EOF
}

#
# END of usage description
############################################################################


############################################################################
# BEGIN of variables for internal use
#
SCRIPT_PATH=$(readlink -f $(dirname $0))
WORKSPACE=$(cd ${SCRIPT_PATH}/../..; pwd)
VM_STORAGE=/home/qemu/vms
DHA_CONF=''
NETWORK_CONF=''
LAB_NAME=''
POD_NAME=''
TARGET_HOSTS_NUM=0
DRY_RUN=0
IS_BARE=1
#
# END of variables to customize
############################################################################

############################################################################
# BEGIN of main
#
while getopts "b:B:Dd:n:l:p:r:w:h" OPTION
do
    case $OPTION in
        b)
            BASE_PATH=${OPTARG}
            ;;
        B)
            BRIDGE=${OPTARG}
            ;;
        d)
            DHA_CONF=${OPTARG}
            ;;
        D)
            DRY_RUN=1
            ;;
        n)
            NETWORK_CONF=${OPTARG}
            ;;
        l)
            LAB_NAME=${OPTARG}
            ;;
        p)
            POD_NAME=${OPTARG}
            ;;
        r)
            REMOTE_SPACE=${OPTARG}
            ;;
        w)
            WORKDIR=${OPTARG}
            ;;
        h)
            usage
            exit 0
            ;;
        *)
            echo "${OPTION} is not a valid argument"
            usage
            exit 0
            ;;
    esac
done

if [ -z $BASE_PATH ] || [ ! -d $BASE_PATH ] || [ -z LAB_NAME ] || [ -z $POD_NAME ] ; then
    echo """Please check
    BASE_PATH: $BASE_PATH
    LAB_NAME: $LAB_NAME
    POD_NAME: $POD_NAME
    """
    usage
    echo "exit abnormal"
    exit 0
fi

BRIDGE={BRIDGE:-pxebr}

# read parameters from lab configuration file
DHA_CONF=$BASE_PATH/labs/$LAB_NAME/$POD_NAME/daisy/config/deploy.yml

# set work space in daisy master node
REMOTE_SPACE=${REMOTE_SPACE:-/home/daisy}
DHA=$REMOTE_SPACE/labs/$LAB_NAME/$POD_NAME/daisy/config/deploy.yml
NETWORK=$REMOTE_SPACE/labs/$LAB_NAME/$POD_NAME/daisy/config/network.yml

# set temporay workdir
WORKDIR=${WORKDIR:-/tmp/workdir}

[[ $POD_NAME =~ (virtual) ]] && IS_BARE=0

# set extra ssh paramters
SSH_PARAS="-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"

deploy_path=$WORKSPACE/deploy

create_qcow2_path=$WORKSPACE/tools

daisy_server_net=$WORKSPACE/templates/virtual_environment/networks/daisy.xml
target_node_net=$WORKSPACE/templates/virtual_environment/networks/os-all_in_one.xml
vmdeploy_daisy_server_vm=$WORKSPACE/templates/virtual_environment/vms/daisy.xml
vmdeploy_target_node_vm=$WORKSPACE/templates/virtual_environment/vms/all_in_one.xml


bmdeploy_daisy_server_net=$WORKSPACE/templates/physical_environment/networks/daisy.xml
bmdeploy_daisy_server_vm=$WORKSPACE/templates/physical_environment/vms/daisy.xml

PARAS_FROM_DEPLOY=`python $WORKSPACE/deploy/get_para_from_deploy.py --dha $DHA_CONF`
TARGET_HOSTS_NUM=`echo $PARAS_FROM_DEPLOY | cut -d " " -f 1`
DAISY_IP=`echo $PARAS_FROM_DEPLOY | cut -d " " -f 2`
DAISY_PASSWD=`echo $PARAS_FROM_DEPLOY | cut -d " " -f 3`
PARAS_IMAGE=${PARAS_FROM_DEPLOY#* * * }


if [ $DRY_RUN -eq 1 ]; then
    echo """
    BASE_PATH: $BASE_PATH
    LAB_NAME: $LAB_NAME
    POD_NAME: $POD_NAME
    IS_BARE: $IS_BARE
    DAISY_IP: $DAISY_IP
    DAISY_PASSWD: $DAISY_PASSWD
    PARAS_IMAGE: $PARAS_IMAGE
    daisy_server_net: $daisy_server_net
    target_node_net: $target_node_net
    vmdeploy_daisy_server_vm: $vmdeploy_daisy_server_vm
    vmdeploy_target_node_vm: $vmdeploy_target_node_vm
    """
    exit 1
fi

test -d ${VM_STORAGE} || mkdir -p ${VM_STORAGE}

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
if [ $IS_BARE == 0 ];then
    clean_up all_in_one daisy2
fi
clean_up daisy daisy1
if [ -f $WORKDIR/daisy/centos7.qcow2 ]; then
    rm -rf $WORKDIR/daisy/centos7.qcow2
fi

echo "=======create daisy node================"
if [ $IS_BARE == 0 ];then
    $create_qcow2_path/daisy-img-modify.sh -c $create_qcow2_path/centos-img-modify.sh -a $DAISY_IP $PARAS_IMAGE
    create_node $daisy_server_net daisy1 $vmdeploy_daisy_server_vm daisy
else
    $create_qcow2_path/daisy-img-modify.sh -c $create_qcow2_path/centos-img-modify.sh -a $DAISY_IP $PARAS_IMAGE
    create_node $bmdeploy_daisy_server_net daisy1 $bmdeploy_daisy_server_vm daisy
fi
sleep 20

echo "====== install daisy==========="
$deploy_path/trustme.sh $DAISY_IP $DAISY_PASSWD
ssh $SSH_PARAS $DAISY_IP "if [[ -f ${REMOTE_SPACE} || -d ${REMOTE_SPACE} ]]; then rm -fr ${REMOTE_SPACE}; fi"
scp -r $WORKSPACE root@$DAISY_IP:${REMOTE_SPACE}
ssh $SSH_PARAS $DAISY_IP "mkdir -p /home/daisy_install"
update_config $WORKSPACE/deploy/daisy.conf daisy_management_ip $DAISY_IP
scp $WORKSPACE/deploy/daisy.conf root@$DAISY_IP:/home/daisy_install
ssh $SSH_PARAS $DAISY_IP "${REMOTE_SPACE}/opnfv.bin  install"
rc=$?
if [ $rc -ne 0 ]; then
    echo "daisy install failed"
    exit 1
else
    echo "daisy install successfully"
fi

echo "====== add relate config of kolla==========="
ssh $SSH_PARAS $DAISY_IP "mkdir -p /etc/kolla/config/nova"
ssh $SSH_PARAS $DAISY_IP "echo -e '[libvirt]\nvirt_type=qemu' > /etc/kolla/config/nova/nova-compute.conf"

echo "===prepare cluster and pxe==="
ssh $SSH_PARAS $DAISY_IP "python ${REMOTE_SPACE}/deploy/tempest.py --dha $DHA --network $NETWORK --cluster 'yes'"

echo "=====create and find node======"
if [ $IS_BARE == 0 ];then
    qemu-img create -f qcow2 ${VM_STORAGE}/all_in_one.qcow2 200G
    create_node $target_node_net daisy2 $vmdeploy_target_node_vm all_in_one
    sleep 20
else
    for i in $(seq 106 110); do
        ipmitool -I lanplus -H 192.168.1.$i -U zteroot -P superuser -R 1 chassis bootdev pxe
        ipmitool -I lanplus -H 192.168.1.$i -U zteroot -P superuser -R 1 chassis  power reset
    done
fi

echo "======prepare host and pxe==========="
ssh $SSH_PARAS $DAISY_IP "python ${REMOTE_SPACE}/deploy/tempest.py  --dha $DHA --network $NETWORK --host 'yes' --env $IS_BARE"

echo "======daisy deploy os and openstack==========="
if [ $IS_BARE == 0 ];then
    virsh destroy all_in_one
    virsh start all_in_one
fi

echo "============restart daisy service==========="
ssh $SSH_PARAS $DAISY_IP "systemctl restart daisy-api"
ssh $SSH_PARAS $DAISY_IP "systemctl restart daisy-registry"

echo "===========check install progress==========="
ssh $SSH_PARAS $DAISY_IP "${REMOTE_SPACE}/deploy/check_os_progress.sh -d $IS_BARE -n $TARGET_HOSTS_NUM"
sleep 10

if [ $IS_BARE == 0 ];then
    virsh reboot all_in_one
fi
ssh $SSH_PARAS $DAISY_IP "${REMOTE_SPACE}/deploy/check_openstack_progress.sh"

exit 0

#
# END of main
############################################################################
