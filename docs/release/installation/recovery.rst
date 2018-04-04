.. This work is licensed under a Creative Commons Attribution 4.0 International Licence.
.. http://creativecommons.org/licenses/by/4.0

Deployment Error Recovery Guide
===============================

Deployment may fail due to different kinds of reasons, such as Daisy VM creation
error, target nodes failure during OS installation, or Kolla deploy command
error. Different errors can be grouped into several error levels. We define
Recovery Levels below to fulfill recover requirements in different error levels.

1. Recovery Level 0
-------------------

This level restart whole deployment again. Mainly to retry to solve errors such
as Daisy VM creation failed. For example we use the following command to do
virtual deployment(in the jump host):


.. code-block:: console

    sudo ./ci/deploy/deploy.sh -b ./ -l zte -p virtual1 -s os-nosdn-nofeature-ha



If command failed because of Daisy VM creation error, then redoing above command
will restart whole deployment which includes rebuilding the daisy VM image and
restarting Daisy VM.


2. Recovery Level 1
-------------------

If Daisy VM was created successfully, but bugs were encountered in Daisy code
or software of target OS which prevent deployment from being done, in this case,
the user or the developer does not want to recreate the Daisy VM again during
next deployment process but just to modify some pieces of code in it. To achieve
this, he/she can redo deployment by deleting all clusters and hosts first(in the
Daisy VM):


.. code-block:: console

    source /root/daisyrc_admin
    for i in `daisy cluster-list | awk -F "|" '{print $2}' | sed -n '4p' | tr -d " "`;do daisy cluster-delete $i;done
    for i in `daisy host-list | awk -F "|" '{print $2}'| grep -o "[^ ]\+\( \+[^ ]\+\)*"|tail -n +2`;do daisy host-delete $i;done



Then, adjust deployment command as below and run it again(in the jump host):


.. code-block:: console

    sudo ./ci/deploy/deploy.sh -S -b ./ -l zte -p virtual1 -s os-nosdn-nofeature-ha



Pay attention to the "-S" argument above, it lets the deployment process to
skip re-creating Daisy VM and use the existing one.


3. Recovery Level 2
-------------------

If both Daisy VM and target node's OS are OK, but error ocurred when doing
OpenStack deployment, then there is even no need to re-install target OS for
the deployment retrying. In this level, all we need to do is just retry the
Daisy deployment command as follows(in the Daisy VM):


.. code-block:: console

    source /root/daisyrc_admin
    daisy uninstall <cluster-id>
    daisy install <cluster-id>



This basically does kolla-ansible destruction and kolla-asnible deployment.

4. Recovery Level 3
-------------------

If previous deployment was failed during kolla-ansible deploy(you can confirm
it by checking /var/log/daisy/api.log) or if previous deployment was successful
but the default configration is not what you want and it is OK for you to destroy
the OPNFV software stack and re-deploy it again, then you can try recovery level 3.

For example, in order to use external iSCSI storage, you are about to deploy
iSCSI cinder backend which is not enabled by default. First, cleanup the
previous deployment.

ssh into daisy node, then do:


.. code-block:: console

    [root@daisy daisy]# source /etc/kolla/admin-openrc.sh
    [root@daisy daisy]# openstack server delete <all vms you created>




Note: /etc/kolla/admin-openrc.sh may not have existed if previous
deployment was failed during kolla deploy.


.. code-block:: console

    [root@daisy daisy]# cd /home/kolla_install/kolla-ansible/
    [root@daisy kolla-ansible]# ./tools/kolla-ansible destroy \
    -i ./ansible/inventory/multinode --yes-i-really-really-mean-it




Then, edit /etc/kolla/globals.yml and append the follwoing line:


.. code-block:: console

    enable_cinder_backend_iscsi: "yes"
    enable_cinder_backend_lvm: "no"




Then, re-deploy again:


.. code-block:: console


    [root@daisy kolla-ansible]# ./tools/kolla-ansible prechecks -i ./ansible/inventory/multinode
    [root@daisy kolla-ansible]# ./tools/kolla-ansible deploy -i ./ansible/inventory/multinode




After successfully deploying, issue the following command to generate
/etc/kolla/admin-openrc.sh file.


.. code-block:: console


    [root@daisy kolla-ansible]# ./tools/kolla-ansible post-deploy -i ./ansible/inventory/multinode




Finally, issue the following command to create necessary resources, and your
environment are ready for running OPNFV functest.


.. code-block:: console


    [root@daisy kolla-ansible]# cd /home/daisy
    [root@daisy daisy]# ./deploy/post.sh -n /home/daisy/labs/zte/virtual1/daisy/config/network.yml




Note: "zte/virtual1" in above path may vary in your environment.
