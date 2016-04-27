"""An enhanced CLI providing IP-related commands"""
from mininet.cli import CLI
from mininet.log import lg


class IPCLI(CLI):
    def do_route(self, line=""):
        """route destination: Print all the routes towards that destination
        for every router in the network"""
        for r in self.mn.routers:
            self.default('[%s] ip route get %s' % (r.name, line))

    def do_ip(self, line):
        """ip IP1 IP2 ...: return the node associated to the given IP"""
        for ip in line.split(' '):
            try:
                n = self.mn.node_for_ip(ip)
            except KeyError:
                n = 'unknown IP'
            finally:
                lg.info(ip, '|', n)
        lg.info('\n')

    def do_ips(self, line):
        """ips n1 n2 ...: return the ips associated to the given node name"""
        for n in line.split(' '):
            try:
                l = [itf.ip for itf in self.mn[n].intfList()]
            except KeyError:
                l = 'unknown node'
            finally:
                lg.info(n, '|', l)
        lg.info('\n')
