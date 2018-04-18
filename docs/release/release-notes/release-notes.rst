
.. This document is protected/licensed under the following conditions
.. (c) Sun Jing (ZTE corporation)
.. Licensed under a Creative Commons Attribution 4.0 International License.
.. You should have received a copy of the license along with this work.
.. If not, see <http://creativecommons.org/licenses/by/4.0/>.


========
Abstract
========

This document covers features, limitations and required system resources for the
OPNFV Fraser release when using Daisy4nfv as a deployment tool.

Introduction
============

Daisy4nfv is an OPNFV installer project based on open source project Daisycloud-core,
which provides containerized deployment and management of OpenStack and other distributed systems such as OpenDaylight.

Release Data
============

+--------------------------------------+--------------------------------------+
| **Project**                          | Daisy4nfv                            |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Repo/tag**                         | daisy/opnfv-6.0                      |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Release designation**              | opnfv-6.0                            |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Release date**                     |                                      |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Purpose of the delivery**          | OPNFV Fraser release                 |
|                                      |                                      |
+--------------------------------------+--------------------------------------+

Deliverables
------------

Software deliverables
~~~~~~~~~~~~~~~~~~~~~

 - Daisy4NFV/opnfv-6.0 ISO, please get it from `OPNFV software download page <https://www.opnfv.org/software/>`_

.. _document-label:

Documentation deliverables
~~~~~~~~~~~~~~~~~~~~~~~~~~

 - OPNFV(Fraser) Daisy4nfv installation instructions

 - OPNFV(Fraser) Daisy4nfv Release Notes

Version change
--------------
.. This section describes the changes made since the last version of this document.

Module version change
~~~~~~~~~~~~~~~~~~~~~

This is the Fraser release of Daisy4nfv as a deployment toolchain in OPNFV, the following
upstream components supported with this release.

 - Centos 7.4

 - Openstack (Pike release)

 - Opendaylight (Carbon SR3)

Reason for new version
----------------------

Feature additions
~~~~~~~~~~~~~~~~~

+--------------------------------------+-----------------------------------------+
| **JIRA REFERENCE**                   | **SLOGAN**                              |
|                                      |                                         |
+--------------------------------------+-----------------------------------------+
|                                      | Support OpenDayLight Carbon SR3         |
|                                      |                                         |
+--------------------------------------+-----------------------------------------+
|                                      | Support OpenStack Pike                  |
|                                      |                                         |
+--------------------------------------+-----------------------------------------+
|                                      | Support OVS+DPDK                        |
|                                      |                                         |
+--------------------------------------+-----------------------------------------+



Bug corrections
~~~~~~~~~~~~~~~

**JIRA TICKETS:**

+--------------------------------------+--------------------------------------+
| **JIRA REFERENCE**                   | **SLOGAN**                           |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
|                                      |                                      |
|                                      |                                      |
+--------------------------------------+--------------------------------------+


Known Limitations, Issues and Workarounds
=========================================

System Limitations
------------------

**Max number of blades:** 1 Jumphost, 3 Controllers, 20 Compute blades

**Min number of blades:** 1 Jumphost, 1 Controller, 1 Compute blade

**Storage:** Ceph is the only supported storage configuration

**Min Jumphost requirements:** At least 16GB of RAM, 16 core CPU

Known issues
------------

+----------------------+-------------------------------+-----------------------+
|   **Scenario**       | **Issue**                     |  **Workarounds**      |
+----------------------+-------------------------------+-----------------------+
|                      |                               |                       |
|                      |                               |                       |
+----------------------+-------------------------------+-----------------------+
|                      |                               |                       |
|                      |                               |                       |
+----------------------+-------------------------------+-----------------------+


Test Result
===========
TODO

