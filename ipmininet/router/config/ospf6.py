"""Base classes to configure an OSPF6 daemon"""

from ipaddress import ip_interface

from ipmininet.link import address_comparator
from ipmininet.utils import realIntfList
from .ospf import OSPF, OSPFRedistributedRoute
from .utils import ConfigDict


class OSPF6(OSPF):
    """This class provides a simple configuration for an OSPF6 daemon.
    It advertizes one network per interface (the primary one), and set
    interfaces not facing another L3Router to passive"""
    NAME = 'ospf6d'
    last_routerid = ip_interface("0.0.0.1")
    routerids_taken = []

    def __init__(self, *args, **kwargs):
        super(OSPF6, self).__init__(*args, **kwargs)

    def _build_interfaces(self, interfaces):
        """Return the list of OSPF6 interface properties from the list of
        active interfaces"""
        return [ConfigDict(description=i.describe,
                           name=i.name,
                           # Is the interface between two routers?
                           active=self.is_active_interface(i),
                           priority=i.get('ospf6_priority',
                                          i.get('ospf_priority', self.options.priority)),
                           dead_int=i.get('ospf6_dead_int',
                                          i.get('ospf_dead_int', self.options.dead_int)),
                           hello_int=i.get('ospf6_hello_int',
                                           i.get('ospf_hello_int', self.options.hello_int)),
                           cost=i.igp_metric,
                           # Is the interface forcefully disabled?
                           passive=i.get('igp_passive', False),
                           instance_id=i.get('instance_id', 0),
                           area=i.igp_area)
                for i in interfaces]

    def set_defaults(self, defaults):
        """:param dead_int: Dead interval timer
        :param hello_int: Hello interval timer
        :param cost: metric for interface
        :param priority: priority for the interface, used for DR election
        :param redistribute: set of OSPFRedistributedRoute sources
        :param instance_id: the number of the attached OSPF instance"""
        defaults.instance_id = 0
        super(OSPF6, self).set_defaults(defaults)

    @property
    def routerid(self):
        """Return the OSPF6 router-id for this router. It defaults to the
        most-visible address among this router interfaces. If no IPv4 addresses
        exists for this router, it generates a unique router-id"""
        ip_list = sorted((ip for itf in realIntfList(self._node)
                          for ip in itf.ips()),
                         cmp=address_comparator)
        if len(ip_list) == 0:
            OSPF6.last_routerid += 1
            while OSPF6.last_routerid in OSPF6.routerids_taken:
                OSPF6.last_routerid += 1
            return OSPF6.last_routerid.with_prefixlen.split("/")[0]
        else:
            id = ip_list.pop().ip
            OSPF6.routerids_taken.append(ip_interface(id))
            return id


class OSPF6RedistributedRoute(OSPFRedistributedRoute):
    """A class representing a redistributed route type in OSPF6"""
    pass
