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
                    --name daisy opnfv/daisy \
                    /opt/daisy4nfv/ci/build_rpm/build_rpms_docker.sh \
                    $OPNFV_ARTIFACT_VERSION
}

function cleanup_container {
    echo "Cleaning daisy container"
    containers_to_kill=$(sudo docker ps --filter "name=daisy" \
        --format "{{.Names}}" -a)

    if [[ ! -z "$containers_to_kill" ]]; then
        volumes_to_remove=$(sudo docker inspect -f \
            '{{range .Mounts}} {{printf "%s\n" .Name }}{{end}}' \
            ${containers_to_kill} | egrep -v '(^\s*$)' | sort | uniq)

        echo "Stopping containers... $containers_to_kill"
        (sudo docker stop -t 2 ${containers_to_kill} 2>&1) > /dev/null
        echo "Removing containers... $containers_to_kill"
        (sudo docker rm -v -f ${containers_to_kill} 2>&1) > /dev/null

        if [[ ! -z "$containers_to_kill" ]]; then
            echo "Removing volumes... $volumes_to_remove"
            (sudo docker volume rm ${volumes_to_remove} 2>&1) || true > /dev/null
        fi
    fi
}

function cleanup_docker_image {
    if [ ! -z "$(sudo docker images -q opnfv/daisy)" ]; then
        sudo docker rmi -f opnfv/daisy
    fi
}

cleanup_container
cleanup_docker_image
build_rpm_pkg
