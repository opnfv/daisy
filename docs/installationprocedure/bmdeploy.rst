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
WE JUST SUPPORT ONE CONTROLLER NODE NOW.

Network Configuration (Virtual Deployment)
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
                  \---------------------------/




Note: For Flat External networks(which is used by default), a physical interface is needed on each compute node for ODL NetVirt recent versions.

Start Deployment (Bare Metal Deployment)
----------------------------------------

(1) Git clone the latest daisy4nfv code from opnfv: "git clone https://gerrit.opnfv.org/gerrit/daisy"

(2) Download latest bin file(such as opnfv-2017-06-06_23-00-04.bin) of daisy from http://artifacts.opnfv.org/daisy.html and change the bin file name(such as opnfv-2017-06-06_23-00-04.bin) to opnfv.bin

(3) Make sure the opnfv.bin file is in daisy4nfv code dir

(4) Create folder of labs/zte/baremetal1/daisy/config in daisy4nfv code dir

(5) Move the ./deploy/config/bm_environment/zte-baremetal1/deploy.yml and ./deploy/config/bm_environment/zte-baremetal1/network.yml to labs/zte/baremetal1/daisy/config dir.

(6) Run the script deploy.sh in daisy/ci/deploy/ with command:
sudo ./ci/deploy/deploy.sh -b ../daisy  -l zte -p virtual1 -B pxebr

(7) When deploy successfully,the floating ip of openstack is 10.20.11.11,the login account is "admin" and the password is "keystone"
