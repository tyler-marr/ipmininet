hostname ${node.hostname}
password ${node.password}
% if node.ospf.logfile:
log file ${node.ospf.logfile}
% endif
% for section in node.ospf.debug:
debug ospf section
% endfor
!
% for intf in node.ospf.interfaces:
  interface ${intf.name}
  # ${intf.description}
  # Highiest priority routers will be DR
  ip ospf priority ${intf.ospf.priority}
  ip ospf cost ${intf.ospf.cost}
  # dead/hello intervals must be consistent across a broadcast domain
  ip ospf dead-interval ${intf.ospf.dead_int}
  ip ospf hello-interval ${intf.ospf.hello_int}
!
% endfor
router ospf
  router-id ${node.ospf.router_id}
  % for type, prop in node.ospf.redistribute:
  redistribute ${type} metric-type ${prop.metric_type} metric ${prop.metric}
  % endfor
  % for net in node.ospf.networks:
  network ${net.domain.with_prefixlen} area ${net.area}
  % endfor
!
