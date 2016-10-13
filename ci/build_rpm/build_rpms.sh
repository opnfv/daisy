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

function build_rpm_pkg {
      sudo docker build -t daisy4nfv_rpm .
      sudo docker run -v DAISYDIR:/opt/daisy4nfv -t  daisy4nfv_rpm \
                      /opt/daisy4nfv/ci/build_rpm/build_rpms_docker.sh
    ;;
}

build_rpm_pkg
