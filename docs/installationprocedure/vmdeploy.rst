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
WE JUST SUPPORT ONE CONTROLLER NODE NOW.

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


    +------------+------------------------------+
    |Jumperserver+                              |
    +------------+                       +--+   |
    |                                    |  |   |
    |                +------------+      |  |   |
    |                | Daisyserver+------+  |   |
    |                +------------+      |  |   |
    |                                    |  |   |
    |                                    |  |   |
    |                                    |  |   |
    |                +------------+      |  |   |
    |       +--------+ Controller +------+  |   |
    |       |        +------------+      |  |   |
    |       |                            |  |   |
    |       |                            |  |   |
    |       |                            |  |   |
    |       |        +------------+      |  |   |
    |       |        |  Compute1  +------+  |   |
    |       |        +------------+      |  |   |
    |       |                            |  |   |
    |       |                            |  |   |
    |       |                            |  |   |
    |       |        +------------+      |  |   |
    |       |        |  Compute2  +------+  |   |
    |       |        +------------+      |  |   |
    |       |                            |  |   |
    |       |                            |  |   |
    |       |                            |  |   |
    |       |                            |  |   |
    |       |                            ++-+   |
    |       |                             ^     |
    |       |                             |     |
    |       |                             |     |
    |      ++--------------------------+  |     |
    |      |                           |  |     |
    |      |      External Network     |  |     |
    |      +---------------------------+  |     |
    |             +-----------------------+---+ |
    |             |    Installation Network   | |
    |             |    Public/Private API     | |
    |             |      Internet Access      | |
    |             |      Tenant Network       | |
    |             +---------------------------+ |
    +-------------------------------------------+



Start Deployment (Virtual Deployment)
-------------------------------------

(1) Git clone the latest daisy4nfv code from opnfv: "git clone https://gerrit.opnfv.org/gerrit/daisy"

(2) Download latest bin file(such as opnfv-2017-06-06_23-00-04.bin) of daisy from http://artifacts.opnfv.org/daisy.html and change the bin file name(such as opnfv-2017-06-06_23-00-04.bin) to opnfv.bin

(3) Make sure the opnfv.bin file is in daisy4nfv code dir

(4) Create folder of labs/zte/virtual1/daisy/config in daisy4nfv code dir

(5) Move the daisy/deploy/config/vm_environment/zte-virtual1/deploy.yml and daisy/deploy/config/vm_environment/zte-virtual1/network.yml to labs/zte/virtual1/daisy/config dir.
Notes:zte-virtual1 config file is just for all-in-one deployment,if you want to deploy openstack with five node(1 lb node and 4 computer nodes),change the zte-virtual1 to zte-virtual2

(6) Run the script deploy.sh in daisy/ci/deploy/ with command:
sudo ./ci/deploy/deploy.sh -b ../daisy  -l zte -p virtual1 -B pxebr -s os-nosdn-nofeature-noha

(7) When deploy successfully,the floating ip of openstack is 10.20.11.11,the login account is "admin" and the password is "keystone"
