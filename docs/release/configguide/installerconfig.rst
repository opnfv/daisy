
.. This document is protected/licensed under the following conditions
.. (c) Sun Jing (ZTE corporation)
.. Licensed under a Creative Commons Attribution 4.0 International License.
.. You should have received a copy of the license along with this work.
.. If not, see <http://creativecommons.org/licenses/by/4.0/>.


========
Abstract
========

This document compiles the release notes for the D 2.0 release of
OPNFV when using Daisy4nfv as a deployment tool.


Configuration Guide
===================

Before you install daisy on jumperserver,you have to configure the
daisy.conf file.Then put the right configured daisy.conf file in the
/home/daisy_install/ dir.

1、you have to supplement the "daisy_management_ip" section with the ip of
   management ip of your daisy-installed host.

2、Now the backend section "default_backend_types" just support the "kolla".

3、"os_install_type" section just support "pxe" for now.

4、Daisy now use pxe server to install the os,so "build_pxe" must set to "yes".
   If the daisy.conf in your env of /home/daisy_install/ dir is no,you must change
   this section to "yes" manually before installing Daisy.

5、"eth_name" section is the pxe server interface,and this section must set when
   the "build_pxe" section set to "yes".

6、"ip_address" section is the ip of pxe server interface.

7、"net_mask" section is the netmask of pxe server,which is required when the "build_pxe"
    is set to "yes"

8、"client_ip_begin" and "client_ip_end" section is the dhcp range of the pxe server.

9、If you want use the multicast type to deliver the kolla image to target node,
   set the "daisy_conf_mcast_enabled" section to "True"
