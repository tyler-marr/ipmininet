"This files lets you start all examples"
import argparse

import ipmininet
from ipmininet.ipnet import IPNet
from ipmininet.cli import IPCLI

from .simple_ospf_network import SimpleOSPFNet
from .simple_bgp_network import SimpleBGPTopo
from .bgp_decision_process import BGPDecisionProcess
from .iptables import IPTablesTopo
from .gre import GRETopo
from .sshd import SSHTopo


from mininet.log import lg, LEVELS

TOPOS = {
         'simple_ospf_network': SimpleOSPFNet,
         'simple_bgp_network': SimpleBGPTopo,
         'bgp_decision_process': BGPDecisionProcess,
         'iptables': IPTablesTopo,
         'gre': GRETopo,
         'ssh': SSHTopo
        }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--topo', choices=TOPOS.keys(),
                        default='simple_ospf_network',
                        help='The topology that you want to start.')
    parser.add_argument('--log', choices=LEVELS.keys(), default='info',
                        help='The level of details in the logs.')
    parser.add_argument('--args', help='Additional arguments to give'
                        'to the topology constructor (key=val, key=val, ...)',
                        default='')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    lg.setLogLevel(args.log)
    if args.log == 'debug':
        ipmininet.DEBUG_FLAG = True
    kwargs = {}
    for arg in args.args.strip(' \r\t\n').split(','):
        arg = arg.strip(' \r\t\n')
        if not arg:
            continue
        try:
            k, v = arg.split('=')
            kwargs[k] = v
        except ValueError:
            lg.error('Ignoring args:', arg)
    net = IPNet(topo=TOPOS[args.topo](**kwargs))
    net.start()
    IPCLI(net)
    net.stop()
