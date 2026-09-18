#!/usr/bin/env python3
"""Execute the real packager's compiled-manifest guard against exact baseline and mutations."""
import argparse,ast,copy,json
from pathlib import Path

def require(ok,message):
 if not ok:raise RuntimeError(message)

def main():
 p=argparse.ArgumentParser();p.add_argument('--packager',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 tree=ast.parse(a.packager.read_text());selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('manifest_tree','verify_manifest_pair')]
 require(len(selected)==2,'Real manifest guard functions missing')
 namespace={'require':require};exec(compile(ast.Module(body=selected,type_ignores=[]),str(a.packager),'exec'),namespace)
 parse=namespace['manifest_tree'];guard=namespace['verify_manifest_pair'];original=(a.baseline/'base-manifest.txt').read_text();candidate=parse((a.baseline/'manifest.txt').read_text())
 for name in ('FOREGROUND_SERVICE_MEDIA_PLAYBACK','WAKE_LOCK'):candidate['children'].append({'tag':'uses-permission','attrs':{'android:name':'"android.permission.'+name+'"'},'children':[]})
 app=next(n for n in candidate['children'] if n['tag']=='application');service=next(n for n in app['children'] if n['tag']=='service' and 'InfinityExtendedBackgroundService' in n['attrs'].get('android:name',''))
 service['attrs']['android:foregroundServiceType']=service['attrs']['android:foregroundServiceType'].replace('0x40000000','0x40000002')
 def serialize(n,depth=0):
  pad='  '*depth;return pad+'E: '+n['tag']+'\n'+''.join(pad+'  A: '+k+'='+v+'\n' for k,v in n['attrs'].items())+''.join(serialize(c,depth+1) for c in n['children'])
 guard(original,serialize(candidate));checks=[{'case':'exact scoped delta accepted','passed':True}]
 mutants=[]
 for name in ('FOREGROUND_SERVICE_MEDIA_PLAYBACK','WAKE_LOCK','FOREGROUND_SERVICE_SPECIAL_USE'):
  for duplicate in (False,True):
   m=copy.deepcopy(candidate);node=next(n for n in m['children'] if name in n['attrs'].get('android:name',''));m['children'].append(copy.deepcopy(node)) if duplicate else m['children'].remove(node);mutants.append(('duplicate ' if duplicate else 'missing ')+name);checks.append((mutants[-1],m))
 for value in ('0x40000000','0x2','0x40000003'):
  m=copy.deepcopy(candidate);ap=next(n for n in m['children'] if n['tag']=='application');svc=next(n for n in ap['children'] if 'InfinityExtendedBackgroundService' in n['attrs'].get('android:name',''));svc['attrs']['android:foregroundServiceType']=value;checks.append(('wrong service type '+value,m))
 m=copy.deepcopy(candidate);ap=next(n for n in m['children'] if n['tag']=='application');svc=next(n for n in ap['children'] if 'InfinityExtendedBackgroundService' in n['attrs'].get('android:name',''));svc['attrs']['android:exported']='0xffffffff';checks.append(('exported service rejected',m))
 m=copy.deepcopy(candidate);m['attrs']['package']='"different.package"';checks.append(('unrelated package mutation rejected',m))
 m=copy.deepcopy(candidate);m['children'].append({'tag':'uses-permission','attrs':{'android:name':'"android.permission.READ_CONTACTS"'},'children':[]});checks.append(('unrelated permission rejected',m))
 results=[checks[0]]
 for title,m in checks[1:]:
  try:guard(original,serialize(m))
  except RuntimeError:results.append({'case':title,'passed':True})
  else:raise RuntimeError('Manifest guard accepted mutation: '+title)
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps({'passed':True,'checks':results},indent=2)+'\n');print('PASS:',len(results),'compiled manifest guard cases')
if __name__=='__main__':main()
