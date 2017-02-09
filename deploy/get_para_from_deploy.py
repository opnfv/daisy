#!/usr/bin/python
##############################################################################
# Copyright (c) 2016 ZTE Coreporation and others.
# hu.zhijiang@zte.com.cn
# lu.yao135@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import get_conf
from oslo_config import cfg
import sys

_CLI_OPTS = [
    cfg.StrOpt('dha',
               help='The dha file path'),
]


def parse(conf, args):
    conf.register_cli_opts(_CLI_OPTS)
    conf(args=args)


def get_yml_para(dha_file):
    data = get_conf.init(dha_file)
    disks = data.get("disks", 0)
    daisyserver_size = disks.get("daisy", 0)
    controller_node_size = disks.get("controller", 0)
    compute_node_size = disks.get("compute", 0)
    daisy_passwd = data.get("daisy_passwd", "")
    daisy_ip = data.get("daisy_ip", "")
    daisy_gateway = data.get("daisy_gateway", "")
    deploy_env = data.get("deploy_env", "")
    return daisyserver_size, controller_node_size,\
        compute_node_size, daisy_passwd, daisy_ip, daisy_gateway,\
        deploy_env


def get_conf_from_deploy():
    conf = cfg.ConfigOpts()
    parse(conf, sys.argv[1:])
    daisyserver_size, controller_node_size, compute_node_size,\
        daisy_passwd, daisy_ip, daisy_gateway,\
        deploy_env = get_yml_para(conf['dha'])
    print daisyserver_size
    print controller_node_size
    print compute_node_size
    print daisy_passwd
    print daisy_ip
    print daisy_gateway

if __name__ == "__main__":
    get_conf_from_deploy()
