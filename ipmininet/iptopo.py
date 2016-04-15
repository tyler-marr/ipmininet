"""This module defines topology class that supports adding L3 routers"""
from mininet.topo import Topo

# TODO add high-level primitives to group links/nodes by IGP areas,
# BGP AS, ... instead of having to do it on a per-link basis.


class IPTopo(Topo):
    """A topology that supports L3 routers"""

    def isNodeType(self, n, x):
        """Return wether node n has a key x set to True

        :param n: node name
        :param x: the key to check"""
        try:
            return self.g.node[n].get(x, False)
        except KeyError:  # node not found
            return False

    def addRouter(self, name, **kwargs):
        """Add a router to the topology

        :param name: the name of the node"""
        return self.addNode(name, isRouter=True, **kwargs)

    def isRouter(self, n):
        """Check whether the given node is a router

        :param n: node name"""
        return self.isNodeType(n, 'isRouter')

    def hosts(self, sort=True):
        # The list si already sorted, simply filter out the routers
        return [h for h in super(IPTopo, self).hosts(sort)
                if not self.isRouter(h)]

    def routers(self, sort=True):
        """Return a list of router node names"""
        return filter(self.isRouter, self.nodes(sort))
