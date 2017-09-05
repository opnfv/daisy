.. _daisy-build-kolla-image:

.. This document is protected/licensed under the following conditions
.. (c) Sun Jing (ZTE corporation)
.. Licensed under a Creative Commons Attribution 4.0 International License.
.. You should have received a copy of the license along with this work.
.. If not, see <http://creativecommons.org/licenses/by/4.0/>.

Build Your Own Kolla Image For Daisy
====================================

The following command will build Ocata Kolla image for Daisy based on
Daisy's fork of openstack/kolla project. This is also the method Daisy
used for the Euphrates release.

The reason why here use fork of openstack/kolla project is to backport
ODL support from pike branch to ocata branch.

.. code-block:: console

  cd ./ci
  ./kolla-build.sh



After building, the above command will put Kolla image into
/tmp/kolla-build-output directory and the image version will be 4.0.2.

If you want to build an image which can update 4.0.2, run the following
command:

.. code-block:: console

  cd ./ci
  ./kolla-build.sh -e 1


This time the image version will be 4.0.2.1 which is higher than 4.0.2
so that it can be used to replace the old version.
