"""This modules shows a 2-routers topology which run the sshd daemon."""
from ipmininet.iptopo import IPTopo
from ipmininet.router.config import SSHd, RouterConfig


class SSHTopo(IPTopo):
    """This is a simple 2-hosts topology with custom IPTable rules."""
    def build(self, *args, **kw):
        config = (RouterConfig, {'daemons': [SSHd]})
        self.addLink(self.addRouter('r1', config=config),
                     self.addRouter('r2', config=config))
        super(SSHTopo, self).build(*args, **kw)
