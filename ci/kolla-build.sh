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

KOLLA_GIT="https://github.com/huzhijiang/kolla.git"
KOLLA_BRANCH="stable/ocata"
KOLLA_TAG=
EXT_TAG=
KOLLA_GIT_VERSION=
KOLLA_IMAGE_VERSION=
KOLLA_GIT_DIR=/tmp/kolla-git
REGISTRY_VOLUME_DIR=/tmp/registry
BUILD_OUTPUT_DIR=/tmp/kolla-build-output
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
  -t  Kolla git repo code tag(base version of image)
  -e  user defined tag extension(extended version)

Examples:
sudo `basename $0` -l https://git.openstack.org/openstack/kolla
                   -b stable/ocata
                   -t 4.0.2
                   -e 1
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EOF
}

while getopts "l:b:t:e:h" OPTION
do
    case $OPTION in
        l)
            KOLLA_GIT=${OPTARG}
            ;;
        b)
            KOLLA_BRANCH=${OPTARG}
            ;;
        t)
            KOLLA_TAG=${OPTARG}
            ;;
        e)
            EXT_TAG=${OPTARG}
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
    elif [ $KOLLA_BRANCH == "stable/ocata" ] ; then
        RPM_REQUIRES="python-docker-py:1.10 python2-pbr:1.10 python-jinja2:2.8 \
            python-gitdb:0.6.4 GitPython:1.0.1 python-six:1.10.0 \
            python2-oslo-config:3.22.0 python-netaddr:0.7.18 \
            python2-setuptools:22.0.0 python2-crypto:2.6 docker-engine:1.12 \
            centos-release-openstack-ocata:1 epel-release:7"
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
        -e REGISTRY_STORAGE_FILESYSTEM_ROOTDIRECTORY=/tmp/registry \
        -v $REGISTRY_VOLUME_DIR:/tmp/registry \
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

    upload_image_to_opnfv kolla-image-$version-$datetag.tgz

    popd
}

function update_kolla_code {
    echo "Updating Kolla code"

    rm -rf $KOLLA_GIT_DIR
    mkdir -p $KOLLA_GIT_DIR

    pushd $KOLLA_GIT_DIR
    git clone $KOLLA_GIT
    pushd $KOLLA_GIT_DIR/kolla
    git checkout $KOLLA_BRANCH

    if [[ ! -z "$KOLLA_TAG" ]]; then
        git checkout $KOLLA_TAG
    fi

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
    KOLLA_IMAGE_VERSION="${KOLLA_IMAGE_VERSION}.${EXT_TAG}"
}

function start_build {
    echo "Start to build Kolla image"
    REGISTRY_PARAM="--registry 127.0.0.1:5000 --push --tag $KOLLA_IMAGE_VERSION"
    pushd $KOLLA_GIT_DIR/kolla

    # Some of the images may be failed to built out but is OK
    # so we use "|| true" here.
    # TODO: We can impl. some checks to see if the images that
    # we really care are built successfully.
    tools/build.py $REGISTRY_PARAM || true;
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

    exit $exitcode
}

importkey () {
    # clone releng repository
    echo "Cloning releng repository..."
    [ -d releng ] && rm -rf releng
    git clone https://gerrit.opnfv.org/gerrit/releng ./releng/ &> /dev/null
    #this is where we import the siging key
    if [ -f ./releng/utils/gpg_import_key.sh ]; then
        source ./releng/utils/gpg_import_key.sh
    fi
}

upload_image_to_opnfv () {
    image=$1

    gpg2 -vvv --batch --yes --no-tty \
        --default-key opnfv-helpdesk@rt.linuxfoundation.org  \
        --passphrase besteffort \
        --detach-sig $image
    gsutil cp $image.sig gs://$GS_URL/upstream/$image.sig
    echo "image signature Upload Complete!"

    echo "Uploading $INSTALLER_TYPE artifact. This could take some time..."
    echo
    gsutil cp $image gs://$GS_URL/upstream/$image
    gsutil -m setmeta \
        -h "Cache-Control:private, max-age=0, no-transform" \
        gs://$GS_URL/upstream/$image

    # check if we uploaded the file successfully to see if things are fine
    gsutil ls gs://$GS_URL/upstream/$image
    if [[ $? -ne 0 ]]; then
        echo "Problem while uploading artifact!"
        exit 1
    fi
}



trap "error_trap" EXIT SIGTERM

pre_check
# Try to cleanup images of the last failed run, if any.
cleanup_kolla_image
update_kolla_code
config_kolla
cleanup_kolla_image

# Make sure there is no garbage in the registry server.
cleanup_registry_server
cleanup_registry_data
start_registry_server

start_build
cleanup_kolla_image
pack_registry_data

# TODO: Upload to OPNFV artifacts repo.
