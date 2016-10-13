#!/bin/bash

function usage() {
    echo ""
    echo "Usage: "
    echo "  package_type : centos only now ;"
    echo "  output: rpm packages"
    echo ""
}

cd ci/build_rpm
./build_rpms.sh
cd $WORKSPACE

