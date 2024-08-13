import six
from chameleon import PageTemplate
import time
import json
BIGTABLE_ZPT = """\
<table xmlns="http://www.w3.org/1999/xhtml"
xmlns:tal="http://xml.zope.org/namespaces/tal">
<tr tal:repeat="row python: options['table']">
<td tal:repeat="c python: row.values()">
<span tal:define="d python: c + 1"
tal:attributes="class python: 'column-' + %s(d)"
tal:content="python: d" />
</td>
</tr>
</table>""" % six.text_type.__name__

def alu():
    input_file = './Che/tables_data.txt'
    with open(input_file, 'r') as f:
        tables = [json.loads(line) for line in f]
    tmpl = PageTemplate(BIGTABLE_ZPT)
    total_time = 0.0
    generation_count = 1
    start = time.time()
    for i in range(generation_count):
        table = tables[i]
        options = {'table': table}
        data = tmpl.render(options=options)
    end = time.time()
    average_time = (end - start) / generation_count
    return {"average_execution_time": average_time}

listoftheresult = []
for i in range(5):
    st = time.time()
    result = alu()
    et = time.time()
    if i>1:
        listoftheresult.append(et-st)
print(sum(listoftheresult)/len(listoftheresult))
print("Now ready for BW Tests")
while True:
    alu()