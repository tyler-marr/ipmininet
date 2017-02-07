% for table, rules in node.ip6tables.rules.iteritems():
*${table}
  % for rule in rules:
${rule}
  % endfor
COMMIT
% endfor
