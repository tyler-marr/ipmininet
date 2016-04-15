import os

from .base import Daemon
from .utils import ConfigDict
from ipmininet.utils import realIntfList

# Zebra actions
DENY = 'deny'
PERMIT = 'permit'


class Zebra(Daemon):
    NAME = 'zebra'
    PRIO = 0

    def __init__(self, *args, **kwargs):
        super(Zebra, self).__init__(*args, **kwargs)

    @property
    def startup_line(self):
        return '{name} -f {cfg} -i {pid} -z {api} -k'\
                .format(name=self.NAME,
                        cfg=self.cfg_filename,
                        pid=self._file('pid'),
                        api=self.zebra_socket(self._node))

    @staticmethod
    def zebra_socket(node):
        """Return the path towards the zebra API socket for the given node"""
        return os.path.join(node.cwd, '%s_%s.api' % (Zebra.NAME, node.name))

    def build(self):
        cfg = super(Zebra, self).build()
        # Update with preset defaults
        cfg.update(self.options)
        # Track interfaces
        cfg.interfaces = (ConfigDict(name=itf.name,
                                     description=itf.describe)
                          for itf in realIntfList(self._node))
        return cfg

    def _set_defaults(self, defaults):
        """:param debug: The set of debug events that should be logged
        :param access_lists: The set of AccessList to create, independently
                             from the ones already included by route_maps
        :param route_maps: The set of RouteMap to create
        :param static_routes: The set of StaticRoute to create"""
        defaults.debug = ()
        defaults.access_lists = ()
        defaults.route_maps = ()
        defaults.static_routes = ()


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
        self.prefix = prefix
        self.nexthop = nexthop
