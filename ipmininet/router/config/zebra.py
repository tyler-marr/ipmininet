import os

from ipaddress import ip_network, ip_interface

from .base import Daemon
from .utils import ConfigDict
from ipmininet.utils import realIntfList
from ipmininet.link import address_comparator

# Zebra actions
DENY = 'deny'
PERMIT = 'permit'


class QuaggaDaemon(Daemon):
    """The base class for all Quagga-derived daemons"""

    # Additional parameters to pass when starting the daemon
    STARTUP_LINE_EXTRA = ''

    @property
    def startup_line(self):
        return '{name} -f {cfg} -i {pid} -z {api} -u root {extra}'\
                .format(name=self.NAME,
                        cfg=self.cfg_filename,
                        pid=self._file('pid'),
                        api=self.zebra_socket,
                        extra=self.STARTUP_LINE_EXTRA)

    @property
    def zebra_socket(self):
        """Return the path towards the zebra API socket for the given node"""
        return os.path.join(self._node.cwd,
                            '%s_%s.api' % ('quagga', self._node.name))

    def build(self):
        cfg = super(QuaggaDaemon, self).build()
        cfg.debug = self.options.debug
        return cfg

    def set_defaults(self, defaults):
        """:param debug: the set of debug events that should be logged"""
        defaults.debug = ()
        super(QuaggaDaemon, self).set_defaults(defaults)

    @property
    def dry_run(self):
        return '{name} -Cf {cfg} -u root'\
               .format(name=self.NAME,
                       cfg=self.cfg_filename)


class Zebra(QuaggaDaemon):
    NAME = 'zebra'
    PRIO = 0
    # We want zebra to preserve existing routes in the kernel RT (e.g. those
    # set via ip route)
    STARTUP_LINE_EXTRA = '-k'
    last_routerid = ip_interface("0.0.0.1")

    def __init__(self, *args, **kwargs):
        super(Zebra, self).__init__(*args, **kwargs)

    def build(self):
        cfg = super(Zebra, self).build()
        # Update with preset defaults
        cfg.update(self.options)
        cfg.routerid = self.get_routerid()
        # Track interfaces
        cfg.interfaces = (ConfigDict(name=itf.name,
                                     description=itf.describe)
                          for itf in realIntfList(self._node))
        return cfg

    def set_defaults(self, defaults):
        """:param access_lists: The set of AccessList to create, independently
                             from the ones already included by route_maps
        :param route_maps: The set of RouteMap to create
        :param static_routes: The set of StaticRoute to create"""
        defaults.access_lists = []
        defaults.route_maps = []
        defaults.static_routes = []
        super(Zebra, self).set_defaults(defaults)

    def has_started(self):
        # We override this such that we wait until we have the API socket
        return os.path.exists(self.zebra_socket)

    @classmethod
    def incr_last_routerid(cls):
        cls.last_routerid += 1

    def _equal_routerid(self, n):
        # Check that the most-visible IPv4 address is not in conflict
        # with the current router id
        ip_list = sorted((ip for itf in realIntfList(n)
                          for ip in itf.ips()),
                         cmp=address_comparator)
        if len(ip_list) != 0 \
                and int(ip_list.pop().ip) == int(self.last_routerid):
            return True

        # Check that a router id explicitly set
        # in any other Quagga daemon is not in conflict
        # with the current router id
        for d in n.config.daemons:
            if issubclass(d, QuaggaDaemon) and d != self \
                    and hasattr(d, "routerid") \
                    and int(d.routerid) == int(self.last_routerid):
                return True
        return False

    def get_routerid(self):
        """Computes the default router id for Quagga daemons
        It returns the most-visible IPv4 address among its router interfaces.
        If no IPv4 addresses exists for its router, it generates a unique router id"""
        ip_list = sorted((ip for itf in realIntfList(self._node)
                          for ip in itf.ips()),
                         cmp=address_comparator)
        if len(ip_list) == 0:

            to_visit = realIntfList(self._node)
            # Explore all routers to check that none has the same router id
            while to_visit:
                self.incr_last_routerid()
                visited = set()
                while to_visit:
                    i = to_visit.pop()
                    if i in visited:
                        continue
                    visited.add(i)
                    for n in i.broadcast_domain.routers:
                        if self._equal_routerid(n.node):
                            break  # We need to change the router id
                        to_visit.extend(realIntfList(n.node))
                to_visit = realIntfList(self._node) if to_visit else []
            return self.last_routerid.with_prefixlen.split("/")[0]
        else:
            id = ip_list.pop().ip
            return id


class AccessListEntry(object):
    """A zebra access-list entry"""

    def __init__(self, prefix, action=PERMIT):
        """:param prefix: The ip_interface prefix for that ACL entry
        :param action: Wether that prefix belongs to the ACL (PERMIT)
                        or not (DENY)"""
        self.prefix = prefix
        self.action = action


class AccessList(object):
    """A zebra access-list class. It contains a set of AccessListEntry,
    which describes all prefix belonging or not to this ACL"""

    # Number of ACL
    count = 0

    def __init__(self, name=None, entries=()):
        """Setup a new access-list

        :param name: The name of the acl, which will default to acl## where ##
                     is the instance number
        :param entries: A sequence of AccessListEntry instance,
                        or of ip_interface which describes which prefixes
                        are composing the ACL"""
        AccessList.count += 1
        self.name = name if name else 'acl%d' % AccessList.count
        self._entries = [e if isinstance(e, AccessListEntry)
                         else AccessListEntry(prefix=e)
                         for e in entries]

    def __iter__(self):
        """Iterating over this ACL is basically iterating over all entries"""
        return iter(self._entries)

    @property
    def acl_type():
        """Return the zebra string describing this ACL
        (access-list, prefix-list, ...)"""
        return 'access-list'


class RouteMapEntry(object):
    """A class representing a set of match clauses in a route map with
    an action applied to it"""

    def __init__(self, action=DENY, match=(), prio=10):
        """:param action: Wether routes matching this route map entry will be
                          accepted or not
        :param match: The set of ACL that will match in this route map entry
        :param prio: The priority of this route map entry wrt. other in the
                     route map"""
        self.action = action
        self._match = match
        self.prio = prio

    def __iter__(self):
        """A route map entry is a set of match clauses"""
        return iter(self._match)


class RouteMap(object):
    """A class representing a set of route maps applied to a given protocol"""

    # Number of route maps
    count = 0

    def __init__(self, name=None, maps=(), proto=()):
        """:param name: The name of the route-map, defaulting to rm##
        :param maps: A set of RouteMapEntry,
                     or of (action, [acl, acl, ...]) tuples that will compose
                     the route map
        :param proto: The set of protocols to which this route-map applies"""
        RouteMap.count += 1
        self.name = name if name else 'rm%d' % RouteMap.count
        self._entries = [e if isinstance(e, RouteMapEntry)
                         else RouteMapEntry(action=e[0], match=e[1])
                         for e in maps]
        self.proto = proto

    def __iter__(self):
        """This Routemap is the set of all its entries"""
        return iter(self._entries)

    @staticmethod
    @property
    def describe():
        """Return the zebra description of this route map and apply it to the
        relevant protocols"""
        return 'route-map'


class StaticRoute(object):
    """A class representing a static route"""

    def __init__(self, prefix, nexthop, distance=10):
        """:param prefix: The prefix for this static route
        :param nexthop: The nexthop for this prefix, one of: <IP address,
                        interface name, null0, blackhole, reject>"""
        self.prefix = ip_network(prefix)
        self.nexthop = nexthop
