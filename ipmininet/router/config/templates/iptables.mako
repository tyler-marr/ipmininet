% for table, rules in node.iptables.rules.iteritems():
*${table}
  % for rule in rules:
${rule}
  % endfor
COMMIT
% endfor
