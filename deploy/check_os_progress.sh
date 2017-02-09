#!/bin/bash
source /root/daisyrc_admin
cluster_id=`daisy cluster-list | awk -F "|" '{print $2}' | sed -n '4p'`
deploy_env=$1
if [ $DEPLOY_ENV == "virtual" ];then
    daisy install $cluster_id --skip-pxe-ipmi true
else
    daisy install $cluster_id
fi
echo "check os installing progress..."
while true; do
    os_install_active=`daisy host-list --cluster-id $cluster_id | awk -F "|" '{print $8}' | grep -c "active" `
    os_install_failed=`daisy host-list --cluster-id $cluster_id | awk -F "|" '{print $8}' | grep -c "install-failed" `
    if [ $os_install_active -eq 1 ]; then
        echo "os installing successful ..."
        break
    elif [ $os_install_failed -gt 0 ]; then
        echo "os installing have failed..."
        exit 1
    else
        progress=`daisy host-list --cluster-id $cluster_id |grep DISCOVERY_SUCCESSFUL |awk -F "|" '{print $7}'|sed s/[[:space:]]//g`
        echo "os in installing, the progress is $progress%"
        sleep 10
    fi
done
systemctl disable dhcpd
systemctl stop dhcpd
