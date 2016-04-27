"This files lets you start all examples"
import argparse

import ipmininet
from ipmininet.ipnet import IPNet
from ipmininet.cli import IPCLI
from .simple_ospf_network import SimpleOSPFNet
from .simple_bgp_network import SimpleBGPTopo
from mininet.log import lg, LEVELS

TOPOS = {
         'simple_ospf_network': SimpleOSPFNet,
         'simple_bgp_network': SimpleBGPTopo
        }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--topo', choices=TOPOS.keys(),
                        default='simple_ospf_network',
                        help='The topology that you want to start.')
    parser.add_argument('--log', choices=LEVELS.keys(), default='info',
                        help='The level of details in the logs.')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    lg.setLogLevel(args.log)
    if args.log == 'debug':
        ipmininet.DEBUG_FLAG = True
    net = IPNet(topo=TOPOS[args.topo]())
    net.start()
    IPCLI(net)
    net.stop()
