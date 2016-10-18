from .base import Daemon
from .utils import ConfigDict
from ipmininet.utils import realIntfList

RA_DEFAULT_VALID = 86400
RA_DEFAULT_PREF = 14400
DEFAULT_ADV_RDNSS_LIFETIME = 25


class RADVD(Daemon):
    """The base class for all Quagga-derived daemons"""

    # Additional parameters to pass when starting the daemon
    STARTUP_LINE_EXTRA = ''
    NAME = 'radvd'

    def __init__(self, *args, **kwargs):
        super(RADVD, self).__init__(*args, **kwargs)

    def build(self):
        cfg = super(RADVD, self).build()
        # Update with preset defaults
        cfg.update(self.options)
        cfg.debug = self.options.debug
        # Track interfaces
        cfg.interfaces = (self._build_interface(itf)
                          for itf in realIntfList(self._node))
        return cfg

    @staticmethod
    def _build_interface(itf):
        """Build the ConfigDict object representing the interface"""
        ra_list = []
        rdnss_list = []
        for prefix in itf.ra_prefixes:
            if prefix.get('prefix') is not None:
                ra_list.append(
                    ConfigDict(prefix=prefix['prefix'],
                               valid_lifetime=prefix.get('valid_lifetime',
                                                         RA_DEFAULT_VALID),
                               preferred_lifetime=prefix.get('preferred_lifetime',
                                                             RA_DEFAULT_PREF)))
        for rdnss in itf.rdnss_list:
            if rdnss.get('ip') is not None:
                rdnss_list.append(
                    ConfigDict(ip=rdnss['ip'],
                               max_lifetime=rdnss.get('max_lifetime', DEFAULT_ADV_RDNSS_LIFETIME)))
        return ConfigDict(name=itf.name, description=itf.describe,
                          ra_prefixes=ra_list, rdnss_list=rdnss_list)

    def set_defaults(self, defaults):
        defaults.debug = ()
        super(RADVD, self).set_defaults(defaults)

    @property
    def startup_line(self):
        s = 'radvd -C {cfg} -p {pid} -m logfile -l {log} -u root {extra}'\
                .format(cfg=self.cfg_filename,
                        log=self._file('log'),
                        pid=self._file('pid'),
                        extra=self.STARTUP_LINE_EXTRA)
        return s

    @property
    def dry_run(self):
        return 'radvd -c -C {cfg} -u root'\
               .format(cfg=self.cfg_filename)

    def cleanup(self):
        process = self._node.popen("killall radvd")  # TODO Find something better
        process.wait()
        super(RADVD, self).cleanup()
