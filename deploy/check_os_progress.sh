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
cluster_id=`daisy cluster-list | awk -F "|" '{print $2}' | sed -n '4p'`
skip=false
if [ $deploy_env == 0 ];then
    skip=true
fi

echo "run daisy install command"
daisy install $cluster_id --skip-pxe-ipmi $skip

echo "check os installing progress..."
while true; do
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
        sleep 10
    fi
done
systemctl disable dhcpd
systemctl stop dhcpd
