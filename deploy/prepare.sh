##############################################################################
# Copyright (c) 2017 ZTE Coreporation and others.
# feng.xiaowei@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
#!/bin/bash

SCRIPT_PATH=$(readlink -f $(dirname $0))

export PYTHONPATH=$SCRIPT_PATH/..

usage ()
{
cat << EOF
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
`basename $0`: make preparation for daisy deployment

usage: `basename $0` -n network_config_file

OPTIONS:
  -n  network configuration path, necessary
  -b  0 for virtual, 1 for baremetal
  -h  Print this message and exit

Description:
  prepare configuration

Examples:
sudo `basename $0` -n /home/daisy/config/vm_environment/zte-virtual1/network.yml
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EOF
}

NETWORK_CONF=''

while getopts "n:b:h" OPTION
do
    case $OPTION in
        n)
            NETWORK_CONF=${OPTARG}
            ;;
        b)
            IS_BARE=${OPTARG}
            ;;
        h)
            usage
            exit 0
            ;;
        *)
            echo "${OPTION} is not a valid argument"
            usage
            exit 0
            ;;
    esac
done

python $PYTHONPATH/deploy/prepare/execute.py -nw $NETWORK_CONF -b $IS_BARE
