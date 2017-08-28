
.. This document is protected/licensed under the following conditions
.. (c) Sun Jing (ZTE corporation)
.. Licensed under a Creative Commons Attribution 4.0 International License.
.. You should have received a copy of the license along with this work.
.. If not, see <http://creativecommons.org/licenses/by/4.0/>.


OpenStack Configuration Guide
=============================

Before Deployment
-----------------

When executing deploy.sh, before doing real deployment, Daisy utilizes
Kolla's service configuration functionality [1] to specify the following
changes to the default OpenStack configuration which comes from Kolla as
default.

a) If is it is a VM deployment, set virt_type=qemu amd cpu_mode=none for
nova-compute.conf.

b) In nova-api.conf set default_floating_pool to the name of the external
network which will be created by Daisy after deployment for nova-api.conf.

c) In heat-api.conf and heat-engine.conf, set deferred_auth_method to
trusts and unset trusts_delegated_roles.

Those above changes are requirements of OPNFV or environment's
constraints.  So it is not recommended to change them. But if the user
wants to add more specific configurations to OpenStack services before
doing real deployment, we suggest to do it in the same way as deploy.sh
do. Currently, this means hacking into deploy/prepare.sh or
deploy/prepare/execute.py then add config file as described in [1].


After Deployment
----------------

After deployment of OpenStack, its configurations can also be changed
and applied by using Kolla's service configuration functionality [1]. But
user has to issue Kolla's command to do it in this release:


.. code-block:: console
    cd /home/kolla_install/kolla-ansible/
    ./tools/kolla-ansible reconfigure -i /home/kolla_install/kolla-ansible/ansible/inventory/multinode



[1] https://docs.openstack.org/kolla-ansible/latest/advanced-configuration.html#openstack-service-configuration-in-kolla
