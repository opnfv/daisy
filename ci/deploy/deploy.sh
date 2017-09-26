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
  -D  Dry-run, does not perform deployment, will be deleted later
  -L  Securelab repo dir
  -l  LAB name, necessary
  -p  POD name, necessary
  -r  Remote workspace in target server, optional
  -w  Workdir for temporary usage, optional
  -h  Print this message and exit
  -s  Deployment scenario
  -S  Skip recreate Daisy VM during deployment

Description:
Deploys the Daisy4NFV on the indicated lab resource

Examples:
sudo `basename $0` -b base_path
                   -l zte -p pod2 -B pxebr
                   -r /opt/daisy -w /opt/daisy -s os-nosdn-nofeature-noha
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
SKIP_DEPLOY_DAISY=0
VM_MULTINODE=("computer01" "computer02" "controller02" "controller03" "controller01")
VALID_DEPLOY_SCENARIO=("os-nosdn-nofeature-noha" "os-nosdn-nofeature-ha" "os-odl_l3-nofeature-noha"
                       "os-odl_l2-nofeature-noha" "os-odl_l3-nofeature-ha" "os-odl_l2-nofeature-ha"
                       "os-odl-nofeature-noha" "os-odl-nofeature-ha")

#
# END of variables to customize
############################################################################

############################################################################
# BEGIN of main
#
while getopts "b:B:Dn:L:l:p:r:w:s:Sh" OPTION
do
    case $OPTION in
        b)
            BASE_PATH=${OPTARG}
            ;;
        B)
            BRIDGE=${OPTARG}
            ;;
        D)
            DRY_RUN=1
            ;;
        L)
            SECURELABDIR=${OPTARG}
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
        s)
            DEPLOY_SCENARIO=${OPTARG}
            ;;
        S)
            SKIP_DEPLOY_DAISY=1
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

DEPLOY_SCENARIO=${DEPLOY_SCENARIO:-"os-nosdn-nofeature-noha"}

BRIDGE=${BRIDGE:-pxebr}

SECURELABDIR=${SECURELABDIR:-./securedlab}

# these two config file should be copied to daisy node and names as
# ${DHA} and ${NETWORK}, see below.
DHA_CONF=$SECURELABDIR/labs/$LAB_NAME/$POD_NAME/daisy/config/deploy.yml
NETWORK_CONF=$SECURELABDIR/labs/$LAB_NAME/$POD_NAME/daisy/config/network.yml

# work space and config file name in daisy node
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
VMDEPLOY_TARGET_NODE_NET=$WORKSPACE/templates/virtual_environment/networks/external.xml
VMDEPLOY_TARGET_KEEPALIVED_NET=$WORKSPACE/templates/virtual_environment/networks/keepalived.xml
VMDEPLOY_DAISY_SERVER_VM=$WORKSPACE/templates/virtual_environment/vms/daisy.xml
VMDEPLOY_TARGET_NODE_VM=$WORKSPACE/templates/virtual_environment/vms/all_in_one.xml

VMDEPLOY_NODE=[]
for ((i=0; i < ${#VM_MULTINODE[@]}; i++)); do
    if [[ ${VM_MULTINODE[$i]} == *controller* ]]; then
        nodename_prefix="controller"
    else
        nodename_prefix="computer"
    fi
    VMDEPLOY_NODE[$i]=$WORKSPACE/templates/virtual_environment/vms/${VM_MULTINODE[$i]}.xml
    cp $WORKSPACE/templates/virtual_environment/vms/${nodename_prefix}.xml ${VMDEPLOY_NODE[$i]}
    sed -i "s/nodename/${VM_MULTINODE[$i]}/g" ${VMDEPLOY_NODE[$i]}
    echo ${VMDEPLOY_NODE[$i]}
done

BMDEPLOY_DAISY_SERVER_NET=$WORKSPACE/templates/physical_environment/networks/daisy.xml
BMDEPLOY_DAISY_SERVER_VM=$WORKSPACE/templates/physical_environment/vms/daisy.xml

# Note: This function must be exectuted in ${SECURELABDIR}
function update_dha_by_pdf()
{
    local pdf_yaml=labs/$LAB_NAME/${POD_NAME}.yaml
    local jinja2_template=installers/daisy/pod_config.yaml.j2
    local generate_config=utils/generate_config.py
    if [ ! -f ${generate_config} ] || [ ! -f ${pdf_yaml} ] || [ ! -f ${jinja2_template} ]; then
        return
    fi

    local tmpfile=$(mktemp XXXXXXXX.yml)
    python ${generate_config} -j ${jinja2_template} -y ${pdf_yaml} > ${tmpfile}
    if [ $? -ne 0 ]; then
        echo "Cannot generate config from POD Descriptor File, use original deploy.yml !"
        return
    fi
    if [ -z $(awk "BEGIN{}(/daisy_ip/){print NR}" $tmpfile) ]; then
        line=$(awk "BEGIN{}(/daisy_gateway/){print NR}" $tmpfile)
        sed -i "${line} i\daisy_ip: $INSTALLER_IP" $tmpfile
    fi
    if [ $? -ne 0 ]; then
        echo "Cannot write INSTALLER_IP to config file, use original deploy.yml !"
        rm $tmpfile
        return
    fi
    cp ${tmpfile} ${DHA_CONF}
    echo "====== Update deploy.yml from POD Descriptor File ======"
    rm -f $tmpfile
}

if [[ ! -z $INSTALLER_IP ]]; then
    pushd ${SECURELABDIR}
    update_dha_by_pdf
    popd
fi

# read parameters from $DHA_CONF
PARAS_FROM_DEPLOY=`python $WORKSPACE/deploy/get_conf.py --dha $DHA_CONF`
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
    DEPLOY_SCENARIO: $DEPLOY_SCENARIO
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

function check_scenario_arg
{
    local is_valid_scenario=0

    for item in ${VALID_DEPLOY_SCENARIO[@]};do
        if [ ${DEPLOY_SCENARIO} == $item ]; then
            is_valid_scenario=1
            break
        fi
    done

    if [ $is_valid_scenario -eq 0 ]; then
        echo "Invalid scenario argument:${DEPLOY_SCENARIO}"
        exit 1
    fi
}

check_scenario_arg

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

function clean_up_target_vms()
{
    local vms=$(virsh list --all | tail -n +3 | awk '{print $2}')
    local active_vms=$(virsh list | tail -n +3 | awk '{print $2}')
    for vm_name in ${VM_MULTINODE[@]} all_in_one; do
        if [[ $(echo $vms | tr " " "\n" | grep ^$vm_name$) ]]; then
            [[ $(echo $active_vms | tr " " "\n" | grep ^$vm_name$) ]] && virsh destroy $vm_name
            virsh undefine $vm_name
        fi
    done
}

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

function clean_up_target_vnetworks()
{
    local nets=$(virsh net-list --all | tail -n +3 |awk '{print $1}')
    local active_nets=$(virsh net-list | tail -n +3 |awk '{print $1}')
    for net_template in ${VMDEPLOY_TARGET_NODE_NET} ${VMDEPLOY_TARGET_KEEPALIVED_NET}; do
        network_name=$(grep "<name>" $net_template | awk -F "<|>" '{print $3}')
        if [[ $(echo $nets | tr " " "\n" | grep ^$network_name$) ]]; then
            [[ $(echo $active_nets | tr " " "\n" | grep ^$network_name$) ]] && virsh net-destroy $network_name
            virsh net-undefine $network_name
        fi
    done
}

function update_pxe_bridge()
{
    bridge_name=$(grep "<source * bridge" $BMDEPLOY_DAISY_SERVER_VM | awk -F "'" '{print $2}') || True
    if [ ${bridge_name} ] && [ ${bridge_name} != ${BRIDGE} ] && [ ! -z ${bridge_name} ]; then
        echo "Use $BRIDGE to replace the bridge in $BMDEPLOY_DAISY_SERVER_VM"
        sed -i -e "/source * bridge/{s/source.*$/source bridge=\'$BRIDGE\'\/>/;}" $BMDEPLOY_DAISY_SERVER_VM
    fi
}

function create_daisy_vm_and_networks()
{
    echo "====== Create Daisy VM ======"
    $CREATE_QCOW2_PATH/daisy-img-modify.sh -c $CREATE_QCOW2_PATH/centos-img-modify.sh -w $WORKDIR -a $DAISY_IP $PARAS_IMAGE
    if [ $IS_BARE == 0 ];then
        create_node $VMDELOY_DAISY_SERVER_NET daisy1 $VMDEPLOY_DAISY_SERVER_VM daisy
    else
        update_pxe_bridge
        virsh define $BMDEPLOY_DAISY_SERVER_VM
        virsh start daisy
    fi

    #wait for the daisy1 network start finished for execute trustme.sh
    #here sleep 40 just needed in Dell blade server
    #for E9000 blade server we only have to sleep 20
    sleep 40
}

function clean_up_daisy_vm_and_networks()
{
    echo "====== Clean up Daisy VM and networks ======"
    clean_up_daisy_vm
    if [ $IS_BARE == 0 ];then
        clean_up_daisy_vnetworks
    fi
}

function clean_up_target_vms_and_networks()
{
    echo "====== Clean up all target VMs and networks ======"
    if [ $IS_BARE == 0 ];then
        clean_up_target_vms
        clean_up_target_vnetworks
    fi
}

function install_daisy()
{
    echo "====== install daisy ======"
    $DEPLOY_PATH/trustme.sh $DAISY_IP $DAISY_PASSWD
    ssh $SSH_PARAS $DAISY_IP "if [[ -f ${REMOTE_SPACE} || -d ${REMOTE_SPACE} ]]; then rm -fr ${REMOTE_SPACE}; fi"
    scp -r $WORKSPACE root@$DAISY_IP:${REMOTE_SPACE}
    scp -q ${DHA_CONF} root@$DAISY_IP:${DHA}
    scp -q ${NETWORK_CONF} root@$DAISY_IP:${NETWORK}
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

    #TODO: Why need this?
    echo "====== generate known_hosts file in daisy vm ======"
    touch $WORKSPACE/known_hosts
    scp $WORKSPACE/known_hosts root@$DAISY_IP:/root/.ssh/
}

function config_daisy()
{
    echo "====== add relate config for Daisy and Kolla ======"
    ssh $SSH_PARAS $DAISY_IP "bash $REMOTE_SPACE/deploy/prepare.sh -n $NETWORK -b $IS_BARE"
}

clean_up_target_vms_and_networks

if [ ! $SKIP_DEPLOY_DAISY -eq 1 ]; then
    clean_up_daisy_vm_and_networks
    create_daisy_vm_and_networks
    install_daisy
    config_daisy
fi


echo "====== prepare cluster and pxe ======"
ssh $SSH_PARAS $DAISY_IP "python ${REMOTE_SPACE}/deploy/tempest.py --dha $DHA --network $NETWORK --cluster 'yes'"


function get_mac_addresses_for_virtual()
{
    tmpfile=$(mktemp XXXXXXXX.yml)
    cp $DHA_CONF $tmpfile

    if [ $TARGET_HOSTS_NUM -ne 1 ]; then
        for ((i=0;i<${#VM_MULTINODE[@]};i++));do
            name=${VM_MULTINODE[$i]}
            macs=$(virsh dumpxml $name | grep "<mac" | awk -F "'" '{print $2}' | tr "\n" " ")
            line=$(awk "BEGIN{}(/name/&&/$name/){print NR}" $tmpfile)
            sed -i "${line}a\  mac_addresses:" $tmpfile
            for mac in $macs; do
                line=$[ line + 1 ]
                sed -i "${line}a\    - \'$mac\'" $tmpfile
            done
        done
    else
        name="all_in_one"
        macs=$(virsh dumpxml $name | grep "<mac" | awk -F "'" '{print $2}' | tr "\n" " ")
        line=$(awk "BEGIN{}(/name/&&/$name/){print NR}" $tmpfile)
        sed -i "${line}a\  mac_addresses:" $tmpfile
        for mac in $macs; do
            line=$[ line + 1 ]
            sed -i "${line}a\    - \'$mac\'" $tmpfile
        done
    fi

    # update DHA file in daisy node
    scp -q $tmpfile root@$DAISY_IP:$DHA
    rm $tmpfile
}


function reboot_baremetal_node()
{
    ips=(`grep ipmi_ip $DHA_CONF | awk '{print $2}' | tr "\n" " " | tr -d "\'"`)
    ip_num=${#ips[@]}
    users=(`grep ipmi_user $DHA_CONF | awk '{print $2}' | tr "\n" " " | tr -d "\'"`)
    user_num=${#users[@]}
    passwds=(`grep ipmi_pass $DHA_CONF | awk '{print $2}' | tr "\n" " " | tr -d "\'"`)
    pass_num=${#passwds[@]}

    if [ $ip_num -ne $TARGET_HOSTS_NUM ]; then
        echo "ERROR: IPMI information should be provided for each node !"
        exit 1
    fi

    for ((i=0; i<$ip_num; i++)); do
        if [ $TARGET_HOSTS_NUM -eq $user_num ] && [ $TARGET_HOSTS_NUM -eq $pass_num ]; then
            ipmitool -I lanplus -H ${ips[$i]} -U ${users[$i]} -P ${passwds[$i]} -R 1 chassis bootdev pxe
            ipmitool -I lanplus -H ${ips[$i]} -U ${users[$i]} -P ${passwds[$i]} -R 1 chassis power reset
        else
            ipmitool -I lanplus -H ${ips[$i]} -R 1 chassis bootdev pxe
            ipmitool -I lanplus -H ${ips[$i]} -R 1 chassis power reset
        fi
    done
}

echo "====== create and find node ======"
if [ $IS_BARE == 0 ];then
    if [ $TARGET_HOSTS_NUM == 1 ];then
        qemu-img create -f qcow2 ${VM_STORAGE}/all_in_one.qcow2 200G
        create_node $VMDEPLOY_TARGET_NODE_NET daisy2 $VMDEPLOY_TARGET_NODE_VM all_in_one
    else
        virsh net-define $VMDEPLOY_TARGET_NODE_NET
        virsh net-autostart daisy2
        virsh net-start daisy2
        virsh net-define $VMDEPLOY_TARGET_KEEPALIVED_NET
        virsh net-autostart daisy3
        virsh net-start daisy3
        for ((i=0;i<${#VM_MULTINODE[@]};i++));do
            qemu-img create -f qcow2 ${VM_STORAGE}/${VM_MULTINODE[$i]}.qcow2 120G
            qemu-img create -f qcow2 ${VM_STORAGE}/${VM_MULTINODE[$i]}_data.qcow2 150G
            virsh define ${VMDEPLOY_NODE[$i]}
            virsh start ${VM_MULTINODE[$i]}
        done
    fi
    sleep 20
    get_mac_addresses_for_virtual
else
    reboot_baremetal_node
fi

echo "====== prepare host and pxe ======"
ssh $SSH_PARAS $DAISY_IP "python ${REMOTE_SPACE}/deploy/tempest.py  --dha $DHA --network $NETWORK --host 'yes' --isbare $IS_BARE --scenario $DEPLOY_SCENARIO"

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
        virsh reset all_in_one
    else
        for ((i=0;i<${#VM_MULTINODE[@]};i++));do
            virsh reset ${VM_MULTINODE[$i]}
        done
    fi
fi

echo "====== check openstack install progress ======"
ssh $SSH_PARAS $DAISY_IP "${REMOTE_SPACE}/deploy/check_openstack_progress.sh -n $TARGET_HOSTS_NUM"
if [ $? -ne 0 ]; then
    exit 1;
fi


echo "====== post deploy ======"
ssh $SSH_PARAS $DAISY_IP "bash $REMOTE_SPACE/deploy/post.sh -n $NETWORK"

if [ $IS_BARE == 0 ]; then
    echo "====== disable iptable rules ======"
    iptables -D FORWARD -o daisy1 -j REJECT --reject-with icmp-port-unreachable
    iptables -D FORWARD -i daisy1 -j REJECT --reject-with icmp-port-unreachable
    iptables -D FORWARD -o daisy2 -j REJECT --reject-with icmp-port-unreachable
    iptables -D FORWARD -i daisy2 -j REJECT --reject-with icmp-port-unreachable
fi

echo "====== deploy successfully ======"

exit 0

#
# END of main
############################################################################
