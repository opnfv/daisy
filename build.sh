cd /home/
mkdir daisy-dir
cd daisy-dir
git clone https://git.openstack.org/openstack/daisycloud-core
cd daisycloud-core/tools
./daisy-compile-rpm.sh

cd ..
cd make
make allrpm
echo "######################################################"
echo "          done              "
echo "######################################################"
