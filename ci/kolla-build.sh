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

set -o errexit
set -o nounset
set -o pipefail

VM_PARAMS=$@

exitcode=""
error_trap()
{
    local rc=$?

    set +e

    if [ -z "$exitcode" ]; then
        exitcode=$rc
    fi

    echo "Image build failed with $exitcode"

    exit $exitcode
}

WORK_DIR=/tmp
while getopts "l:b:j:t:e:w:h" OPTION
do
    #Only get what we need
    case $OPTION in
        w)
            WORK_DIR=${OPTARG}
            ;;
    esac
done

BUILD_OUTPUT_DIR=$WORK_DIR/kolla-build-output

############Builder VM operations################

SCRIPT_PATH=$(readlink -f $(dirname $0))
WORKSPACE=$(cd ${SCRIPT_PATH}/..; pwd)
DEPLOY_PATH=$WORKSPACE/deploy

# VM configurations
VMDELOY_DAISY_SERVER_NET=$WORKSPACE/templates/virtual_environment/networks/daisy.xml
VMDEPLOY_DAISY_SERVER_VM=$WORKSPACE/templates/virtual_environment/vms/daisy.xml

# read deploy parameters from $DHA_CONF, any DHA_CONF is OK for us, so we choose zte-virtual1
DHA_CONF=$WORKSPACE/deploy/config/vm_environment/zte-virtual1/deploy.yml
PARAS_FROM_DEPLOY=`python $WORKSPACE/deploy/get_conf.py --dha $DHA_CONF`
DAISY_IP=`echo $PARAS_FROM_DEPLOY | cut -d " " -f 2`
DAISY_PASSWD=`echo $PARAS_FROM_DEPLOY | cut -d " " -f 3`
PARAS_IMAGE=${PARAS_FROM_DEPLOY#* * * }

# qcow2 image modifier location
CREATE_QCOW2_PATH=$WORKSPACE/tools
# temp storage for qcow2 image modifier
IMWORKDIR=${IMWORKDIR:-/tmp/workdir/daisy}

# set extra ssh paramters
SSH_PARAS="-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"

# work space and config files' path(absolute) in daisy node
REMOTE_SPACE=${REMOTE_SPACE:-/home/daisy}

function clean_up_daisy_vm()
{
    local vms=$(virsh list --all | tail -n +3 | awk '{print $2}')
    local active_vms=$(virsh list | tail -n +3 | awk '{print $2}')
    vm_name=daisy
    if [[ $(echo $vms | tr " " "\n" | grep ^$vm_name$) ]]; then
        [[ $(echo $active_vms | tr " " "\n" | grep ^$vm_name$) ]] && virsh destroy $vm_name
        virsh undefine $vm_name
    fi
}

function clean_up_daisy_vnetworks()
{
    local nets=$(virsh net-list --all | tail -n +3 |awk '{print $1}')
    local active_nets=$(virsh net-list | tail -n +3 |awk '{print $1}')
    for net_template in ${VMDELOY_DAISY_SERVER_NET}; do
        network_name=$(grep "<name>" $net_template | awk -F "<|>" '{print $3}')
        if [[ $(echo $nets | tr " " "\n" | grep ^$network_name$) ]]; then
            [[ $(echo $active_nets | tr " " "\n" | grep ^$network_name$) ]] && virsh net-destroy $network_name
            virsh net-undefine $network_name
        fi
    done
}

function clean_up_daisy_vm_and_networks()
{
    echo "====== Clean up Daisy VM and networks ======"
    clean_up_daisy_vm
    clean_up_daisy_vnetworks
}

function create_daisy_vm_and_networks()
{
    echo "====== Create Daisy VM ======"
    $CREATE_QCOW2_PATH/daisy-img-modify.sh -c $CREATE_QCOW2_PATH/centos-img-modify.sh -w $IMWORKDIR -a $DAISY_IP $PARAS_IMAGE

    virsh net-define $VMDELOY_DAISY_SERVER_NET
    virsh net-start daisy1 

    virsh define $VMDEPLOY_DAISY_SERVER_VM
    virsh start daisy

    #wait for the daisy1 network start finished for execute trustme.sh
    #here sleep 40 just needed in Dell blade server
    #for E9000 blade server we only have to sleep 20
    sleep 40
}

function build_kolla_image_in_daisy_vm()
{
    echo "====== build_kolla_image_in_daisy_vm ======"
    $DEPLOY_PATH/trustme.sh $DAISY_IP $DAISY_PASSWD
    ssh $SSH_PARAS $DAISY_IP "if [[ -f ${REMOTE_SPACE} || -d ${REMOTE_SPACE} ]]; then rm -fr ${REMOTE_SPACE}; fi"
    scp -r $WORKSPACE root@$DAISY_IP:${REMOTE_SPACE}
    ssh $SSH_PARAS $DAISY_IP "${REMOTE_SPACE}/ci/kolla-build-vm.sh $VM_PARAMS"
    rc=$?
    if [ $rc -ne 0 ]; then
        echo "daisy install failed"
        exit 1
    else
        echo "daisy install successfully"
    fi

    rm -rf $BUILD_OUTPUT_DIR
    mkdir -p $BUILD_OUTPUT_DIR
    scp -r root@$DAISY_IP:$BUILD_OUTPUT_DIR $WORK_DIR
}

trap "error_trap" EXIT SIGTERM

clean_up_daisy_vm_and_networks
create_daisy_vm_and_networks
build_kolla_image_in_daisy_vm
