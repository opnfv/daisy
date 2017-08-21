.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0

CI job introduction
===================

1. CI base architech
--------------------

https://wiki.opnfv.org/display/INF/CI+Evolution

2. Project gating and daily deployment test
-------------------------------------------

To save time, currently, Daisy4NFV does not run deployment test in gate job which simply builds and
uploads artifacts to low confidence level repo. The project deployment test is triggered on a daily
basis. If the artifact passes the test, then it will be promoted to the high confidence level repo.

The low confidence level artifacts are bin files in http://artifacts.opnfv.org/daisy.html named like
"daisy/opnfv-Gerrit-39495.bin", while the high confidence level artifacts are named like
"daisy/opnfv-2017-08-20_08-00-04.bin".

The daily project deployment status can be found at

https://build.opnfv.org/ci/job/daisy-daily-master/

3. Production CI
----------------

The status of Daisy4NFV's CI/CD which running on OPNFV production CI environments(both B/M and VM)
can be found at

https://build.opnfv.org/ci/job/daisy-os-nosdn-nofeature-ha-baremetal-daily-master/
https://build.opnfv.org/ci/job/daisy-os-odl-nofeature-ha-baremetal-daily-master/
https://build.opnfv.org/ci/job/daisy-os-nosdn-nofeature-ha-virtual-daily-master/
https://build.opnfv.org/ci/job/daisy-os-odl-nofeature-ha-virtual-daily-master/

Dashboard for taking a glance on CI health status in a more intuitive way can be found at

http://testresults.opnfv.org/reporting/functest/release/master/index-status-daisy.html
