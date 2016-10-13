#!/bin/bash

set -eux

function build_rpm_pkg {
      sudo docker build -t daisy4nfv_rpm .
      sudo docker run -v $WORKSPACE:/opt/daisy4nfv -t  daisy4nfv_rpm \
                      /opt/daisy4nfv/ci/build_rpm/build_rpms_docker.sh
    ;;
}

 build_rpm_pkg
