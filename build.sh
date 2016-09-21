#!/bin/bash

echo "#########################################################"
echo "               systemctl info:                   "
echo "#########################################################"
echo "###Uname:"
uname
echo "###Hostname:"
hostname


maxcount=3
cnt=0
rc=1
while [ $cnt -lt $maxcount ] && [ $rc -ne 0 ]
do
    cnt=$[cnt + 1]
    echo -e "\n\n\n*** Starting build attempt # $cnt"

    cd $WORKSPACE
    mkdir daisy-dir
    cd daisy-dir
    git clone https://git.openstack.org/openstack/daisycloud-core
    cd daisycloud-core/tools

    echo "######################################################"
    echo "          done              "
    echo "######################################################"
    rc=$?
    if [ $rc -ne 0 ]; then
        echo "### Build failed with rc $rc ###"
    else
        echo "### Build successful at attempt # $cnt"
    fi
done
exit $rc

