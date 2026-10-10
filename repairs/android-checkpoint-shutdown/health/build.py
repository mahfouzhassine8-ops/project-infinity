#!/usr/bin/env python3
"""Exact 2.5.17 code-only update; untouched files retained byte-for-byte."""
import argparse,hashlib,zipfile,json,ast
from pathlib import Path
HERE=Path(__file__).parent
BASELINE_SHA='f659173c224bae64534cd27cd904416d45fdbd7bb5bc9861f2cc98113b647640'
DEFAULT_SHA='9d8d3c331f208cccc1083ceec00924abae027ed28a69335e7eb3cfb2f845a402'
def replace_function(source,name,body):
 tree=ast.parse(source);node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==name)
 lines=source.splitlines(True);return ''.join(lines[:node.lineno-1])+body+'\n'+''.join(lines[node.end_lineno:])
def patch(source):
 assert hashlib.sha256(source.encode()).hexdigest()==DEFAULT_SHA
 source=replace_function(source,'_latest_marker_state',"def _latest_marker_state(lines, failures, successes):\n    from khc_lifecycle import marker_state\n    return marker_state(lines,failures,successes)\n")
 start=source.index('    for key,severity,title,error_token,success_tokens,recovered_detail in auth_rules:')
 end=source.index('    return active,recovered',start)
 source=source[:start]+'''    from khc_lifecycle import scope
    for key,severity,title,error_token,success_tokens,recovered_detail in auth_rules:
        owners={scope(text_lines[i]) for i,low in enumerate(low_lines) if error_token in low}
        for owner in sorted(owners,key=lambda x:x or ''):
            idx=[i for i,low in enumerate(low_lines) if error_token in low and scope(text_lines[i])==owner]
            last_error=max(idx)
            later_success=next((i for i in range(last_error+1,len(low_lines)) if owner and scope(text_lines[i])==owner and any(tok in low_lines[i] for tok in success_tokens)),None)
            base={'key':key+':'+(owner or 'unscoped'),'severity':severity,'title':title,'count':len(idx),'samples':[text_lines[i] for i in idx[:5]],'owner':owner}
            if later_success is not None:
                base.update({'detail':recovered_detail,'recovered':True,'recovery_sample':text_lines[later_success],'resolved_samples':[text_lines[i] for i in idx]})
                recovered.append(base)
            else:
                base.update({'detail':'No later matching verification for this add-on authorization operation.','recovered':False})
                active.append(base)
''' +source[end:]
 # Preserve all original log evidence, moving only positively recovered samples out of current counts.
 marker='    authorization=_authorization_health(lines)\n'
 replacement=marker+'''    from khc_lifecycle import read_checkpoint
    checkpoint=read_checkpoint(HOME)
    recovered_samples={sample for finding in recovered_runtime_findings for sample in finding.get('resolved_samples',finding.get('samples',[]))}
    resolved_errors=[line for line in errors if line in recovered_samples]
    errors=[line for line in errors if line not in recovered_samples]
    actual=[line for line in actual if line not in recovered_samples]
    noisy=[line for line in noisy if line not in recovered_samples]
'''
 assert source.count(marker)==1;source=source.replace(marker,replacement)
 source=source.replace("if (actual or issues or runtime_findings or authorization.get('needs_attention_count',0))", "if (actual or issues or runtime_findings or checkpoint.get('active') or authorization.get('needs_attention_count',0))")
 source=source.replace("'current_errors':len(errors),","'current_errors':len(errors),\n            'resolved_errors':len(resolved_errors),\n            'checkpoint_active':int(checkpoint.get('active',False)),")
 source=source.replace("'current_errors':errors,","'current_errors':errors,\n        'resolved_errors':resolved_errors,\n        'shutdown_checkpoint':checkpoint,")
 source=source.replace("    c=scan.get('counts',{})\n", "    c=scan.get('counts',{})\n")
 source=source.replace("    if cleared:\n        msg+='", "    msg+='\\n\\nShutdown: '+scan.get('shutdown_checkpoint',{}).get('state','UNVERIFIED')\n    if cleared:\n        msg+='",1)
 source=source.replace("    section('HISTORICAL CRASH / SCRIPT ENTRIES','historical_likely_crashes_script_failures')", "    section('RESOLVED / VERIFIED LOG OPERATIONS','resolved_errors')\n    out.extend(['','SHUTDOWN CHECKPOINT',str(scan.get('shutdown_checkpoint',{}))])\n    section('HISTORICAL CRASH / SCRIPT ENTRIES','historical_likely_crashes_script_failures')")
 start=source.index('    try:\n        issues=[]',source.index('def _publish_dashboard_state():'))
 end=source.index('    try:\n        when=time.localtime',start)
 source=source[:start]+'''    try:
        scan=_scan_collect('dashboard-fresh-read')
        needs=scan.get('status')=='NEEDS ATTENTION'
        home.setProperty('KHC.Status','Needs attention' if needs else 'Healthy')
        home.setProperty('KHC.StatusDetail','Current verification needs attention' if needs else 'No current verified failures')
    except Exception:
        home.setProperty('KHC.Status','Unverified')
        home.setProperty('KHC.StatusDetail','Current health scan unavailable')
''' +source[end:]
 ast.parse(source);return source

def build(baseline,output):
 if BASELINE_SHA:assert hashlib.sha256(baseline.read_bytes()).hexdigest()==BASELINE_SHA
 with zipfile.ZipFile(baseline) as z:
  files={n:z.read(n) for n in z.namelist() if not n.endswith('/')};assert len(files)==len([n for n in z.namelist() if not n.endswith('/')])
 prefix='script.kodihealthcenter/'
 files[prefix+'default.py']=patch(files[prefix+'default.py'].decode()).encode()
 xml=files[prefix+'addon.xml'];assert b'version="2.5.17"' in xml;files[prefix+'addon.xml']=xml.replace(b'version="2.5.17"',b'version="2.5.18"',1)
 files[prefix+'khc_lifecycle.py']=(HERE/'khc_lifecycle.py').read_bytes()
 output.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
  for n,data in sorted(files.items()):z.writestr(n,data)
 return files
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();build(a.baseline,a.output);print(a.output)
