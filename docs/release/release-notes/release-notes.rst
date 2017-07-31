
.. This document is protected/licensed under the following conditions
.. (c) Sun Jing (ZTE corporation)
.. Licensed under a Creative Commons Attribution 4.0 International License.
.. You should have received a copy of the license along with this work.
.. If not, see <http://creativecommons.org/licenses/by/4.0/>.


========
Abstract
========

This document covers features, limitations and required system resources of
OPNFV E 1.0 release when using Daisy4nfv as a deployment tool.

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
| **Repo/tag**                         | Daisy4nfv/Euphrates.1.0              |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Release designation**              | Euphrates.1.0                        |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Release date**                     |                                      |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Purpose of the delivery**          | OPNFV Euphrates release              |
|                                      |                                      |
+--------------------------------------+--------------------------------------+

Deliverables
------------

Software deliverables
~~~~~~~~~~~~~~~~~~~~~

 - Daisy4nfv/Euphrates.1.0 ISO, please get it from `OPNFV software download page <https://www.opnfv.org/software/>`_

.. _document-label:

Documentation deliverables
~~~~~~~~~~~~~~~~~~~~~~~~~~

 - OPNFV(Danube) Daisy4nfv installation instructions

 - OPNFV(Danube) Daisy4nfv Release Notes

Version change
--------------
.. This section describes the changes made since the last version of this document.

Module version change
~~~~~~~~~~~~~~~~~~~~~

This is the Euphrates release of Daisy4nfv as a deployment toolchain in OPNFV, the following
upstream components supported with this release.

 - Centos 7.3

 - Openstack (Ocata release)

 - Opendaylight (Carbon release)

Reason for new version
----------------------

Feature additions
~~~~~~~~~~~~~~~~~

+--------------------------------------+-----------------------------------------+
| **JIRA REFERENCE**                   | **SLOGAN**                              |
|                                      |                                         |
+--------------------------------------+-----------------------------------------+
|                                      | Support OpenDayLight Carbon             |
|                                      |                                         |
+--------------------------------------+-----------------------------------------+
|                                      | Support OpenStack Ocata                 |
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
|                      |                               |                       |
+----------------------+-------------------------------+-----------------------+
|  All HA scenario     | Occasionally lose VIP         | Failed in testcase,   |
|                      |                               | normal in usage       |
+----------------------+-------------------------------+-----------------------+


Test Result
===========
TODO

