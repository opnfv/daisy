.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0

This document provides scenario level details for Fraser 1.0 of
deployment with no SDN controller and no extra features enabled by using
Daisy installer.

============
Introduction
============

This scenario is used primarily to validate and deploy a Pike OpenStack
deployment without any NFV features or SDN controller enabled.

Scenario components and composition
===================================

This scenario is composed of common OpenStack services enabled by default,
including Nova, Neutron, Glance, Cinder, Keystone, Horizon. Ceph is used as
the backend storage to Cinder, Glance and Nova on all deployed nodes.

All services are in HA, meaning that there are multiple cloned instances of
each service, and they are balanced by HA Proxy using a Virtual IP Address
per service. VIP is elected by using keepalived.

Scenario usage overview
=======================

Simply deploy this scenario by using the '-s os-nosdn-nofeature-ha'
parameter among others when calling ./ci/deploy/deploy.sh.

Limitations, Issues and Workarounds
===================================

None

References
==========

For more information on the OPNFV Fraser release, please visit
http://www.opnfv.org/fraser
