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
  -h  Print this message and exit

Description:
  prepare configuration

Examples:
sudo `basename $0` -n /home/daisy/config/vm_environment/zte-virtual1/network.yml
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EOF
}

NETWORK_CONF=''

while getopts "n:h" OPTION
do
    case $OPTION in
        n)
            NETWORK_CONF=${OPTARG}
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

python $PYTHONPATH/deploy/prepare/execute.py -nw $NETWORK_CONF
