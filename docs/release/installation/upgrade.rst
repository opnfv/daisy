.. This work is licensed under a Creative Commons Attribution 4.0 International Licence.
.. http://creativecommons.org/licenses/by/4.0

OpenStack Minor Version Update Guide
====================================

Thanks for the Kolla's kolla-ansible upgrade function, Daisy enable to
update OpenStack minor version as the follows:

1. Get new version file only from Daisy team.
Since Daisy's Kolla images are build by meeting the OPNFV requirements
and have their own file packaging layout, Daisy requires user to
always use Kolla image file built by Daisy team. Currently, it can be
got from http://120.24.17.215/.

2. Put new version file into /var/lib/daisy/kolla/, for example,
/var/lib/daisy/kolla/kolla-image-ocata-170811155446.tgz

3. Add version file to Daisy's version management database then get the
version ID.


.. code-block:: console

    [root@daisy ~]# daisy version-add kolla-image-ocata-170811155446.tgz kolla
    +-------------+--------------------------------------+
    | Property    | Value                                |
    +-------------+--------------------------------------+
    | checksum    | None                                 |
    | created_at  | 2017-08-28T06:45:25.000000           |
    | description | None                                 |
    | id          | 8be92587-34d7-43e8-9862-a5288c651079 |
    | name        | kolla-image-ocata-170811155446.tgz   |
    | owner       | None                                 |
    | size        | 0                                    |
    | status      | unused                               |
    | target_id   | None                                 |
    | type        | kolla                                |
    | updated_at  | 2017-08-28T06:45:25.000000           |
    | version     | None                                 |
    +-------------+--------------------------------------+



4. Get cluster ID


.. code-block:: console

    [root@daisy ~]# daisy cluster-list
    +--------------------------------------+-------------+...
    | ID                                   | Name        |...
    +--------------------------------------+-------------+...
    | d4c1e0d3-c4b8-4745-aab0-0510e62f0ebb | clustertest |...
    +--------------------------------------+-------------+...



5. Issuing update command passing cluster ID and version ID



.. code-block:: console

    [root@daisy ~]# daisy update d4c1e0d3-c4b8-4745-aab0-0510e62f0ebb --update-object kolla --version-id 8be92587-34d7-43e8-9862-a5288c651079
    +----------+--------------+
    | Property | Value        |
    +----------+--------------+
    | status   | begin update |
    +----------+--------------+


6. Since step 5's command is non-blocking, the user need to run the
following command to get updating progress.



.. code-block:: console

    [root@daisy ~]# daisy host-list --cluster-id d4c1e0d3-c4b8-4745-aab0-0510e62f0ebb
    ...+---------------+-------------+-------------------------+
    ...| Role_progress | Role_status | Role_messages           |
    ...+---------------+-------------+-------------------------+
    ...| 0             | updating    | prechecking envirnoment |
    ...+---------------+-------------+-------------------------+



Notes. The above command returns many fields. User only have to take care
about the Role_xxx fields in this case.
