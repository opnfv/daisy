.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0

This document provides scenario level details for Fraser 1.0 of
deployment with the OpenDaylight SDN controller and no extra features enabled.

============
Introduction
============

This scenario is used primarily to validate and deploy a Pike OpenStack
deployment with OpenDaylight, and without any NFV features enabled.

Scenario components and composition
===================================

This scenario is composed of common OpenStack services enabled by default,
including Nova, Neutron, Glance, Cinder, Keystone, Horizon. Ceph is used as
the backend storage to Cinder, Glance and Nova on all deployed nodes.

All services are in HA, meaning that there are multiple cloned instances of
each service, and they are balanced by HA Proxy using a Virtual IP Address
per service. VIP is elected by using keepalived.

OpenDaylight is also enabled in HA, and forms a cluster.  Neutron
communicates with a Virtual IP Address for OpenDaylight which is load
balanced across the OpenDaylight cluster.  Every Open vSwitch node is
connected to every OpenDaylight for High Availability, thus it is the
OpenDaylight controllers responsbility to elect a master.

Scenario usage overview
=======================

Simply deploy this scenario by using the '-s os-odl-nofeature-ha'
parameter among others when calling ./ci/deploy/deploy.sh.

References
==========

For more information on the OPNFV Fraser release, please visit
http://www.opnfv.org/fraser
