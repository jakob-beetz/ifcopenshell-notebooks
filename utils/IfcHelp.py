from IPython.display import IFrame
import json

with open("utils/ifc2x3doc.json", "r") as f:
    
    _doc_urls3 = json.load( f)

with open("utils/ifc4doc.json", "r") as f:
    
    _doc_urls4 = json.load( f)
    
def getHelp3(entname):
    return IFrame(src=_doc_urls3.get(entname.lower()), width='100%', height='500px')
def getHelp4(entname):
    return IFrame(src=_doc_urls4.get(entname.lower()), width='100%', height='500px')