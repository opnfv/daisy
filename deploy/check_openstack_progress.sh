#!/bin/bash
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

maxcount=180
count=0

while true; do
    if [ $count -gt $maxcount ]; then
        echo "It took too long to install openstack, exit 1."
        exit 1
    fi
    count=$[count + 1]

    # get 'Role_status' column
    openstack_install_active=`daisy host-list --cluster-id $cluster_id | awk -F "|" '{print $13}' | grep -c "active" `
    openstack_install_failed=`daisy host-list --cluster-id $cluster_id | awk -F "|" '{print $13}' | grep -c "install-failed" `
    if [ $openstack_install_active -eq $hosts_num ]; then
        echo "openstack installing successful ..."
        break
    elif [ $openstack_install_failed -gt 0 ]; then
        echo "openstack installing have failed..."
        tail -n 200 /var/log/daisy/kolla_$cluster_id*
        exit 1
    else
        # get 'Role_progress' column
        progress=`daisy host-list --cluster-id $cluster_id |grep DISCOVERY_SUCCESSFUL |awk -F "|" '{print $12}'|sed s/[[:space:]]//g|sed ':a;N;$ s/\n/ /g;ba'`
        echo " openstack in installing , progress of each node is $progress%"
        sleep 30
    fi
done
