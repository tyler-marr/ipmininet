# See `man radvd.conf` for more details
% for itf in node.radvd.interfaces:
    interface ${itf.name}
    {
        IgnoreIfMissing on;
        AdvSendAdvert on;
        MaxRtrAdvInterval 15;
        % for prefix in itf.ra_prefixes:
        prefix ${prefix.prefix}
        {
             AdvOnLink on;
             AdvAutonomous on;
             AdvValidLifetime ${prefix.valid_lifetime};
             AdvPreferredLifetime ${prefix.preferred_lifetime};
        };
        % endfor
        % for rdnss in itf.rdnss_list:
             RDNSS ${rdnss.ip} {
                 AdvRDNSSLifetime ${rdnss.max_lifetime}; # in seconds (0 means invalid)
             };
             DNSSL local {
                 # list of dnssl specific options
             };
        % endfor
    };
% endfor
