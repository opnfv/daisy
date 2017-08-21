.. This work is licensed under a Creative Commons Attribution 4.0 International Licence.
.. http://creativecommons.org/licenses/by/4.0

Installation Guide (Virtual Deployment)
=======================================

Nodes Configuration (Virtual Deployment)
----------------------------------------

The below file is the inventory template of deployment nodes:

"./deploy/conf/vm_environment/zte-virtual1/deploy.yml"

You can write your own name/roles reference into it.

        - name -- Host name for deployment node after installation.

        - roles -- Components deployed.

**Set TYPE and FLAVOR**

E.g.

.. code-block:: yaml

    TYPE: virtual
    FLAVOR: cluster

**Assignment of different roles to servers**

E.g. OpenStack only deployment roles setting

.. code-block:: yaml

    hosts:
      - name: host1
        roles:
          - controller

      - name: host2
        roles:
          - compute

NOTE:
For B/M, Daisy uses MAC address defined in deploy.yml to map discovered nodes to node items definition in deploy.yml,
then assign role described by node item to the discovered nodes by name pattern.
Currently, controller01, controller02, and controller03 will be assigned with Controller role
while computer01, computer02, computer03, and computer04 will be assigned with Compute role.

NOTE:
For V/M, There is no MAC address defined in deploy.yml for each virtual machine. Instead, Daisy will fill that blank by getting MAC from "virsh dump-xml".

E.g. OpenStack and ceph deployment roles setting

.. code-block:: yaml

    hosts:
      - name: host1
        roles:
          - controller

      - name: host2
        roles:
          - compute

Network Configuration (Virtual Deployment)
------------------------------------------

Before deployment, there are some network configurations to be checked based
on your network topology. The default network configuration file for Daisy is
"daisy/deploy/config/vm_environment/zte-virtual1/network.yml".
You can write your own reference into it.

**The following figure shows the default network configuration.**

.. code-block:: console


    +-B/M--------+------------------------------+
    |Jumperserver+                              |
    +------------+                       +--+   |
    |                                    |  |   |
    |                +-V/M--------+      |  |   |
    |                | Daisyserver+------+  |   |
    |                +------------+      |  |   |
    |                                    |  |   |
    |     +--+                           |  |   |
    |     |  |       +-V/M--------+      |  |   |
    |     |  +-------+ Controller +------+  |   |
    |     |  |       | ODL(Opt.)  |      |  |   |
    |     |  |       | Network    |      |  |   |
    |     |  |       | Ceph1      |      |  |   |
    |     |  |       +------------+      |  |   |
    |     |  |                           |  |   |
    |     |  |                           |  |   |
    |     |  |                           |  |   |
    |     |  |       +-V/M--------+      |  |   |
    |     |  +-------+  Compute1  +------+  |   |
    |     |  |       |  Ceph2     |      |  |   |
    |     |  |       +------------+      |  |   |
    |     |  |                           |  |   |
    |     |  |                           |  |   |
    |     |  |                           |  |   |
    |     |  |       +-V/M--------+      |  |   |
    |     |  +-------+  Compute2  +------+  |   |
    |     |  |       |  Ceph3     |      |  |   |
    |     |  |       +------------+      |  |   |
    |     |  |                           |  |   |
    |     |  |                           |  |   |
    |     |  |                           |  |   |
    |     +--+                           +--+   |
    |       ^                             ^     |
    |       |                             |     |
    |       |                             |     |
    |      /---------------------------\  |     |
    |      |      External Network     |  |     |
    |      \---------------------------/  |     |
    |             /-----------------------+---\ |
    |             |    Installation Network   | |
    |             |    Public/Private API     | |
    |             |      Internet Access      | |
    |             |      Tenant Network       | |
    |             |     Storage Network       | |
    |             |     HeartBeat Network     | |
    |             \---------------------------/ |
    +-------------------------------------------+



Note:
For Flat External networks(which is used by default), a physical interface is needed on each compute node for ODL NetVirt recent versions.
HeartBeat network is selected,and if it is configured in network.yml,the keepalived interface will be the heartbeat interface.

Start Deployment (Virtual Deployment)
-------------------------------------

(1) Git clone the latest daisy4nfv code from opnfv: "git clone https://gerrit.opnfv.org/gerrit/daisy",
make sure the current branch is master

(2) Download latest bin file(such as opnfv-2017-06-06_23-00-04.bin) of daisy from
http://artifacts.opnfv.org/daisy.html and change the bin file name(such as opnfv-2017-06-06_23-00-04.bin)
to opnfv.bin. Check the https://build.opnfv.org/ci/job/daisy-os-odl-nofeature-ha-baremetal-daily-master/,
and if the 'snaps_health_check' of functest result is 'PASS',
you can use this verify-passed bin to deploy the openstack in your own environment

(3) Assumed cloned dir is $workdir, which laid out like below:
[root@daisyserver daisy]# ls
ci  code  deploy  docker  docs  INFO  LICENSE  requirements.txt  setup.py  templates  test-requirements.txt  tests  tools  tox.ini
Make sure the opnfv.bin file is in $workdir

(4) Enter into $workdir, Create folder of labs/zte/virtual1/daisy/config in $workdir

(5) Move the deploy/config/vm_environment/zte-virtual1/deploy.yml and
deploy/config/vm_environment/zte-virtual1/network.yml to
labs/zte/virtual1/daisy/config dir.

Note:
zte-virtual1 config file deploy openstack with five nodes(3 lb nodes and 2 computer nodes),
if you want to deploy an all-in-one openstack, change the zte-virtual1 to zte-virtual2

Note:
If selinux is disabled on the host, please delete all xml files section of below lines in dir templates/virtual_environment/vms/
  <seclabel type='dynamic' model='selinux' relabel='yes'>
    <label>system_u:system_r:svirt_t:s0:c182,c195</label>
    <imagelabel>system_u:object_r:svirt_image_t:s0:c182,c195</imagelabel>
  </seclabel>

(6) Run the script deploy.sh in daisy/ci/deploy/ with command:
sudo ./ci/deploy/deploy.sh -b ./ -l zte -p virtual1 -s os-nosdn-nofeature-ha

Note:
The value after -p parameter(virtual1) is get from labs/zte/virtual1/daisy/config/
The value after -l parameter(zte) is get from labs/
The value after -s "os-nosdn-nofeature-ha" used for deploy multinode openstack
The value after -s "os-nosdn-nofeature-noha" used for deploy all-in-one openstack

(7) When deploy successfully,the floating ip of openstack is 10.20.11.11,
the login account is "admin" and the password is "keystone"
