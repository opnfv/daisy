import argparse
import os

from deploy.config.network import NetworkConfig

KOLLA_CONF_PATH = '/etc/kolla/config'


def _make_dirs(path):
    if not os.path.isdir(path):
        os.makedirs(path, mode=0644)


def _write_conf_file(conf_file, conf):
    with open(conf_file, 'w') as f:
        f.write(conf)
        f.close()


def _config(service, server, conf):
    service_conf_path = os.path.join(KOLLA_CONF_PATH, service)
    service_server = os.path.join(service_conf_path,
                                  '{}-{}.conf'.format(service, server))
    _make_dirs(service_conf_path)
    _write_conf_file(service_server, conf)


def _config_nova_api(network_file):
    xnet = NetworkConfig(network_file=network_file).external_network
    _config('nova', 'api',
            '[DEFAULT]\n'
            'default_floating_pool = {}\n'.format(xnet['network_name']))


def _config_heat_api():
    _config('heat', 'api',
            '[DEFAULT]\n'
            'deferred_auth_method = password\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-nw', '--network-file',
                        type=str,
                        required=True,
                        help='network configuration file')
    args = parser.parse_args()
    _config_nova_api(args.network_file)
    _config_heat_api()


if __name__ == '__main__':
    main()
