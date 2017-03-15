import argparse
import os

from deploy.config.network import NetworkConfig

NOVA_CONF_PATH = '/etc/kolla/config/nova'
NOVA_API_CONF = '{}/nova-api.conf'.format(NOVA_CONF_PATH)


def _config_nova_api(network_file):
    xnet = NetworkConfig(network_file=network_file).external_network
    if not os.path.isdir(NOVA_CONF_PATH):
        os.makedirs(NOVA_CONF_PATH, mode=0644)

    with open(NOVA_API_CONF, 'w') as f:
        f.write('[DEFAULT]\n'
                'default_floating_pool={}\n'.format(xnet['network_name']))
        f.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-nw', '--network-file',
                        type=str,
                        required=True,
                        help='network configuration file')
    args = parser.parse_args()
    _config_nova_api(args.network_file)


if __name__ == '__main__':
    main()
