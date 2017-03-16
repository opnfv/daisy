#!/bin/bash

SCRIPT_PATH=$(readlink -f $(dirname $0))

export PYTHONPATH=$SCRIPT_PATH/..

usage ()
{
cat << EOF
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
`basename $0`: create default configuration

usage: `basename $0` -n network_config_file

OPTIONS:
  -nw  network configuration path, necessary
  -h  Print this message and exit

Description:
  create default configuration for OpenStack

Examples:
sudo `basename $0` -n /home/daisy/labs/zte/virtual1/daisy/config/network.yml
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EOF
}

NETWORK=''

while getopts "n:h" OPTION
do
    case $OPTION in
        n)
            NETWORK=${OPTARG}
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

python $PYTHONPATH/deploy/prepare/execute.py -nw $NETWORK
