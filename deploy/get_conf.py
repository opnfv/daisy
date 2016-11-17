import yaml


def init(file):
    with open(file) as fd:
        return yaml.load(fd)


def networkdecorator(func):
    def wrapter(s, seq):
        network_list = s.get('networks', [])
        result = {}
        for network in network_list:
            s = func(s, seq, network)
            if not s:
                continue
            result.update(s)
        if len(result) == 0:
            return ""
        else:
            return result
    return wrapter


def hostdecorator(func):
    def wrapter(s, seq):
        host_list = s.get('hosts', [])
        result = {}
        for host in host_list:
            s = func(s, seq, host)
            if not s:
                continue
            result.update(s)
        if len(result) == 0:
            return ""
        else:
            return result
    return wrapter


def decorator(func):
    def wrapter(s, seq):
        host_list = s.get('hosts', [])
        result = []
        for host in host_list:
            s = func(s, seq, host)
            if not s:
                continue
            result.append(s)
        if len(result) == 0:
            return ""
        else:
            return result
    return wrapter


@networkdecorator
def network(s, seq, network=None):
    net_plane = network.get('name', '')
    network.pop('name')
    map = {}
    map[net_plane] = network
    return map


@hostdecorator
def interface(s, seq, host=None):
    hostname = host.get('name', '')
    interface = host.get('interface', '')[0]
    map = {}
    map[hostname] = interface
    return map


@hostdecorator
def role(s, seq, host=None):
    hostname = host.get('name', '')
    role = host.get('roles', '')
    map = {}
    map[hostname] = role
    return map


@decorator
def host(s, seq, host=None):
    hostip = host.get('ip', [])
    passwd = host.get('password', [])
    map = {}
    map = {'ip': hostip, 'passwd': passwd}
    return map


def network_config_parse(s, dha_file):
    network_map = network(s, ',')
    vip = s.get('internal_vip')
    return network_map, vip


def dha_config_parse(s, dha_file):
    host_interface_map = interface(s, ',')
    host_role_map = role(s, ',')
    host_ip_passwd_map = host(s, ',')
    return host_interface_map, host_role_map, host_ip_passwd_map


def config(dha_file, network_file):
    data = init(dha_file)
    host_interface_map, host_role_map, host_ip_passwd_map = \
        dha_config_parse(data, dha_file)
    data = init(network_file)
    network_map, vip = network_config_parse(data, network_file)
    return host_interface_map, host_role_map, \
           host_ip_passwd_map, network_map, vip
