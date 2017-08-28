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



If command failed because of Daisy VM creation error, then redo above command
will restart whole deployment which includes rebuild the daisy VM image and
restart Daisy VM.


2. Recovery Level 1
-------------------

If Daisy VM was created successfully, but bugs was encountered in Daisy code
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



This basically do kolla-ansible destroy and kolla-asnible deploy.
