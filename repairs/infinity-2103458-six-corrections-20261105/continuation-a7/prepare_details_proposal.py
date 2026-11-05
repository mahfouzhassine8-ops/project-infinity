"""Inert skin-only proposal; never apply to the overlay."""
from pathlib import Path
import hashlib,json,difflib,xml.etree.ElementTree as E
import polish as P
HERE=Path(__file__).resolve().parent
path=P.BASE/'Includes_InfinityMediaLists.xml';a=path.read_text()
old='<onup>98064</onup>'
new='<onup condition="Control.IsVisible(98066)">98066</onup>\n                <onup>50</onup>'
assert a.count(old)==3
x=E.fromstring(a)
assert [c.get('id') for c in x.findall('.//control') if c.findtext('onup')=='98064']==['98070','98071','98072']
b=a.replace(old,new);y=E.fromstring(b)
assert b.replace(new,old)==a
for cid in ('98070','98071','98072'):
 c=y.find('.//control[@id="'+cid+'"]');up=c.findall('onup')
 assert [(n.text,n.attrib) for n in up]==[('98066',{'condition':'Control.IsVisible(98066)'}),('50',{})]
for tag in ('onclick','ondown','onleft','onright','visible','enable','label','texture','pagecontrol'):
 assert [(n.text,n.attrib) for n in x.findall('.//'+tag)]==[(n.text,n.attrib) for n in y.findall('.//'+tag)]
assert path.read_text()==a
rel=str(path.relative_to(P.ROOT))
(HERE/'DETAILS-NAVIGATION-PROPOSAL.patch').write_text(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel)))
(HERE/'DETAILS-NAVIGATION-PROPOSAL.json').write_text(json.dumps({'status':'UNAPPLIED_REQUIRES_SEPARATE_APPROVAL','file':rel,'before_sha256':hashlib.sha256(a.encode()).hexdigest(),'proposed_sha256':hashlib.sha256(b.encode()).hexdigest(),'affected_controls':[98070,98071,98072],'static_checks':'PASS','behavior_tests':'NOT_RUN_NOT_AUTHORIZED','native_changes':False},indent=2)+'\n')
print('Details navigation proposal prepared; overlay unchanged.')
