"""Prove D8 API outline owner/name changes without editing APK instructions."""
import hashlib,json,re
from pathlib import Path
OWNERS=['com/projectinfinity/kodi/Main$$ExternalSyntheticApiModelOutline0','com/projectinfinity/kodi/CobraProUi$Hero$$ExternalSyntheticApiModelOutline0']
METHOD=re.compile(r'^\.method (public static(?: bridge)? synthetic) (m(?:\$\d+)?\([^\n ]+)\n(.*?)^\.end method\n',re.M|re.S)
CALL=re.compile(r'Lcom/projectinfinity/kodi/(?:Main|CobraProUi\$Hero)\$\$ExternalSyntheticApiModelOutline0;->m(?:\$\d+)?\([^\s]+')
def require(ok,message):
    if not ok:raise RuntimeError(message)
def outlines(classes):
    mapping={};bodies=set();headers={}
    for owner in OWNERS:
        name=owner+'.smali';text=classes[name]
        require('.field ' not in text and '<clinit>' not in text and '<init>' not in text.split('# direct methods')[0], 'API outline acquired state')
        methods=list(METHOD.finditer(text));require(bool(methods),'Missing API outline methods')
        headers[name]=METHOD.sub('',text)
        require('.method ' not in headers[name],'Unexpected API outline method')
        for m in methods:
            signature=m[2];descriptor=signature[signature.index('('):]
            exact=m[1]+' '+descriptor+'\n'+m[3]
            digest=hashlib.sha256(exact.encode()).hexdigest();mapping['L'+owner+';->'+signature]=digest;bodies.add(exact)
    return mapping,bodies,headers
def verify(old,new,out):
    left,before,lh=outlines(old);right,after,rh=outlines(new)
    require(before==after,'API bridge instructions, signatures or register counts changed')
    require(lh==rh,'API outline class metadata changed')
    def canonical(text,table):
        def call(m):
            require(m[0] in table,'Unresolved API outline call: '+m[0]);return 'IDENTICAL_API_BRIDGE_'+table[m[0]]
        return CALL.sub(call,text)
    raw_changed=sorted(n for n in old.keys()|new.keys() if old.get(n)!=new.get(n))
    checked_old={n:canonical(t,left) for n,t in old.items()};checked_new={n:canonical(t,right) for n,t in new.items()}
    # Method ownership/order is compiler generated. Their combined exact bodies
    # were proved equal above; keep metadata strict and ignore ownership only.
    for owner in OWNERS:
        name=owner+'.smali';checked_old[name]=lh[name];checked_new[name]=rh[name]
    preserved=[]
    for name in raw_changed:
        if checked_old.get(name)==checked_new.get(name):preserved.append(name)
    report={'api_outline_exact_bodies':len(before),'api_outline_instruction_sets_identical':True,'compiler_only_relocated_classes':preserved,'raw_changed_classes':raw_changed}
    (Path(out)/'API-BRIDGE-PRESERVATION.json').write_text(json.dumps(report,indent=2)+'\n')
    return checked_old,checked_new,report
