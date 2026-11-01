"""Exact accepted442 owner boundary, including unchanged previously accepted repairs."""
import json,sys
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H))
from build_owner import read_classes,header,methods,APP,HELPER,CHANNEL,digest,save
def verify(root,out):
 before={};after={}
 for p in root.glob('original-part-*'):before.update(read_classes(p))
 for p in root.glob('verify-part-*'):after.update(read_classes(p))
 assert len(before)==7174 and len(after)==7181
 delta={};preserved_methods={}
 for name,raw in before.items():
  assert header(raw)==header(after[name]),name
  a,b=methods(raw),methods(after[name]);changed=sorted(s for s in a.keys()|b.keys() if a.get(s)!=b.get(s))
  if changed:delta[name]=changed
  if name==APP:preserved_methods={s:digest(text.encode()) for s,text in a.items() if s not in changed}
 expected=json.loads((H/'METHOD-ALLOWLIST.json').read_text());assert delta==expected
 assert {n:sorted(methods(after[n])) for n in after.keys()-before.keys()}==json.loads((H/'NEW-CLASS-METHODS.json').read_text())
 # All accepted layouts, indicators, controls, themes, worker/scheduling and data classes are exact.
 protected=[n for n in before if n!=APP and n!='Lcom/projectinfinity/kodi/CobraComponent;']
 assert all(before[n]==after[n] for n in protected)
 result=dict(status='PASS_EXACT442_COBRA_OWNER_PRESERVATION',changed_methods=delta,new_classes=sorted(after.keys()-before.keys()),unchanged_classes=len(protected),original_fields_annotations='IDENTICAL',
  Cards_Pro_Sports_MultiView_themes_PlayerBindings='EXACT_ORIGINAL_CLASSES',native_activity_unchanged_method_count=len(preserved_methods),
  Infinity='OWNER_BUILD_NEVER_ACCESSES_INFINITY; FINAL_APK_COMPARISON_REQUIRED',shutdown='UNCHANGED_NOT_TESTED')
 out.mkdir(parents=True,exist_ok=True);save(out/'OWNER-PRESERVATION.json',result);save(out/'UNCHANGED-ACTIVITY-METHODS.json',preserved_methods)
 print(result['status'],len(protected),len(preserved_methods))
if __name__=='__main__':verify(*(Path(v) for v in sys.argv[1:]))
