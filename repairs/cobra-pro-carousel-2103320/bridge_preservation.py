"""Compare exact API helper bodies at each call site, including protected classes."""
import hashlib,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'cobra-pro-season-2103317'))
import importlib.util
_spec=importlib.util.spec_from_file_location("bridge317",Path(__file__).resolve().parent.parent/"cobra-pro-season-2103317/bridge_preservation.py")
_previous=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_previous)
inherited_outlines=_previous.outlines;CALL=_previous.CALL;OWNERS=_previous.OWNERS;require=_previous.require
ALLOWED=re.compile(r'com/projectinfinity/kodi/(?:InfinityLiveActivity|CobraProUi|BuildConfig)(?:\$[^/]*)?\.smali$')
def verify(old,new,out):
    left,before,lh=inherited_outlines(old);right,after,rh=inherited_outlines(new)
    lh={n:'\n'.join(line for line in t.splitlines() if line.strip()) for n,t in lh.items()}
    rh={n:'\n'.join(line for line in t.splitlines() if line.strip()) for n,t in rh.items()}
    require(lh==rh,'API outline class metadata changed')
    def canonical(text,table):
        def substitute(m):
            require(m[0] in table,'Unresolved API outline call: '+m[0])
            return 'EXACT_API_BODY_'+table[m[0]]
        return CALL.sub(substitute,text)
    checked_old={n:canonical(t,left) for n,t in old.items()}
    checked_new={n:canonical(t,right) for n,t in new.items()}
    outline_names={owner+'.smali' for owner in OWNERS}
    for name in outline_names:
        checked_old[name]=lh[name];checked_new[name]=rh[name]
    protected=[n for n in old.keys()|new.keys() if not ALLOWED.fullmatch(n) and n not in outline_names]
    changed_protected=[n for n in protected if checked_old.get(n)!=checked_new.get(n)]
    details=Path(out)/'compiler-diffs';details.mkdir(exist_ok=True)
    for label,bodies in [('removed',before-after),('added',after-before)]:
        (details/('api-bodies-'+label+'.txt')).write_text('\n\n'.join(sorted(bodies)))
    report={'exact_api_bodies_before':len(before),'exact_api_bodies_after':len(after),
      'protected_classes_checked':len(protected),'protected_class_differences':changed_protected,
      'added_bodies':[hashlib.sha256(x.encode()).hexdigest() for x in sorted(after-before)],
      'removed_bodies':[hashlib.sha256(x.encode()).hexdigest() for x in sorted(before-after)],
      'method':'Canonicalize each API call to SHA-256 of its exact access flags, signature, registers and instructions; compare all protected classes exactly. New or removed bodies are permitted only when no protected call site changes.'}
    (Path(out)/'API-BRIDGE-PRESERVATION.json').write_text(json.dumps(report,indent=2)+'\n')
    require(not changed_protected,'Protected class instructions or referenced API helper bodies changed: '+repr(changed_protected))
    return checked_old,checked_new,report
