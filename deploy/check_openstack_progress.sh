#!/bin/bash
source /root/daisyrc_admin
echo "check openstack installing progress..."
cluster_id=`daisy cluster-list | awk -F "|" '{print $2}' | sed -n '4p'`

maxcount=180
count=0

while true; do
    if [ $count -gt $maxcount ]; then
        echo "It took too long to install openstack, exit 1."
        exit 1
    fi
    count=$[count + 1]

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
        progress=`daisy host-list --cluster-id $cluster_id |grep DISCOVERY_SUCCESSFUL |awk -F "|" '{print $11}'|sed s/[[:space:]]//g`
        echo " openstack in installing , progress is $progress%"
        sleep 30
    fi
done
