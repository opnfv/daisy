#!/bin/bash
##############################################################################
# Copyright (c) 2016 ZTE Coreporation and others.
# hu.zhijiang@zte.com.cn
# sun.jing22@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
set -eux
DAISYDIR=$1
OPNFV_ARTIFACT_VERSION=$2
function build_rpm_pkg {
    # Cleanup prev build resutls
    rm -rf $DAISYDIR/build_output
    mkdir -p $DAISYDIR/build_output

    sudo docker run --rm -t \
                    -v $DAISYDIR:/opt/daisy4nfv \
                    -v $CACHE_DIRECTORY:/home/cache \
                    /opt/daisy4nfv/ci/build_rpm/build_rpms_docker.sh \
                    --name daisy \
                    opnfv/daisy $OPNFV_ARTIFACT_VERSION
}

function cleanup_docker_image {
    [[ ! -z $(sudo docker images -q opnfv/daisy) ]] && sudo docker rmi opnfv/daisy
}

cleanup_docker_image
build_rpm_pkg
