from xml.dom import minidom

file = minidom.parse('testcaseAIA/fic_DYD.xml')
models = file.getElementsByTagName('blackBoxModel')
crvfile = minidom.parse('testcaseAIA/fic_CRV.xml')

for model in models:
    lib = model.attributes['lib'].value
    dump = minidom.parse('dumpfiles/'+lib+'.so.xml')
    vars = dump.getElementsByTagName('variable')
    for v in vars:
        newvar = crvfile.createElement('curve')
        newvar.attributes['model'] = model.attributes['id'].value
        newvar.attributes['variable'] = v.attributes['name'].value
        crvfile.childNodes[0].appendChild(newvar)
with open('output.xml', 'w') as out:
    crvfile.writexml(out)
    out.close()
