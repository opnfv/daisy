##############################################################################
# Copyright (c) 2017 ZTE Corporation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from jsonschema import Draft4Validator, FormatChecker


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
            'template': {'type': 'string', 'minLength': 1}
        }
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
}

deploy_schema = {
    'type': 'object',
    'properties': schema_mapping,
    'required': ['hosts', 'daisy_passwd', 'daisy_ip', 'daisy_gateway']
}


def _validate(data, schema):
    v = Draft4Validator(schema, format_checker=FormatChecker())
    errors = sorted(v.iter_errors(data), key=lambda e: e.path)
    return errors


def item_validate(data, schema_type):
    if schema_type not in schema_mapping:
        return str('Schema Type %s does not exist' % schema_type)
    else:
        return _validate(data, schema_mapping.get(schema_type))


def deploy_schema_validate(data):
    return _validate(data, deploy_schema)
