# See `man radvd.conf` for more details
% for itf in node.radvd.interfaces:
    % if len(itf.ra_prefixes) != 0:
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
                #clients
                #{
                #    fe80::21f:16ff:fe06:3aab;
                #    fe80::21d:72ff:fe96:aaff;
                #};
            % for rdnss in itf.rdnss_list:
                RDNSS ${rdnss.ip} {
                    AdvRDNSSLifetime ${rdnss.max_lifetime}; # in seconds (0 means invalid)
                };
                DNSSL local {
                    # list of dnssl specific options
                };
            % endfor
        };
    % endif
% endfor
