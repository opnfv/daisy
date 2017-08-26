
.. This document is protected/licensed under the following conditions
.. (c) Sun Jing (ZTE corporation)
.. Licensed under a Creative Commons Attribution 4.0 International License.
.. You should have received a copy of the license along with this work.
.. If not, see <http://creativecommons.org/licenses/by/4.0/>.


========
Abstract
========

This document compiles the release notes for the D 2.0 release of
OPNFV when using Daisy as a deployment tool.


Configuration Guide
===================

Before installing Daisy4NFV on jump server,you have to configure the
daisy.conf file.Then put the right configured daisy.conf file in the
/home/daisy_install/ dir.

1. you have to supplement the "daisy_management_ip" field with the ip of
   management ip of your Daisy server vm.

2. Now the backend field "default_backend_types" just support the "kolla".

3. "os_install_type" field just support "pxe" for now.

4. Daisy now use pxe server to install the os, if "build_pxe" set to "yes", before
   install the os, daisy will build a pxe server, which will delete after install
   the os for each target node. Suggest to set the "build_pxe" item to "no", and use
   tempest.py file to build pxe server, which can rebuild pxe server without reinstall
   daisy. If the section is set to "no", tempest.py file will only read the "eth_name"
   section and use this interface to build pxe server.

5. "eth_name" field is the pxe server interface, and this field is required when
   the "build_pxe" field set to "yes".This should be set to the interface
   (in Daisy Server VM) which will be used for communicating with other target nodes
   on management/PXE net plane. Default is ens3.

6. "ip_address" field is the ip address of pxe server interface.

7. "net_mask" field is the netmask of pxe server,which is required when the "build_pxe"
   is set to "yes"

8. "client_ip_begin" and "client_ip_end" field are the dhcp range of the pxe server.

9. If you want to use the multicast type to deliver the kolla image to target node,
   set the "daisy_conf_mcast_enabled" field to "True"
