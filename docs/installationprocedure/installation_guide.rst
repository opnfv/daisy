.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0

Daisy4nfv configuration
=======================

This document provides guidelines on how to install and configure the Danube
release of OPNFV when using Daisy as a deployment tool including required
software and hardware configurations.

Installation and configuration of host OS, OpenStack etc. can be supported by
Daisy on Virtual nodes and Bare Metal nodes.

The audience of this document is assumed to have good knowledge in
networking and Unix/Linux administration.

Prerequisites
-------------

Before starting the installation of the Danube release of OPNFV, some plannings
must be done.


Retrieving the installation bin image
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First of all, the installation bin which includes packages of Daisy, OS,
OpenStack, and so on is needed for deploying your OPNFV environment.

The stable release bin image can be retrieved via `OPNFV software download page <https://www.opnfv.org/software>`_

The daily build bin image can be retrieved via OPNFV artifacts repository:

http://artifacts.opnfv.org/daisy.html

NOTE: Search the keyword "daisy/Danube" to locate the bin image.

E.g.
daisy/opnfv-gerrit-27155.bin

The git url and sha1 of bin image are recorded in properties files.
According to these, the corresponding deployment scripts can be retrieved.


Retrieve the deployment scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To retrieve the repository of Daisy on Jumphost use the following command:

- git clone https://gerrit.opnfv.org/gerrit/daisy

To get stable Danube release, you can use the following command:

- git checkout danube.1.0


Setup Requirements
------------------

If you have only 1 Bare Metal server, Virtual deployment is recommended. if you have more
than 3 servers, the Bare Metal deployment is recommended. The minimum number of
servers for each role in Bare metal deployment is listed below.

+------------+------------------------+
| **Role**   | **Number of Servers**  |
|            |                        |
+------------+------------------------+
| Jump Host  | 1                      |
|            |                        |
+------------+------------------------+
| Controller | 1                      |
|            |                        |
+------------+------------------------+
| Compute    | 1                      |
|            |                        |
+------------+------------------------+


Jumphost Requirements
~~~~~~~~~~~~~~~~~~~~~

The Jumphost requirements are outlined below:

1.     CentOS 7.2 (Pre-installed).

2.     Root access.

3.     Libvirt virtualization support(For virtual deployment).

4.     Minimum 1 NIC(or 2 NICs for virtual deployment).

       -  PXE installation Network (Receiving PXE request from nodes and providing OS provisioning)

       -  IPMI Network (Nodes power control and set boot PXE first via IPMI interface)

       -  Internet access (For getting latest OS updates)

       -  External Interface(For virtual deployment, exclusively used by instance traffic to access the rest of the Internet)

5.     16 GB of RAM for a Bare Metal deployment, 64 GB of RAM for a Virtual deployment.

6.     CPU cores: 32, Memory: 64 GB, Hard Disk: 500 GB, (Virtual deployment needs 1 TB Hard Disk)


Bare Metal Node Requirements
----------------------------

Bare Metal nodes require:

1.     IPMI enabled on OOB interface for power control.

2.     BIOS boot priority should be PXE first then local hard disk.

3.     Minimum 1 NIC for Compute nodes, 2 NICs for Controller nodes.

       -  PXE installation Network (Broadcasting PXE request)

       -  IPMI Network (Receiving IPMI command from Jumphost)

       -  Internet access (For getting latest OS updates)

       -  External Interface(For virtual deployment, exclusively used by instance traffic to access the rest of the Internet)




Network Requirements
--------------------

Network requirements include:

1.     No DHCP or TFTP server running on networks used by OPNFV.

2.     2-7 separate networks with connectivity between Jumphost and nodes.

       -  PXE installation Network

       -  IPMI Network

       -  Internet access Network

       -  OpenStack Public API Network

       -  OpenStack Private API Network

       -  OpenStack External Network

       -  OpenStack Tenant Network(currently, VxLAN only)


3.     Lights out OOB network access from Jumphost with IPMI node enabled (Bare Metal deployment only).

4.     Internet access Network has Internet access, meaning a gateway and DNS availability.

5.     OpenStack External Network has Internet access too if you want instances to access the Internet.

Note: **All networks except OpenStack External Network can share one NIC(Default configuration) or use an exclusive**
**NIC(Reconfigurated in network.yml).**


Execution Requirements (Bare Metal Only)
----------------------------------------

In order to execute a deployment, one must gather the following information:

1.     IPMI IP addresses of the nodes.

2.     IPMI login information for the nodes (user/password).
