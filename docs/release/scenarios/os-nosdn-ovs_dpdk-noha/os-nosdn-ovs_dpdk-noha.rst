.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0

This document provides scenario level details for Fraser 1.0 of
deployment with no SDN controller and DPDK enabled Open vSwitch by using
Daisy installer.

Introduction
============

NFV and virtualized high performance applications, such as video processing,
require Open vSwitch to be accelerated with a fast data plane solution that
provides both carrier grade forwarding performance, scalability and open
extensibility.

A key component of any NFV solution is the virtual forwarder, which should
consist of soft switch that includes an accelerated data plane component. For
this, any virtual switch should make use of hardware accelerators and optimized
cache operation to be run in user space.

Scenario components and composition
===================================

This scenario enables high performance data plan acceleration by utilizing
DPDK enabled Open vSwitch (OVS).  This allows packet switching to be isolated
to particular hardware resources (CPUs, huge page memory allocation) without
kernel interrupt or context switching on the data plane CPU.

Both tenant tunnel and external physnet1 leverage Open vSwitch accelerated
with a fast user space data path, while other network planes are performed
via non-accelerated OVS.

Scenario Configuration
======================

Due to the performance optimization done by this scenario, it is recommended to
set some performance settings in the deploy settings in order to ensure maximum
performance.  This is not necessary unless doing a baremetal deployment.  Note,
this scenario requires taking the NIC mapped to the tenant and external network
on the compute node and binding them to DPDK.  This means it will no longer be
accessible via the kernel.  Ensure the NIC supports DPDK.

40 huge pages of 1G size are allocaled on each compute and network node for DPDK
and VMs by default and currently this can not be re-configured by using
configure files.

For each compute and network node, One CPU core of each NUMA is dedicatedly
allocated for DPDK by default and currently this can not be re-configured by using
configure files. 

Deploy this scenario by using the '-s os-nosdn-ovs_dpdk-noha' parameter among
others when calling ./ci/deploy/deploy.sh.

References
==========

For more information on the OPNFV Fraser release, please visit
http://www.opnfv.org/fraser
