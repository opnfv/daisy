#!/bin/bash
usage()
{
    cat << EOF
USAGE: `basename $0` [-d deploy_env] [-n hosts_num]

OPTIONS:
  -d deploy environment of daisy(0:virtual or 1:baremetal)
  -n target node numbers

EXAMPLE:
    sudo `basename $0` -d 1 -n 5
EOF
}

while getopts "d:n:h" OPTION
do
    case $OPTION in
        d)
            deploy_env=${OPTARG}
            ;;
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
cluster_id=`daisy cluster-list | awk -F "|" '{print $2}' | sed -n '4p' | tr -d " "`
hosts_id=`daisy host-list | awk -F "|" '{print $2}'| grep -o "[^ ]\+\( \+[^ ]\+\)*"|tail -n +2`
if [ $deploy_env == 0 ];then
    for host_id in $hosts_id
    do
        echo "detail info of host $host_id:"
        daisy host-detail $host_id
    done
else
    for host_id in $hosts_id;
    do
        echo "update host $host_id ipmi user and passwd"
        daisy host-update $host_id --ipmi-user zteroot --ipmi-passwd superuser
    done
    echo "update all hosts ipmi user and passwd ok!"
fi

echo "check os installing progress..."
maxcount=180
count=0
while true; do
    if [ $count -gt $maxcount ]; then
        echo "It took too long to install the os, exit 1."
        exit 1
    fi
    count=$[count + 1]

    os_install_active=`daisy host-list --cluster-id $cluster_id | awk -F "|" '{print $8}' | grep -c "active" `
    os_install_failed=`daisy host-list --cluster-id $cluster_id | awk -F "|" '{print $8}' | grep -c "install-failed" `
    if [ $os_install_active -eq $hosts_num ]; then
        echo "os installing successful ..."
        break
    elif [ $os_install_failed -gt 0 ]; then
        echo "os installing have failed..."
        exit 1
    else
        progress=`daisy host-list --cluster-id $cluster_id |grep DISCOVERY_SUCCESSFUL |awk -F "|" '{print $7}'|sed s/[[:space:]]//g|sed ':a;N;$ s/\n/ /g;ba'`
        echo "os in installing, the progress of each node is $progress%"
        sleep 30
    fi
done
systemctl disable dhcpd
systemctl stop dhcpd
