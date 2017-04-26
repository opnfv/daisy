##############################################################################
# Copyright (c) 2017 ZTE Corporation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import commands
from configobj import ConfigObj
import os
import logging
import subprocess
import sys


join = os.path.join
CWD = os.getcwd()
WORKSPACE = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
BASE = CWD


def get_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(levelname)s  %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


LOG = get_logger()
LD = LOG.debug
LI = LOG.info
LW = LOG.warn
LE = LOG.error


def save_log_to_file(log_file):
    if os.path.isfile(log_file):
        os.remove(log_file)
    status, output = commands.getstatusoutput('touch %s' % log_file)
    if status:
        err_exit('Log file %s cannot be accessed' % log_file)

    formatter = logging.Formatter('%(asctime)s %(levelname)s  %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler = logging.FileHandler(log_file, mode='w')
    handler.setFormatter(formatter)
    LOG.addHandler(handler)


def err_exit(message):
    LE('%s\n' % message)
    sys.exit(1)


def log_bar(message, log_func=LI):
    bar = '=' * len(message)
    log_func(bar)
    log_func(message)
    log_func(bar)


def check_sudo_privilege():
    uid = os.getuid()
    if uid != 0:
        err_exit('You need run this script with sudo privilege')


def check_file_exists(file_path):
    if not os.path.dirname(file_path):
        file_path = os.path.normpath(os.path.join(BASE, file_path))
    if not os.access(file_path, os.R_OK):
        err_exit('File %s not found\n' % file_path)


def make_file_executable(file_path):
    if not os.path.isdir(file_path):
        file_path = os.path.normpath(os.path.join(BASE, file_path))
    if not os.access(file_path, os.R_OK):
        err_exit('File %s not found\n' % file_path)
    if not os.access(file_path, os.X_OK):
        LW('File %s is not executable, chmod it and continue' % file_path)
        status, output = commands.getstatusoutput('chmod +x %s' % file_path)
        if status:
            err_exit('Cannot change the file mode of %s' % file_path)


def confirm_dir_exists(dir_path):
    if not os.path.isdir(dir_path):
        LI('Creating directory %s' % dir_path)
        os.makedirs(dir_path)


def update_config(conf_file, key, value, section='DEFAULT'):
    LI('Update_config [ %s : %s ] to file: %s' % (key, value, conf_file))
    config = ConfigObj(conf_file)
    config[section][key] = value
    config.write()


def ipmi_reboot_node(host, user, passwd, boot_source=None):
    prefix = 'ipmitool -I lanplus -H {host} -U {user} -P {passwd} -R 1 '.format(
        host=host, user=user, passwd=passwd)
    if boot_source:
        cmd = prefix + 'chassis bootdev {boot_source}'.format(boot_source=boot_source)
        LI('IMPI set node %s boot from %s' % (host, boot_source))
        status, output = commands.getstatusoutput(cmd)
        if status:
            err_exit('IPMI command failed: %s' % output)

    cmd = prefix + 'chassis power reset'
    LI('IPMI reset node %s' % host)
    status, output = commands.getstatusoutput(cmd)
    if status:
        err_exit('IPMI command failed: %s' % output)


def run_shell(cmd, check=False):
    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               shell=True)
    while process.poll() is None:
        LD(process.stdout.readline().strip())

    response, stderr = process.communicate()
    return_code = process.returncode

    if check:
        if return_code > 0:
            stderr = stderr.strip()
            LE('Failed command: ' + str(cmd))
            LE('Command returned error: ' + str(stderr))
            err_exit('Command return code: ' + str(return_code))
        else:
            LI('Successful command: ' + str(cmd))

    return return_code
