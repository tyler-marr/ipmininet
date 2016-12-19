"""This modules provides a config object for a router,
that is able to provide configurations for a set of routing daemons.
It also defines the base class for a routing daemon, as well as a minimalistic
configuration for a router."""
import os
import abc
from contextlib import closing
from operator import attrgetter

from .utils import ConfigDict, template_lookup, ip_statement
from ipmininet.utils import require_cmd

import mako

from mininet.log import lg as log


class RouterConfig(object):
    """This class manages a set of daemons, and generates the global
    configuration for a router"""
    def __init__(self, node, daemons=(), sysctl=None,
                 *args, **kwargs):
        """Initialize our config builder

        :param node: The node for which this object will build configurations
        :param daemons: an iterable of active routing daemons for this node
        :param sysctl: A dictionnary of sysctl to set for this node.
                       By default, it enables IPv4/IPv6 forwarding on all
                       interfaces."""
        self._node = node  # The node for which we will build the configuration
        self._daemons = {}  # Active daemons
        map(self.register_daemon, daemons)
        self._cfg = ConfigDict()  # Our root config object
        self._sysctl = {'net.ipv4.ip_forward': 1,
                        'net.ipv6.conf.all.forwarding': 1}
        if sysctl:
            self._sysctl.update(sysctl)
        super(RouterConfig, self).__init__(*args, **kwargs)

    def build(self):
        """Build the configuration for each daemon, then write the
        configuration files"""
        self._cfg.clear()
        self._cfg.password = self._node.password
        self._cfg.name = self._node.name
        # Check that all daemons have their dependencies satisfied
        map(self.register_daemon,
            (c for cls in self._daemons.values()
             for c in cls.DEPENDS if c.NAME not in self._daemons))
        # Build their config
        for name, d in self._daemons.iteritems():
            self._cfg[name] = d.build()
        # Write their config, using the global ConfigDict to handle
        # dependencies
        for d in self._daemons.itervalues():
            cfg = d.render(self._cfg)
            d.write(cfg)

    def cleanup(self):
        """Cleanup all temporary files for the daemons"""
        for d in self._daemons.itervalues():
            d.cleanup()

    def register_daemon(self, cls, **daemon_opts):
        """Add a new daemon to this configuration

        :param cls: Daemon class or object, or a 2-tuple (Daemon, dict)
        :param daemon_opts: Options to set on the daemons"""
        try:
            cls, kw = cls
            daemon_opts.update(kw)
        except TypeError:
            pass
        if cls.NAME in self._daemons:
            return
        if not isinstance(cls, Daemon):
            if issubclass(cls, Daemon):
                cls = cls(self._node, **daemon_opts)
            else:
                raise TypeError('Expected an object or a subclass of '
                                'Daemon, got %s instead' % cls)
        else:
            cls.options.update(daemon_opts)
        self._daemons[cls.NAME] = cls
        require_cmd(cls.NAME, 'Could not find an executable for a daemon!')

    @property
    def sysctl(self):
        """Return an iterator over all sysctl to set on this node"""
        return self._sysctl.iteritems()

    @sysctl.setter
    def sysctl(self, *values):
        """Sets sysctl to particular value.
        :param values: sysctl strings, as `key=val`
        Example:  RouterConfig().sysctl = 'net.ipv4.ip_forward=1',
                                          'net.ipv6.conf.all.forwarding=1'"""
        for value in values:
            try:
                key, val = value.split('=')
                self._sysctl[key] = val
            except ValueError:
                raise ValueError('sysctl must be specified using `key=val` '
                                 'format. Ignoring %s' % value)

    @property
    def daemons(self):
        return sorted(self._daemons.itervalues(), key=attrgetter('PRIO'))

    def daemon(self, key):
        """Return the Daemon object in this config for the given key
        :param key: the daemon name or a daemon class or instance
        :return the Daemon object
        :raise KeyError: if not found"""
        if not isinstance(key, basestring):
            key = key.NAME
        return self._daemons[key]


class Daemon(object):
    """This class serves as base for routing daemons"""
    __metaclass__ = abc.ABCMeta
    # The name of this routing daemon
    NAME = None
    # The priority of this daemon, relative to others
    # (e.g. to define startup order)
    PRIO = 10
    # The eventual dependencies of this daemon on other daemons
    DEPENDS = ()

    def __init__(self, node, **kwargs):
        """:param node: The node for which we build the config
        :param kwargs: Pre-set options for the daemon, see defaults()"""
        self._node = node
        self._startup_line = None
        self.files = []
        self._options = self._defaults(**kwargs)
        super(Daemon, self).__init__()

    @property
    def options(self):
        """Get the options ConfigDict for this daemon"""
        return self._options

    def build(self):
        """Build the configuration tree for this daemon

        :return: ConfigDict-like object describing this configuration"""
        cfg = ConfigDict()
        cfg.logfile = self._options['logfile']
        return cfg

    def cleanup(self):
        """Cleanup the files belonging to this daemon"""
        for f in self.files:
            try:
                os.unlink(f)
            except IOError:
                pass
        self.files = []

    def render(self, cfg, **kwargs):
        """Render the configuration file for this daemon

        :param cfg: The global config for the node
        :param kwargs: Additional keywords args. will be passed directly
                       to the template"""
        self.files.append(self.cfg_filename)
        log.debug('Generating %s\n' % self.cfg_filename)
        try:
            return template_lookup.get_template(self.template_filename)\
                                  .render(node=cfg,
                                          ip_statement=ip_statement,
                                          **kwargs)
        except:
            # Display template errors in a less cryptic way
            log.error('Couldn''t render a config file(',
                      self.template_filename, ')')
            log.error(mako.exceptions.text_error_template().render())
            raise ValueError('Cannot render a configuration [%s: %s]' % (
                self._node.name, self.NAME))

    def write(self, cfg):
        """Write down the configuration for this daemon

        :param cfg: The configuration string"""
        with closing(open(self.cfg_filename, 'w')) as f:
            f.write(cfg)

    @abc.abstractproperty
    def startup_line(self):
        """Return the corresponding startup_line for this daemon"""

    @abc.abstractproperty
    def dry_run(self):
        """The startup line to use to check that the daemon is
        well-configured"""

    def _filename(self, suffix):
        """Return a filename for this daemon and node,
        with the specified suffix"""
        return '%s_%s.%s' % (self.NAME, self._node.name, suffix)

    def _filepath(self, f):
        """Return a path towards a given file"""
        return os.path.join(self._node.cwd, f)

    def _file(self, suffix):
        """Generates a file name in the daemon's node cwd"""
        return self._filepath(self._filename(suffix=suffix))

    @property
    def cfg_filename(self):
        """Return the filename in which this daemon config should be stored"""
        return self._file(suffix='cfg')

    @property
    def template_filename(self):
        return '%s.mako' % self.NAME

    def _defaults(self, **kwargs):
        """Return the default options for this daemon

        :param logfile: the path to the logfile for the daemon"""
        defaults = ConfigDict()
        defaults.logfile = self._file('log')
        # Apply daemon-specific defaults
        self.set_defaults(defaults)
        # Use user-supplied defaults if present
        defaults.update(**kwargs)
        return defaults

    @abc.abstractmethod
    def set_defaults(self, defaults):
        """Update defaults to contain the defaults specific to this daemon"""

    def has_started(self):
        """Return whether this daemon has started or not"""
        return True


class BasicRouterConfig(RouterConfig):
    """A basic router that will run an OSPF daemon"""

    def __init__(self, node, additional_daemons=(), *args, **kwargs):
        """A simple router made of at least an OSPF daemon

        :param additional_daemons: Other daemons that should be used"""
        # Importing here to avoid circular import
        from ospf import OSPF
        # We don't want any zebra-specific settings, so we rely on the OSPF
        # DEPENDS list for that daemon to run it with default settings
        # We also don't want specific settings beside the defaults, so we don't
        # provide an instance but the class instead
        d = [OSPF]
        d.extend(additional_daemons)
        super(BasicRouterConfig, self).__init__(node, daemons=d,
                                                *args, **kwargs)
