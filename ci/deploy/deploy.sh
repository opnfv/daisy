#!/bin/bash
##############################################################################
# Copyright (c) 2016 ZTE Coreporation and others.
# hu.zhijiang@zte.com.cn
# sun.jing22@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
#daisy host discover
DAISYDIR=
json_file=$DAISYDIR/deploy/config/vm_environment/zte-virtual/template.json
source ~/daisyrc_admin
daisy discover-host-add 192.168.122.152 ossdbg1
daisy discover-host

cnt=30
while [ $cnt -ge 0 ]; do
    host_id=`daisy host-list |grep -w 'DaisyNode5' | awk -F "|" '{print $2}'| grep -o "[^ ]\+\( \+[^ ]\+\)*" `
    if [ -z "$host_id" ]; then
        echo "host have not discoverd , loop again  ... "
        cnt=$[$cnt-1]
        sleep 30
    else
        echo "host list checkout successful... "
    break
    fi
done
daisy host-list

echo "======prepare install os(centos) & kolla(openstack) ==========="
daisy import-json-to-template $json_file
daisy import-template-to-db template testdaisy
daisy template-to-host testdaisy DaisyNode $host_id

echo "======daisy install kolla(openstack)==========="
cluster_id=`daisy cluster-list | awk -F "|" '{print $2}' | sed -n '4p'`
daisy install $cluster_id

echo "check installing proess..."
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
