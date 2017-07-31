.. This work is licensed under a Creative Commons Attribution 4.0 International Licence.
.. http://creativecommons.org/licenses/by/4.0

Installation Guide (Bare Metal Deployment)
==========================================

Nodes Configuration (Bare Metal Deployment)
-------------------------------------------

The below file is the inventory template of deployment nodes:

"./deploy/config/bm_environment/zte-baremetal1/deploy.yml"

You can write your own name/roles reference into it.

        - name -- Host name for deployment node after installation.

        - roles -- Components deployed. CONTROLLER_LB is for Controller,
COMPUTER is for Compute role. Currently only these two role is supported.
The first CONTROLLER_LB is also used for ODL controller. 3 hosts in
inventory will be chosen to setup the Ceph storage cluster.

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
          - CONTROLLER_LB
      - name: host2
        roles:
          - COMPUTER
      - name: host3
        roles:
          - COMPUTER


NOTE:
For B/M, Daisy uses MAC address defined in deploy.yml to map discovered nodes to node items definition in deploy.yml, then assign role described by node item to the discovered nodes by name pattern. Currently, controller01, controller02, and controller03 will be assigned with Controler role while computer01, 'computer02, computer03, and computer04 will be assigned with Compute role.

NOTE:
For V/M, There is no MAC address defined in deploy.yml for each virtual machine. Instead, Daisy will fill that blank by getting MAC from "virsh dump-xml".


Network Configuration (Bare Metal Deployment)
------------------------------------------

Before deployment, there are some network configurations to be checked based
on your network topology. The default network configuration file for Daisy is
"./deploy/config/bm_environment/zte-baremetal1/network.yml".
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
    +------------------------------------|  |---+
                                         |  |
                                         |  |
          +--+                           |  |
          |  |       +-B/M--------+      |  |
          |  +-------+ Controller +------+  |
          |  |       | ODL(Opt.)  |      |  |
          |  |       | Network    |      |  |
          |  |       | CephOSD1   |      |  |
          |  |       +------------+      |  |
          |  |                           |  |
          |  |                           |  |
          |  |                           |  |
          |  |       +-B/M--------+      |  |
          |  +-------+  Compute1  +------+  |
          |  |       |  CephOSD2  |      |  |
          |  |       +------------+      |  |
          |  |                           |  |
          |  |                           |  |
          |  |                           |  |
          |  |       +-B/M--------+      |  |
          |  +-------+  Compute2  +------+  |
          |  |       |  CephOSD3  |      |  |
          |  |       +------------+      |  |
          |  |                           |  |
          |  |                           |  |
          |  |                           |  |
          +--+                           +--+
            ^                             ^
            |                             |
            |                             |
           /---------------------------\  |
           |      External Network     |  |
           \---------------------------/  |
                  /-----------------------+---\
                  |    Installation Network   |
                  |    Public/Private API     |
                  |      Internet Access      |
                  |      Tenant Network       |
                  |     Storage Network       |
                  |     HeartBeat Network     |
                  \---------------------------/




Note:
For Flat External networks(which is used by default), a physical interface is needed on each compute node for ODL NetVirt recent versions.
HeartBeat network is selected,and if it is configured in network.yml,the keepalived interface will be the heartbeat interface.

Start Deployment (Bare Metal Deployment)
----------------------------------------

(1) Git clone the latest daisy4nfv code from opnfv: "git clone https://gerrit.opnfv.org/gerrit/daisy"

(2) Download latest bin file(such as opnfv-2017-06-06_23-00-04.bin) of daisy from http://artifacts.opnfv.org/daisy.html and change the bin file name(such as opnfv-2017-06-06_23-00-04.bin) to opnfv.bin

(3) Make sure the opnfv.bin file is in daisy4nfv code dir

(4) Create folder of labs/zte/pod2/daisy/config in daisy4nfv code dir

(5) Move the ./deploy/config/bm_environment/zte-baremetal1/deploy.yml and ./deploy/config/bm_environment/zte-baremetal1/network.yml to labs/zte/pod2/daisy/config dir.

(6) Config the bridge in jumperserver,make sure the daisy vm can connect to the targetnode,use the command below:
brctl addbr br7
brctl addif br7 enp3s0f3(the interface for jumperserver to connect to daisy vm)
ifconfig br7 10.20.7.1 netmask 255.255.255.0 up
service network restart

(7) Run the script deploy.sh in daisy/ci/deploy/ with command:
sudo ./ci/deploy/deploy.sh -b ../daisy  -l zte -p pod2 -s os-nosdn-nofeature-noha

(8) When deploy successfully,the floating ip of openstack is 10.20.7.11,the login account is "admin" and the password is "keystone"
