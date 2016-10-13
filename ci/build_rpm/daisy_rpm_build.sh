
#!/bin/bash

output_dir = "$1"

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

    mkdir daisy-dir
    cd daisy-dir
    git clone https://git.openstack.org/openstack/daisycloud-core
    cd daisycloud-core/tools
    make allrpm

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
cd daisy-dir
mv daisycloud-core/target/el7/noarch/installdaisy_el7_noarch.bin output_dir
exit $rc
