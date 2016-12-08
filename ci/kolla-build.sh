#!/bin/bash
##############################################################################
# Copyright (c) 2016 ZTE Coreporation and others.
# hu.zhijiang@zte.com.cn
# lu.yao135@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Build OpenStack container images as well as extension images.
# Parameters: $1 kolla git url, for example, 
#                 https://git.openstack.org/openstack/kolla 
#             $2 kolla branch, for example, stable/newton
set -o

KOLLA_GIT=$1
KOLLA_BRANCH=$2
KOLLA_GIT_VERSION=
KOLLA_GIT_DIR=/tmp/kolla-git
REGISTRY_VOLUME_DIR=/tmp/registry
BUILD_OUTPUT_DIR=/tmp/kolla-build-output
REGISTRY_SERVER_NAME=daisy-registry

function pre_check {
    echo "Pre setup"
    if [ $KOLLA_BRANCH == "stable/mitaka" ] ; then
        RPM_REQUIRES="python-docker-py:1.6 python-pbr:1.6 python-jinja2:2.8 \
            python-gitdb:0.6.4 GitPython:1.0.1 python-six:1.9.0 \
            python2-oslo-config:3.7.0 python-beautifulsoup4:4.4.1 \
            python2-setuptools:16.0.0 python2-crypto:2.6 docker-engine:1.12"
    elif [ $KOLLA_BRANCH == "stable/newton" ] ; then
        RPM_REQUIRES="python-docker-py:1.6 python-pbr:1.6 python-jinja2:2.8 \
            python-gitdb:0.6.4 GitPython:1.0.1 python-six:1.9.0 \
            python2-oslo-config:3.14.0 python-netaddr:0.7.13 \
            python2-setuptools:16.0.0 python2-crypto:2.6 docker-engine:1.12 \
            centos-release-openstack-newton:1 epel-release:7"
    else
        exit 1
    fi

    for package_version in $RPM_REQUIRES
    do
        package=`echo $package_version | awk -F: '{print $1}'`
        expversion=`echo $package_version | awk -F: '{print $2}'`

        echo "Step:1 Check if $package existed"
        rpm -q $package &> /dev/null
        if [ "$?" != "0" ] ; then
            echo "$package not installed"
                exit 1
            fi

        echo "Step:2 Check if $package version meets the requirement"
        realversion=$(rpm -q --queryformat '%{VERSION}' $package)
        smallestversion=`printf "$realversion\n$expversion\n" | sort -V | head -1`
        if [ "$smallestversion" != "$expversion" ] ; then
            echo "$package version $realversion DOES NOT meet the \
                requirement verion $expversion"
            exit 1
        fi
    done

    # Some packages must be installed by pip.
    # TODO: Check version of packages installed by pip just like what we do for RPM above.
    rpm -e tox || true
    rpm -e python-virtualenv || true
    rpm -e python-py || true
    pip install tox

    # Just make sure docker is working.
    service docker restart
}

function cleanup_registry_server {
    echo "Cleaning registry server"
    containers_to_kill=$(sudo docker ps --filter "name=$REGISTRY_SERVER_NAME" \
        --format "{{.Names}}" -a)

    if [[ -z "$containers_to_kill" ]]; then
        echo "No containers to cleanup."
    else
        volumes_to_remove=$(sudo docker inspect -f \
            '{{range .Mounts}} {{printf "%s\n" .Name }}{{end}}' \
            ${containers_to_kill} | egrep -v '(^\s*$)' | sort | uniq)
    fi

    echo "Stopping containers... $containers_to_kill"
    sudo docker stop -t 2 ${containers_to_kill} >/dev/null 2>&1

    echo "Removing containers... $containers_to_kill"
    sudo docker rm -v -f ${containers_to_kill} >/dev/null 2>&1

    echo "Removing volumes... $volumes_to_remove"
    sudo docker volume rm ${volumes_to_remove} >/dev/null 2>&1
}

function cleanup_registry_data {
    echo "Cleaning registry data dir"

    # Host runs this builder can not be used for other purposes,
    # so here we can delete all the prev built images.
    docker rm -f $(docker ps -a -q)
    docker rmi -f $(docker images -q)

    rm -rf $REGISTRY_VOLUME_DIR
    mkdir -p $REGISTRY_VOLUME_DIR
}

function start_registry_server {
    echo "Starting registry server"
    sudo docker run -d -p 5000:5000 --restart=always \
        -e REGISTRY_STORAGE_FILESYSTEM_ROOTDIRECTORY=/tmp/registry \
        -v $REGISTRY_VOLUME_DIR:/tmp/registry  --name $REGISTRY_SERVER_NAME registry:2
}

function pack_registry_data {
    echo "Packaging registry data"
    datetag=`date +%y%m%d%H%M%S`
    version=`echo $KOLLA_BRANCH | awk -F'/' '{print $2}'`

    if [ ! -d $BUILD_OUTPUT_DIR ] ; then
        mkdir -p $BUILD_OUTPUT_DIR
    fi

    pushd $BUILD_OUTPUT_DIR
    tar czf registry-$version-$datetag.tgz $REGISTRY_VOLUME_DIR
    echo $KOLLA_GIT_VERSION > registry-$version-$datetag.version
    tar czf kolla-image-$version-$datetag.tgz \
        registry-$version-$datetag.tgz \
        registry-$version-$datetag.version
    popd
}

function update_kolla_code {
    echo "Updating Kolla code"
    if [ ! -d $KOLLA_GIT_DIR ] ; then
            mkdir -p $KOLLA_GIT_DIR
    fi

    if [ ! -d $KOLLA_GIT_DIR/kolla ] ; then
        pushd $KOLLA_GIT_DIR
        git clone $KOLLA_GIT
        git checkout $KOLLA_BRANCH
        popd
    else
        pushd $KOLLA_GIT_DIR/kolla
        git remote update
        git checkout $KOLLA_BRANCH
        git pull --ff-only
        popd
    fi

    pushd $KOLLA_GIT_DIR/kolla
    KOLLA_GIT_VERSION=`git log -1 --pretty="%H"`
    tox -e genconfig
    popd
}

function start_build {
    echo "Start to build Kolla image"
    REGISTRY_PARAM="--registry 127.0.0.1:5000 --push"
    pushd $KOLLA_GIT_DIR/kolla
    tools/build.py $REGISTRY_PARAM
    popd
}

function usage {
    echo "Usage: $0 https://git.openstack.org/openstack/kolla stable/newton" 
}

if [ "$1" == "" -o "$2" == "" ] ; then
    usage
    exit 1
fi

pre_check
update_kolla_code

# Make sure ther is no garbage in the registry server.
cleanup_registry_server
cleanup_registry_data
start_registry_server

start_build
pack_registry_data

# TODO: Upload to OPNFV artifacts repo.
