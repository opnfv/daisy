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

set -o errexit
set -o nounset
set -o pipefail

KOLLA_GIT="https://git.openstack.org/openstack/kolla"
KOLLA_BRANCH="stable/ocata"
OPNFV_JOB_NAME=
KOLLA_TAG=
EXT_TAG=
KOLLA_GIT_VERSION=
KOLLA_IMAGE_VERSION=

SCRIPT_PATH=$(readlink -f $(dirname $0))
WORKSPACE=$(cd ${SCRIPT_PATH}/..; pwd)

WORK_DIR=$WORKSPACE

REGISTRY_SERVER_NAME=daisy-registry

function usage
{
cat << EOF
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
`basename $0`: Build Daisy4NFV's Kolla image package

usage: `basename $0` [options]

OPTIONS:
  -l  Kolla git repo location
  -b  Kolla git repo branch
  -j  OPNFV job name
  -t  Kolla git repo code tag(base version of image)
  -e  user defined tag extension(extended version)
  -w  working directroy

Examples:
sudo `basename $0` -l https://git.openstack.org/openstack/kolla
                   -b stable/ocata
                   -j daisy-docker-build-euphrates
                   -t 4.0.2
                   -e .1
                   -w /path/to/the/working/dir
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EOF
}

while getopts "l:b:j:t:e:w:h" OPTION
do
    case $OPTION in
        l)
            KOLLA_GIT=${OPTARG}
            ;;
        b)
            KOLLA_BRANCH=${OPTARG}
            ;;
        j)
            OPNFV_JOB_NAME=${OPTARG}
            ;;
        t)
            KOLLA_TAG=${OPTARG}
            ;;
        e)
            EXT_TAG=${OPTARG}
            ;;
        w)
            WORK_DIR=${OPTARG}
            ;;
        h)
            usage
            exit 0
            ;;
        *)
            echo "${OPTION} is not a valid argument"
            usage
            exit 1
            ;;
    esac
done

KOLLA_GIT_DIR=$WORK_DIR/kolla-git
REGISTRY_VOLUME_DIR=$WORK_DIR/registry
BUILD_OUTPUT_DIR=$WORK_DIR/kolla-build-output

# OPNFV_JOB_NAME overwrites KOLLA_BRANCH
if [[ ! -z "$OPNFV_JOB_NAME" ]]; then
    if [[ "$OPNFV_JOB_NAME" =~ "euphrates" ]]; then
        KOLLA_BRANCH="stable/ocata"
    elif [[ "$OPNFV_JOB_NAME" =~ "fraser" ]]; then
        KOLLA_BRANCH="stable/pike"
    else
        # For master branch
        KOLLA_BRANCH="stable/pike"
    fi
fi

function pre_check {
    echo "Pre setup"
    if [ $KOLLA_BRANCH == "stable/mitaka" ] ; then
        yum install -y epel-release centos-release-openstack-mitaka
        RPM_REQUIRES="python-docker-py:1.6 python-pbr:1.6 python-jinja2:2.8 \
            python-gitdb:0.6.4 GitPython:1.0.1 python-six:1.9.0 \
            python2-oslo-config:3.7.0 python-beautifulsoup4:4.4.1 \
            python2-setuptools:16.0.0 python2-crypto:2.6 docker-engine:1.12"
    elif [ $KOLLA_BRANCH == "stable/newton" ] ; then
        yum install -y epel-release centos-release-openstack-newton
        RPM_REQUIRES="python-docker-py:1.6 python-pbr:1.6 python-jinja2:2.8 \
            python-gitdb:0.6.4 GitPython:1.0.1 python-six:1.9.0 \
            python2-oslo-config:3.14.0 python-netaddr:0.7.13 \
            python2-setuptools:16.0.0 python2-crypto:2.6 docker-engine:1.12 \
            centos-release-openstack-newton:1 epel-release:7"
    elif [ $KOLLA_BRANCH == "stable/ocata" ] ; then
        yum install -y epel-release centos-release-openstack-ocata
        yum update -y
        yum install -y python-docker-py python2-pbr python-jinja2 \
            python-gitdb GitPython python-six \
            python2-oslo-config python-netaddr \
            python2-setuptools python2-crypto docker
        RPM_REQUIRES="python-docker-py:1.10 python2-pbr:1.10 python-jinja2:2.8 \
            python-gitdb:0.6.4 GitPython:1.0.1 python-six:1.10.0 \
            python2-oslo-config:3.22.0 python-netaddr:0.7.18 \
            python2-setuptools:22.0.0 python2-crypto:2.6 docker:1.12 \
            centos-release-openstack-ocata:1 epel-release:7"
    elif [ $KOLLA_BRANCH == "stable/pike" ] ; then
        yum install -y epel-release centos-release-openstack-pike
        yum update -y
        yum install -y python2-docker python2-pbr python2-jinja2 \
            python-gitdb GitPython python2-six \
            python2-oslo-config python-netaddr \
            python2-setuptools python2-crypto docker
        RPM_REQUIRES="python2-docker:2.4.2 python2-pbr:3.1.1 python2-jinja2:2.8 \
            python-gitdb:0.6.4 GitPython:1.0.1 python2-six:1.10.0 \
            python2-oslo-config:3.22.0 python-netaddr:0.7.18 \
            python2-setuptools:22.0.0 python2-crypto:2.6 docker:1.12 \
            centos-release-openstack-pike:1 epel-release:7"
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
                requirement version $expversion"
            exit 1
        fi
    done

    yum install -y gcc
    yum install -y python-devel
    yum install -y crudini

    # Some packages must be installed by pip.
    # TODO: Check version of packages installed by pip just like what we do for RPM above.
    rpm -e python-tox || true
    rpm -e python-virtualenv || true
    rpm -e python-py || true
    yum install -y python2-pip
    pip install tox

    # Just make sure docker is working.
    service docker restart
}

function cleanup_registry_server {
    echo "Cleaning registry server"
    containers_to_kill=$(sudo docker ps --filter "name=$REGISTRY_SERVER_NAME" \
        --format "{{.Names}}" -a)

    if [[ ! -z "$containers_to_kill" ]]; then
        volumes_to_remove=$(sudo docker inspect -f \
            '{{range .Mounts}} {{printf "%s\n" .Name }}{{end}}' \
            ${containers_to_kill} | egrep -v '(^\s*$)' | sort | uniq)

        echo "Stopping containers... $containers_to_kill"
        (sudo docker stop -t 2 ${containers_to_kill} 2>&1) > /dev/null
        echo "Removing containers... $containers_to_kill"
        (sudo docker rm -v -f ${containers_to_kill} 2>&1) > /dev/null

        if [[ ! -z "$volumes_to_remove" ]]; then
            echo "Removing volumes... $volumes_to_remove"
            (sudo docker volume rm ${volumes_to_remove} 2>&1) || true > /dev/null
        fi
    fi
}

function cleanup_registry_data {
    echo "Cleaning registry data dir"
    rm -rf $REGISTRY_VOLUME_DIR
    mkdir -p $REGISTRY_VOLUME_DIR
}

function cleanup_kolla_image {
    echo "Cleaning Kolla images"
    if [ -d $KOLLA_GIT_DIR/kolla ] ; then
        pushd $KOLLA_GIT_DIR/kolla
        (./tools/cleanup-images 2>&1) || true > /dev/null;
        popd
    fi
}

function start_registry_server {
    echo "Starting registry server"
    sudo docker run -d -p 5000:5000 --restart=always \
        -e REGISTRY_STORAGE_FILESYSTEM_ROOTDIRECTORY=/home/registry \
        -v $REGISTRY_VOLUME_DIR:/home/registry \
        --name $REGISTRY_SERVER_NAME registry:2
}

function pack_registry_data {
    echo "Packaging registry data"
    datetag=$(date +%y%m%d%H%M%S)

    #TODO: not compatible with "master" branch
    version=$(echo $KOLLA_BRANCH | awk -F'/' '{print $2}')

    if [ ! -d $BUILD_OUTPUT_DIR ] ; then
        mkdir -p $BUILD_OUTPUT_DIR
    fi

    pushd $BUILD_OUTPUT_DIR
    echo $KOLLA_GIT_VERSION > registry-$version-$datetag.version
    echo "branch = $KOLLA_BRANCH" >> registry-$version-$datetag.version
    echo "tag = $KOLLA_IMAGE_VERSION" >> registry-$version-$datetag.version
    echo "date = $datetag" >> registry-$version-$datetag.version
    tar czf kolla-image-$version-$datetag.tgz $REGISTRY_VOLUME_DIR \
        registry-$version-$datetag.version
    rm -rf registry-$version-$datetag.version
    popd
}

function update_kolla_code {
    echo "Updating Kolla code"

    rm -rf $KOLLA_GIT_DIR
    mkdir -p $KOLLA_GIT_DIR

    pushd $KOLLA_GIT_DIR
    git clone https://git.openstack.org/openstack/kolla 
    pushd $KOLLA_GIT_DIR/kolla
    git checkout $KOLLA_BRANCH

    if [[ ! -z "$KOLLA_TAG" ]]; then
        git checkout $KOLLA_TAG
    fi

    # Apply patches for openstack/kolla project
    cp $WORKSPACE/ci/kolla_patches/*.patch ./
    git apply *.patch

    KOLLA_GIT_VERSION=$(git log -1 --pretty="%H")
    tox -e genconfig
    KOLLA_IMAGE_VERSION=$(cat $KOLLA_GIT_DIR/kolla/etc/kolla/kolla-build.conf \
        | grep "#tag" | gawk -F' = ' '{print $2}')

    if [[ ! -z "$KOLLA_TAG" ]]; then
        if ["$KOLLA_TAG" != $KOLLA_IMAGE_VERSION] ; then
            echo "tag in git: $KOLLA_TAG, while tag in code: $KOLLA_IMAGE_VERSION"
            exit 1
        fi
    fi

    popd
    popd
}

function config_kolla {
    rm -rf /etc/kolla/kolla-build.conf
    KOLLA_IMAGE_VERSION="${KOLLA_IMAGE_VERSION}${EXT_TAG}"
}

function config_kolla_with_dpdksource {
#    crudini --set $KOLLA_GIT_DIR/kolla/etc/kolla/kolla-build.conf  DEFAULT debug true
    crudini --set $KOLLA_GIT_DIR/kolla/etc/kolla/kolla-build.conf  DEFAULT threads 2
    crudini --set $KOLLA_GIT_DIR/kolla/etc/kolla/kolla-build.conf  DEFAULT retries 10

    crudini --set $KOLLA_GIT_DIR/kolla/etc/kolla/kolla-build.conf  profiles opnfvb "ceilometer, gnocchi, neutron, openvswitch, nova-, cron, kolla-toolbox, fluentd, aodh, mongodb, horizon, heat, cinder, glance, ceph, keystone, rabbitmq, mariadb, memcached, keepalived, haproxy, opendaylight, tgtd, iscsi"
    crudini --set $KOLLA_GIT_DIR/kolla/etc/kolla/kolla-build.conf  DEFAULT profile opnfvb

    crudini --set $KOLLA_GIT_DIR/kolla/etc/kolla/kolla-build.conf  ovsdpdk-plugin-ovs type git
    crudini --set $KOLLA_GIT_DIR/kolla/etc/kolla/kolla-build.conf  ovsdpdk-plugin-ovs location https://github.com/openvswitch/ovs.git
    crudini --set $KOLLA_GIT_DIR/kolla/etc/kolla/kolla-build.conf  ovsdpdk-plugin-ovs reference v2.7.0

    crudini --set $KOLLA_GIT_DIR/kolla/etc/kolla/kolla-build.conf  ovsdpdk-plugin-dpdk type git
    crudini --set $KOLLA_GIT_DIR/kolla/etc/kolla/kolla-build.conf  ovsdpdk-plugin-dpdk location http://dpdk.org/git/dpdk
    #crudini --set $KOLLA_GIT_DIR/kolla/etc/kolla/kolla-build.conf  ovsdpdk-plugin-dpdk reference v17.02
    crudini --set $KOLLA_GIT_DIR/kolla/etc/kolla/kolla-build.conf  ovsdpdk-plugin-dpdk reference v16.11

    mkdir -p /etc/kolla/
    rm -rf /etc/kolla/kolla-build.conf
    cp $KOLLA_GIT_DIR/kolla/etc/kolla/kolla-build.conf /etc/kolla/
    KOLLA_IMAGE_VERSION="${KOLLA_IMAGE_VERSION}${EXT_TAG}"
}


function start_build {
    echo "Start to build Kolla image"
    pushd $KOLLA_GIT_DIR/kolla

    echo "=============================OpenStack & ODL build from binary=============================="

    REGISTRY_PARAM="--registry 127.0.0.1:5000 --push --tag $KOLLA_IMAGE_VERSION"
    tools/build.py $REGISTRY_PARAM;

    echo "=============================DPDK build from source=============================="

    REGISTRY_PARAM="--registry 127.0.0.1:5000 --push --tag $KOLLA_IMAGE_VERSION --template-override contrib/template-override/ovs-dpdk.j2 -t source dpdk"
    tools/build.py $REGISTRY_PARAM;
    popd
}

exitcode=""
error_trap()
{
    local rc=$?

    set +e

    if [ -z "$exitcode" ]; then
        exitcode=$rc
    fi

    echo "Image build failed with $exitcode"
    cleanup_kolla_image
    cleanup_registry_server
    cleanup_registry_data
    exit $exitcode
}

trap "error_trap" EXIT SIGTERM

pre_check

# Try to cleanup images of the last failed run, if any.
cleanup_kolla_image
update_kolla_code
config_kolla_with_dpdksource
cleanup_kolla_image

# Make sure there is no garbage in the registry server.
cleanup_registry_server
cleanup_registry_data
start_registry_server

start_build
cleanup_kolla_image
pack_registry_data
