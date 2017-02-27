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
          - ha

      - name: host2
        roles:
          - compute

NOTE:
IF YOU SELECT MUTIPLE NODES AS CONTROLLER, THE 'ha' role MUST BE SELECTED, TOO.

E.g. OpenStack and ceph deployment roles setting

.. code-block:: yaml

    hosts:
      - name: host1
        roles:
          - controller
          - ha
          - ceph-adm
          - ceph-mon

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

                                    +--+
                                    |  |
                +------------+      |  |
                |  Jumphost  +------+  |
                +------------+      |  |
                                    |  |
                                    |  |
                                    |  |
                +------------+      |  |
       +--------+ Controller +------+  |
       |        +------------+      |  |
       |                            |  |
       |                            |  |
       |                            |  |
       |        +------------+      |  |
       |        |  Compute1  +------+  |
       |        +------------+      |  |
       |                            |  |
       |                            |  |
       |                            |  |
       |        +------------+      |  |
       |        |  Compute2  +------+  |
       |        +------------+      |  |
       |                            |  |
       |                            |  |
       |                            |  |
       |                            |  |
       |                            ++-+
       |                             ^
       |                             |
       |                             |
      ++--------------------------+  |
      |      External Network     |  |
      +---------------------------+  |
             +-----------------------+---+
             |    Installation Network   |
             |    Public/Private API     |
             |      Internet Access      |
             |      Tenant Network       |
             +---------------------------+


Start Deployment (Virtual Deployment)
-------------------------------------

TODO


