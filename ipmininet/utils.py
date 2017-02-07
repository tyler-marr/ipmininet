"""utils: utility functions to manipulate host, interfaces, ..."""
import collections
import os
from mininet.log import lg as log
from ipaddress import ip_address


def require_cmd(cmd, help_str=None):
    """
    Ensures that a command is available in $PATH
    :param cmd: the command to test
    :param help_str: an optional help string to display if cmd is not found
    """
    # Check if cmd is a valid absolute path
    if os.path.isfile(cmd):
        return
    # Try to find the cmd in each directory in $PATH
    for path in os.environ["PATH"].split(os.pathsep):
        path = path.strip('"')
        exe = os.path.join(path, cmd)
        if os.path.isfile(exe):
            return
    if help_str:
        log.error(help_str)
    raise RuntimeError('[%s] is not available in $PATH' % cmd)


def otherIntf(intf):
    """"Get the interface on the other side of a link"""
    l = intf.link
    return (l.intf1 if l.intf2 == intf else l.intf2) if l else None


def realIntfList(n):
    """Return the list of interfaces of node n excluding loopback"""
    return [i for i in n.intfList() if i.name != 'lo']


def is_container(x):
    """Return whether x is a container (=iterable but not a string)"""
    return (isinstance(x, collections.Sequence) and
            not isinstance(x, basestring))


def prefix_for_netmask(mask):
    """Return the prefix length associated to a given netmask.
    Will return garbage if the netmask is unproperly formatted!"""
    ip = ip_address(mask)
    v = ~int(ip) & ~(1 - (1 << ip.max_prefixlen))
    print v
    l = 0
    while v > 0:
        v >>= 1
        l += 1
    return ip.max_prefixlen - l


class L3Router(object):
    """Placeholder class to identify L3 routing devices (primarely routers,
    but this could also be used for a device needing to participate to some
    routing protocol e.g. for TE purposes)"""
    @staticmethod
    def is_l3router_intf(itf):
        """Returns whether an interface belongs to an L3Router
        (in the Mininet meaning: an intf with an associated node)"""
        try:
            return isinstance(itf.node, L3Router)
        except AttributeError:
            return False


def get_set(d, key, default):
    """Attempt to return the value for the given key,
    otherwise intialize it

    :param d: dict
    :param default: constructor"""
    try:
        return d[key]
    except KeyError:
        x = d[key] = default()
        return x
