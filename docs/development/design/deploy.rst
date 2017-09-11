.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0

Deployment Steps
================

This document takes VM all-in-one environment as example to show what ci/deploy/deploy.sh
really do.

1. On jump host, clean up all-in-one vm and networks.

2. On jump host, clean up daisy vm and networks.

3. On jump host, create and start daisy vm and networks.

4. In daisy vm, Install daisy artifact.

5. In daisy vm, config daisy and OpenStack default options.

6. In daisy vm, create cluster, update network and build PXE server for the bootstrap
kernel. In short, be ready for discovering target nodes. These tasks are done by running
the following command.

python /home/daisy/deploy/tempest.py --dha /home/daisy/labs/zte/virtual1/daisy/config/deploy.yml --network /home/daisy/labs/zte/virtual1/daisy/config/network.yml --cluster 'yes'

7. On jump host, create and start all-in-one vm and networks.

8. On jump host, after all-in-one vm is up, get its mac address and write into /home/daisy/labs/zte/virtual1/daisy/config/deploy.yml.

9. In daisy vm, check if all-in-one vm was discovered, if it was, then update its network
assignment and config OpenStack according to OPNFV scenario and setup PXE for OS
installaion. These tasks are done by running the following command.
 
python /home/daisy/deploy/tempest.py --dha /home/daisy/labs/zte/virtual1/daisy/config/deploy.yml --network /home/daisy/labs/zte/virtual1/daisy/config/network.yml --host yes --isbare 0 --scenario os-nosdn-nofeature-noha

Note: Current host status:
os_status is "init".

10. On jump host, restart all_in_one vm to install OS.

11. In daisy vm, continue to intall OS by running the following command which for VM
environment only.

python /home/daisy/deploy/tempest.py --dha /home/daisy/labs/zte/virtual1/daisy/config/deploy.yml --network /home/daisy/labs/zte/virtual1/daisy/config/network.yml --install 'yes'

12. In daisy vm, run the following command to check OS intallation progress.
/home/daisy/deploy/check_os_progress.sh -d 0 -n 1

Note: Current host status:
os_status is "installing" during installation, then os_status becomes "active" after OS
was succesfully installed.

13. On jump host, reboot all-in-one vm again to get a fresh and first booted OS.

14. In daisy vm, run the following command to check OpenStack/ODL/... intallation
progress.

/home/daisy/deploy/check_openstack_progress.sh -n 1
