#!/bin/bash
##############################################################################
# Copyright (c) 2017 ZTE Corporation and others.
# hu.zhijiang@zte.com.cn
# lu.yao135@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

usage()
{
    cat << EOF
USAGE: `basename $0`  [-n hosts_num]

OPTIONS:
  -n target node numbers

EXAMPLE:
    sudo `basename $0` -n 5
EOF
}

function dump_log_for_cluster()
{
    local cid
    cid=$1

    echo "Show daisy api log as following ..."
    cat /var/log/daisy/api.log |grep -v wsgi

    files=$(ls /var/log/daisy/kolla_$cid* 2>/dev/null | wc -l)
    if [ $files -ne 0 ]; then
        echo "----------------------------------------------------"
        echo "Show kolla installation log as following ..."
        tail -n 5000 /var/log/daisy/kolla_$cid*
    else
        prepare_files=$(ls /var/log/daisy/kolla_prepare_$cid* 2>/dev/null | wc -l)
        if [ $prepare_files -ne 0 ]; then
            echo "----------------------------------------------------"
            echo "Show kolla preparation log as following ..."
            tail -n 5000 /var/log/daisy/kolla_prepare_$cid*
        fi
    fi
}

while getopts "n:h" OPTION
do
    case $OPTION in
        n)
            hosts_num=${OPTARG}
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

source /root/daisyrc_admin
echo "check openstack installing progress..."
cluster_id=`daisy cluster-list | awk -F "|" '{print $2}' | sed -n '4p' | tr -d " "`

maxcount=360
count=0

while true; do
    if [ $count -gt $maxcount ]; then
        echo "It took too long to install openstack, exit."
        dump_log $cluster_id
        exit 1
    fi
    count=$[count + 1]

    # get 'Role_status' column
    openstack_install_active=`daisy host-list --cluster-id $cluster_id | awk -F "|" '{print $13}' | grep -c "active" `
    openstack_install_failed=`daisy host-list --cluster-id $cluster_id | awk -F "|" '{print $13}' | grep -c "install-failed" `
    if [ $openstack_install_active -eq $hosts_num ]; then
        echo "openstack installation succeded ..."
        break
    elif [ $openstack_install_failed -gt 0 ]; then
        echo "openstack installation failed ..."
        dump_log $cluster_id
        exit 1
    else
        # get 'Role_progress' column
        progress=`daisy host-list --cluster-id $cluster_id |grep DISCOVERY_SUCCESSFUL |awk -F "|" '{print $12}'|sed s/[[:space:]]//g|sed ':a;N;$ s/\n/ /g;ba'`
        echo " openstack in installing , progress of each node is $progress%"
        sleep 30
    fi
done
