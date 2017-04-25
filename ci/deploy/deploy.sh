#!/bin/bash
##############################################################################
# Copyright (c) 2016 ZTE Corporation and others.
# hu.zhijiang@zte.com.cn
# lu.yao135@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

############################################################################
# BEGIN of usage description
#
function usage
{
cat << EOF
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
`basename $0`: Deploys the Daisy4NFV

usage: `basename $0` -d dha_conf -l lab_name -p pod_name
                     -r remote_workspace -w workdir

OPTIONS:
  -b  Base configuration path, necessary
  -B  PXE Bridge for booting Daisy Master, optional
  -d  Configuration yaml file of DHA, optional, will be deleted later
  -D  Dry-run, does not perform deployment, will be deleted later
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
                   -r /opt/daisy -w /opt/daisy
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
LAB_NAME=''
POD_NAME=''
TARGET_HOSTS_NUM=0
DRY_RUN=0
IS_BARE=1
VM_MULTINODE=("computer01" "computer02" "controller01" "controller02" "controller03")
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

BRIDGE=${BRIDGE:-pxebr}

# read parameters from lab configuration file
DHA_CONF=$BASE_PATH/labs/$LAB_NAME/$POD_NAME/daisy/config/deploy.yml

# set work space in daisy master node
REMOTE_SPACE=${REMOTE_SPACE:-/home/daisy}
DHA=$REMOTE_SPACE/labs/$LAB_NAME/$POD_NAME/daisy/config/deploy.yml
NETWORK=$REMOTE_SPACE/labs/$LAB_NAME/$POD_NAME/daisy/config/network.yml

# set temporay workdir
WORKDIR=${WORKDIR:-/tmp/workdir/daisy}

[[ $POD_NAME =~ (virtual) ]] && IS_BARE=0

# set extra ssh paramters
SSH_PARAS="-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"

DEPLOY_PATH=$WORKSPACE/deploy

CREATE_QCOW2_PATH=$WORKSPACE/tools

VMDELOY_DAISY_SERVER_NET=$WORKSPACE/templates/virtual_environment/networks/daisy.xml
VMDEPLOY_TARGET_NODE_NET=$WORKSPACE/templates/virtual_environment/networks/os-all_in_one.xml
VMDEPLOY_DAISY_SERVER_VM=$WORKSPACE/templates/virtual_environment/vms/daisy.xml
VMDEPLOY_TARGET_NODE_VM=$WORKSPACE/templates/virtual_environment/vms/all_in_one.xml

VMDEPLOY_NODE=[]
for ((i=0;i<${#VM_MULTINODE[@]};i++));do
    VMDEPLOY_NODE[$i]=$WORKSPACE/templates/virtual_environment/vms/${VM_MULTINODE[$i]}.xml
    echo ${VMDEPLOY_NODE[$i]}
done

BMDEPLOY_DAISY_SERVER_NET=$WORKSPACE/templates/physical_environment/networks/daisy.xml
BMDEPLOY_DAISY_SERVER_VM=$WORKSPACE/templates/physical_environment/vms/daisy.xml

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
    VMDELOY_DAISY_SERVER_NET: $VMDELOY_DAISY_SERVER_NET
    VMDEPLOY_TARGET_NODE_NET: $VMDEPLOY_TARGET_NODE_NET
    VMDEPLOY_DAISY_SERVER_VM: $VMDEPLOY_DAISY_SERVER_VM
    VMDEPLOY_TARGET_NODE_VM: $VMDEPLOY_TARGET_NODE_VM
    """
    exit 1
fi

if [ ! -f ${WORKSPACE}/opnfv.bin ]; then
    echo "opnfv.bin does not exist in WORKSPACE, exit."
    exit 1
elif [ ! -x ${WORKSPACE}/opnfv.bin ]; then
    echo "opnfv.bin in WORKSPACE is not executable, chmod it and continue."
    chmod +x ${WORKSPACE}/opnfv.bin
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

echo "====== clean up all node and network ======"
if [ $IS_BARE == 0 ];then
    clean_up all_in_one daisy2
    for ((i=0;i<${#VM_MULTINODE[@]};i++));do
        virsh destroy ${VM_MULTINODE[$i]}
        virsh undefine ${VM_MULTINODE[$i]}
    done
    clean_up daisy daisy1
else
    virsh destroy daisy
    virsh undefine daisy
fi

echo "====== create daisy node ======"
$CREATE_QCOW2_PATH/daisy-img-modify.sh -c $CREATE_QCOW2_PATH/centos-img-modify.sh -w $WORKDIR -a $DAISY_IP $PARAS_IMAGE
if [ $IS_BARE == 0 ];then
    create_node $VMDELOY_DAISY_SERVER_NET daisy1 $VMDEPLOY_DAISY_SERVER_VM daisy
else
    virsh define $BMDEPLOY_DAISY_SERVER_VM
    virsh start daisy
fi
#wait for the daisy1 network start finished for execute trustme.sh
#here sleep 40 just needed in Dell blade server
#for E9000 blade server we only have to sleep 20
sleep 40

echo "====== install daisy ======"
$DEPLOY_PATH/trustme.sh $DAISY_IP $DAISY_PASSWD
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

echo "====== generate known_hosts file in daisy vm ======"
touch $WORKSPACE/known_hosts
scp $WORKSPACE/known_hosts root@$DAISY_IP:/root/.ssh/

if [ $IS_BARE == 0 ];then
    echo "====== add relate config of kolla ======"
    ssh $SSH_PARAS $DAISY_IP "bash $REMOTE_SPACE/deploy/prepare.sh -n $NETWORK"
fi

echo "====== prepare cluster and pxe ======"
ssh $SSH_PARAS $DAISY_IP "python ${REMOTE_SPACE}/deploy/tempest.py --dha $DHA --network $NETWORK --cluster 'yes'"

echo "====== create and find node ======"
if [ $IS_BARE == 0 ];then
    if [ $TARGET_HOSTS_NUM == 1 ];then
        qemu-img create -f qcow2 ${VM_STORAGE}/all_in_one.qcow2 200G
        create_node $VMDEPLOY_TARGET_NODE_NET daisy2 $VMDEPLOY_TARGET_NODE_VM all_in_one
    else
        virsh net-define $VMDEPLOY_TARGET_NODE_NET
        virsh net-autostart daisy2
        virsh net-start daisy2
        for ((i=0;i<${#VM_MULTINODE[@]};i++));do
            qemu-img create -f qcow2 ${VM_STORAGE}/${VM_MULTINODE[$i]}.qcow2 200G
            virsh define ${VMDEPLOY_NODE[$i]}
            virsh start ${VM_MULTINODE[$i]}
        done
    fi
    sleep 20
else
    for i in $(seq 106 110); do
        ipmitool -I lanplus -H 192.168.1.$i -U zteroot -P superuser -R 1 chassis bootdev pxe
        ipmitool -I lanplus -H 192.168.1.$i -U zteroot -P superuser -R 1 chassis  power reset
    done
fi

echo "====== prepare host and pxe ======"
ssh $SSH_PARAS $DAISY_IP "python ${REMOTE_SPACE}/deploy/tempest.py  --dha $DHA --network $NETWORK --host 'yes' --isbare $IS_BARE"

if [ $IS_BARE == 0 ];then
    echo "====== daisy virtual-deploy operating system and openstack ======"
    if [ $TARGET_HOSTS_NUM == 1 ];then
        virsh destroy all_in_one
        virsh start all_in_one
    else
        for ((i=0;i<${#VM_MULTINODE[@]};i++));do
            virsh destroy ${VM_MULTINODE[$i]}
            virsh start ${VM_MULTINODE[$i]}
        done
    fi
    sleep 20
    ssh $SSH_PARAS $DAISY_IP "python ${REMOTE_SPACE}/deploy/tempest.py --dha $DHA --network $NETWORK --install 'yes'"
fi

echo "====== check operating system install progress ======"
ssh $SSH_PARAS $DAISY_IP "${REMOTE_SPACE}/deploy/check_os_progress.sh -d $IS_BARE -n $TARGET_HOSTS_NUM"
if [ $? -ne 0 ]; then
    exit 1;
fi
sleep 10

if [ $IS_BARE == 0 ];then
    if [ $TARGET_HOSTS_NUM == 1 ];then
        virsh reboot all_in_one
    else
        for ((i=0;i<${#VM_MULTINODE[@]};i++));do
            virsh reboot ${VM_MULTINODE[$i]}
        done
    fi
fi

echo "====== check openstack install progress ======"
ssh $SSH_PARAS $DAISY_IP "${REMOTE_SPACE}/deploy/check_openstack_progress.sh -n $TARGET_HOSTS_NUM"
if [ $? -ne 0 ]; then
    exit 1;
fi


if [ $IS_BARE == 0 ];then
    echo "====== post deploy ======"
    ssh $SSH_PARAS $DAISY_IP "bash $REMOTE_SPACE/deploy/post.sh -n $NETWORK"
fi

echo "====== deploy successfully ======"

exit 0

#
# END of main
############################################################################
