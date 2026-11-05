"""Prepare an inert review patch; never write overlay/native source or run UI."""
from pathlib import Path
import difflib,hashlib,json,re,xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
NAME='repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz/unified/DialogVideoInfo.xml'
a=(R/NAME).read_text();b=a
pairs=[('|10|50|','|9011|50|',1),('type="button" id="10"','type="button" id="9011"',1),('Control.HasFocus(10)','Control.HasFocus(9011)',1),('name="control" value="10"','name="control" value="9011"',1),('type="togglebutton" id="15"','type="togglebutton" id="9012"',1),('Container(15)','Container(9012)',10),('\\&quot;15\\&quot;','\\&quot;9012\\&quot;',2)]
counts=[]
for old,new,expected in pairs:
 count=b.count(old);assert count==expected,(old,count,expected)
 b=b.replace(old,new);counts.append({'from':old,'to':new,'occurrences':count})
x=E.fromstring(b);ids=[c.get('id') for c in x.findall('.//control') if c.get('id')]
assert len(ids)==len(set(ids));assert not ({'10','15','11'}&set(ids))
assert {'9011','9012','8','5','50','106'}<=set(ids)
restored=b
for old,new,_ in reversed(pairs):restored=restored.replace(new,old)
assert restored==a
assert (R/NAME).read_text()==a
(HERE/'INFO-CONTROL-PROPOSAL.patch').write_text(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+NAME,tofile='b/'+NAME)))
(HERE/'INFO-CONTROL-PROPOSAL.json').write_text(json.dumps({'status':'INERT_PROPOSAL_NOT_APPLIED','source_file':NAME,'before_sha256':hashlib.sha256(a.encode()).hexdigest(),'proposed_sha256':hashlib.sha256(b.encode()).hexdigest(),'replacements':counts,'static_checks':'PASS_REFERENCE_IDS_ACTIONS_UNIQUE_IDS','behavior_tests':'NOT_RUN_NOT_AUTHORIZED','native_changes':False},indent=2)+'\n')
print('Inert proposal prepared; overlay unchanged; runtime tests NOT RUN.')
