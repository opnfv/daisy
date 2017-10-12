.. This work is licensed under a Creative Commons Attribution 4.0 International Licence.
.. http://creativecommons.org/licenses/by/4.0

Deployment Test Guide
===============================

After successfully deployed openstack, daisy4nfv use Functest to test the api of openstack.
You can follow below instruction to test the successfully deployed openstack on jumperserver.

1.docker pull opnfv/functest
run 'docker images' command to make sure have the latest functest images. 

2.docker run -ti --name functest -e INSTALLER_TYPE="daisy" -e INSTALLER_IP="10.20.11.2" -e NODE_NAME="zte-vtest" -e DEPLOY_SCENARIO="os-nosdn-nofeature-ha" -e BUILD_TAG="jenkins-functest-daisy-virtual-daily-master-1259" -e DEPLOY_TYPE="virt" opnfv/functest:latest  /bin/bash
Before run above command change below parameters:
DEPLOY_SCENARIO: indicate the scenario
DEPLOY_TYPE: virt/baremetal
NODE_NAME: pod name
INSTALLER_IP: daisy vm node ip

3.Log in the daisy vm node to get the /etc/kolla/admin-openrc.sh file, and write them in /home/opnfv/functest/conf/openstack.creds file of functest container.

4.Run command 'functest env prepare' to prepare the functest env.

5.Run command 'functest testcase list' to list all the testcase can run.

6.Run command 'functest testcase run testcase_name' to run the testcase_name testcase of functest.
