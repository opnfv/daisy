##############################################################################
# Copyright (c) 2017 ZTE Corporation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import copy
from jsonschema import Draft4Validator, FormatChecker
import sys
import yaml


MIN_DAISY_DISK_SIZE = 50
# minimal size of root_lv_size is 102400 mega-bytes
MIN_NODE_DISK_SIZE = 110
MIN_CEPH_DISK_SIZE = 110

hosts_schema = {
    'type': 'array',
    'items': {
        'type': 'object',
        'properties': {
            'name': {'type': 'string', 'minLength': 1},
            'roles': {
                'type': 'array',
                'items': {
                    'type': 'string',
                    'enum': ['COMPUTER', 'CONTROLLER_LB', 'CONTROLLER_HA']
                }
            },
            'template': {'type': 'string', 'minLength': 1},
            'ipmi_ip': {'type': 'string', 'format': 'ip-address'},
            'ipmi_user': {'type': 'string'},
            'ipmi_pass': {'type': 'string'},
            'mac_addresses': {
                'type': 'array',
                'items': {
                    'type': 'string',
                    'pattern': '^([0-9a-fA-F]{2})((:[0-9a-fA-F]{2}){5})$'
                }
            }
        },
        'required': ['roles']
    }
}

disks_schema = {
    'type': 'object',
    'properties': {
        'daisy': {'type': 'integer', 'minimum': MIN_DAISY_DISK_SIZE},
        'controller': {'type': 'integer', 'minimum': MIN_NODE_DISK_SIZE},
        'compute': {'type': 'integer', 'minimum': MIN_NODE_DISK_SIZE},
        'ceph': {'type': 'integer', 'minimum': MIN_CEPH_DISK_SIZE}
    }
}

schema_mapping = {
    'adapter': {'type': 'string', 'enum': ['ipmi', 'libvirt']},
    'hosts': hosts_schema,
    'disks': disks_schema,
    'daisy_passwd': {'type': 'string'},
    'daisy_ip': {'type': 'string', 'format': 'ip-address'},
    'daisy_gateway': {'type': 'string', 'format': 'ip-address'},
    'ceph_disk_name': {'type': 'string'},
    'modules': {'type': ['array', 'null']}
}

deploy_schema = {
    'type': 'object',
    'properties': schema_mapping,
    'required': ['hosts', 'daisy_passwd', 'daisy_gateway']
}

deploy_schema_bm = copy.deepcopy(deploy_schema)
deploy_schema_bm['properties']['hosts']['items']['required'] = \
    ['roles', 'ipmi_ip', 'ipmi_user', 'ipmi_pass']


def _validate(data, schema):
    v = Draft4Validator(schema, format_checker=FormatChecker())
    errors = sorted(v.iter_errors(data), key=lambda e: e.path)
    return errors


def deploy_schema_validate(data):
    if data.get('adapter', 'libvirt') == 'ipmi':
        return _validate(data, deploy_schema_bm)
    else:
        return _validate(data, deploy_schema)


def _main():
    if 2 != len(sys.argv):
        sys.exit(1)
    try:
        data = yaml.safe_load(open(sys.argv[1], 'r'))
        errors = deploy_schema_validate(data)
    except Exception as e:
        errors = 'Exception occured: ' + str(e)
    if errors:
        sys.exit(errors)


if __name__ == '__main__':
    _main()
