"""Protected instruction comparison, using the reviewed stateless D8 helper resolver.
Only string encoding width and unreachable payload-alignment nops are normalized.
Registers, string values, branch targets, exception regions and executable code stay checked.
"""
import difflib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile
HERE=Path(__file__).resolve().parent
ALLOWED=re.compile(r'com/projectinfinity/kodi/(?:InfinityLiveActivity|CobraProUi|BuildConfig)(?:\$[^/]*)?\.smali$')
# Baksmali --sequential-labels uses :array_0 rather than :array_data_0.
# Run 38224181197 exposed exactly two terminal-return/alignment-only differences.
# The proof still requires a terminal predecessor, no intervening branch/exception
# label, and an actual payload directive immediately after the payload label.
PAYLOAD=re.compile(r'^:(?:(?:pswitch|sswitch|array)_data_\d+|array_\d+)$')
TERMINAL=re.compile(r'^(?:return(?:-void|-object|-wide)?(?:\s|$)|throw\s|goto(?:/16|/32)?\s)')

def normalize(text):
 lines=text.splitlines();result=[]
 for i,line in enumerate(lines):
  if line.strip()=='nop':
   before=i-1
   while before>=0 and (not lines[before].strip() or lines[before].lstrip().startswith('#')):before-=1
   after=i+1
   while after<len(lines) and (not lines[after].strip() or lines[after].lstrip().startswith('#')):after+=1
   payload=after+1
   while payload<len(lines) and not lines[payload].strip():payload+=1
   if before>=0 and TERMINAL.match(lines[before].strip()) and after<len(lines) and PAYLOAD.fullmatch(lines[after].strip()) and payload<len(lines) and lines[payload].strip().startswith(('.packed-switch','.sparse-switch','.array-data')):continue
  line=re.sub(r'^(\s*)const-string/jumbo(?=\s)',r'\1const-string',line)
  if line.strip():result.append(line)
 return '\n'.join(result)

def selftest():
 assert normalize('const-string/jumbo v1, "abc"')==normalize('const-string v1, "abc"')
 assert normalize('const-string v1, "abc"')!=normalize('const-string v1, "abd"')
 assert normalize('const-string v1, "abc"')!=normalize('const-string v2, "abc"')
 for label in (':array_data_0',':array_0'):
  assert normalize('return-void\nnop\n'+label+'\n.array-data 4\n0x3f94fdf4')==normalize('return-void\n'+label+'\n.array-data 4\n0x3f94fdf4')
  assert 'nop' in normalize('move v0, v1\nnop\n'+label+'\n.array-data 4')
  assert 'nop' in normalize('return-void\n:target_0\nnop\n'+label+'\n.array-data 4')
  assert 'nop' in normalize('return-void\n:try_end_0\nnop\n'+label+'\n.array-data 4')
  assert 'nop' in normalize('return-void\nnop\n'+label+'\nmove v0, v1')
  assert normalize('return-void\nnop\n'+label+'\n.array-data 4\n0x3f94fdf4')!=normalize('return-void\n'+label+'\n.array-data 4\n0x3f94fdf5')
 assert normalize('goto :a')!=normalize('goto :b')
 assert normalize('.catch Ljava/lang/Exception; {:a .. :b} :c')!=normalize('.catch Ljava/lang/Exception; {:a .. :d} :c')

def compare(base,candidate,classpath,out):
 selftest()
 spec=importlib.util.spec_from_file_location('approved_bridge_guard',HERE.parent/'chooser-close-owner-2103324/bridge_preservation.py')
 bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
 reports=[]
 with tempfile.TemporaryDirectory(prefix='cobra-delivery-dex-') as directory:
  maps=[]
  for label,apk in (('base',base),('candidate',candidate)):
   root=Path(directory)/label;root.mkdir()
   with zipfile.ZipFile(apk) as archive:
    for name in archive.namelist():
     if re.fullmatch(r'classes\d*\.dex',name):
      dex=root/name;dex.write_bytes(archive.read(name))
      subprocess.run(['java','-cp',classpath,'org.jf.baksmali.Main','disassemble','--sequential-labels',str(dex),'-o',str(root/'smali')],check=True)
   raw={p.relative_to(root/'smali').as_posix():p.read_text() for p in (root/'smali').rglob('*.smali')}
   resolved,bodies,helpers=bridge.resolve({n:normalize(t)+'\n' for n,t in raw.items()});maps.append((raw,resolved))
   reports.append({'side':label,'classes':len(raw),'exact_helper_bodies':sorted(bodies),'helper_containers':sorted(helpers)})
  (oldraw,old),(newraw,new)=maps
  protected=sorted(n for n in old.keys()|new.keys() if not ALLOWED.fullmatch(n))
  changed=[n for n in protected if old.get(n)!=new.get(n)]
  diagnostics=out/'compiler-differences';diagnostics.mkdir(exist_ok=True)
  for n in changed:(diagnostics/(n.replace('/','_')+'.diff')).write_text(''.join(difflib.unified_diff(old.get(n,'').splitlines(True),new.get(n,'').splitlines(True),'approved/'+n,'candidate/'+n)))
  report={'protected_classes_checked':len(protected),'unexpected_differences':changed,'encoding_only_differences':[n for n in protected if oldraw.get(n)!=newraw.get(n) and old.get(n)==new.get(n)],'allowed_class_families':ALLOWED.pattern,'helper_proofs':reports,'decoded_protected_instructions_identical':not changed,'method':'Exact decoded instructions and recursive helper bodies, with encoding-only string width and unreachable payload-padding normalization. Sequential :array_N and offset :array_data_N labels are both recognized; payload values and incoming targets remain checked.'}
  (out/'DEX-PRESERVATION.json').write_text(json.dumps(report,indent=2)+'\n')
  if changed:raise RuntimeError('Protected bytecode changed: '+repr(changed))
  return report
