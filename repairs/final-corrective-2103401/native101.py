"""Two necessary ownership inputs; retain all other 9402 protected compiler inputs."""
from pathlib import Path
import copy,json,os,sys
import components101 as c
sys.path.insert(0,str(c.HERE.parent/'consolidated-2103398'))
import native98 as previous
old_adapters,module=previous.old_adapters,previous.module
CONTRACT=previous.CONTRACT
COORDINATOR=previous.COORDINATOR
CONTAINER=previous.CONTAINER
PLUGIN='xbmc/filesystem/PluginDirectory.cpp'
PLAYER='xbmc/interfaces/json-rpc/PlayerOperations.cpp'
PATHS={CONTRACT,COORDINATOR}

def patches(before,original,final):
 c.require(set(before)==PATHS,'native change scope mismatch')
 out=dict(before)
 _,release,_=old_adapters();coherence=release.coherence
 pins=json.loads(original[c.UI+'/CONTROLLER-PREIMAGES.json']);nextpins=json.loads(final[c.UI+'/CONTROLLER-PREIMAGES.json'])
 additions=[]
 for endpoint in (*coherence.ENDPOINTS,'default.py'):
  variants=[v for v in coherence.contracts(before[CONTRACT].decode()) if v['script']==c.CC+'/'+endpoint and v['pins']=={c.CC+'/'+n:h for n,h in pins.items()}]
  c.require(len(variants)==1,'exact baseline controller contract absent '+endpoint)
  block=variants[0]['block'].encode()
  for n,p in pins.items():
   if nextpins[n]!=p:block=c.once(block,p.encode(),nextpins[n].encode())
  additions.append(block)
 out[CONTRACT]=c.once(before[CONTRACT],b'  };\n  return *contracts;',b'    // INFINITY_2103401_CC29_EXACT_SOURCES\n'+b'\n'.join(additions)+b'\n  };\n  return *contracts;')
 out[COORDINATOR]=c.once(before[COORDINATOR],b'active["addon_version"].asString() != "0.3.5.28"',b'active["addon_version"].asString() != "0.3.5.28" && active["addon_version"].asString() != "0.3.5.29"')
 return out

def bind(producer,parent,stage,source_commit):
 d,_,_=old_adapters();native=producer/'kodi';checkpoint=producer/'checkpoint-build'
 expected=json.loads((checkpoint/'FOLD100-NATIVE-SOURCE-MAP.json').read_text())
 c.require(len(expected)==9404,'all original native sources required')
 for name,pin in expected.items():c.require(c.digest(native/name)==pin,'baseline native drift '+name)
 links=d.native_build_inventory(native,expected,Path(os.environ['DEPENDS']))
 from zipfile import ZipFile
 archive=parent.parent/'Infinity-2103400-Source-and-Build-Receipts.zip'
 c.require(c.digest(archive)=='ec2d7552544a7fd84f5d71ee5dc6172d870c16ff37b845f56b063346d545151c','exact signed baseline source receipt required')
 with ZipFile(archive) as z:c.require(json.loads(z.read('NATIVE-SOURCE-MAP.json'))==expected,'reconstructed inputs differ from locked native inputs')
 original=c.read_parent(parent);final=c.components(original)
 for name,body in final.items():c.require((stage/name).read_bytes()==body,'component stage mismatch '+name)
 after=patches({p:(native/p).read_bytes() for p in PATHS},original,final)
 aftermap=dict(expected,**{p:c.sha(b) for p,b in after.items()})
 driver=d.module('scoped100_immutable_driver',producer/'repairs/four-repair-20261018/native_ci.py')
 ordering=driver.parent.parent.parent.parent.parent.parent.parent
 paths=[checkpoint/'FOUR-REPAIR-INPUT-DELTA.json',Path(ordering.native_manifest(ordering.stable())).resolve(),checkpoint/'FINAL-SHUTDOWN-SOURCE-PRESERVATION.json']
 locked=json.loads((checkpoint/'LOCKED-2103384-SOURCE-MAP.json').read_text());records=[json.loads(p.read_text()) for p in paths]
 c.require(dict(locked,**records[0]['after'])==expected and all(r['after']==expected for r in records[1:]),'complete compiler ledgers disagree')
 replacements={native/p:b for p,b in after.items()}
 for p,r in zip(paths,records):
  v=copy.deepcopy(r);v['after'].update({k:aftermap[k] for k in PATHS});v['changed']=sorted(set(v.get('changed',[]))|PATHS);v['source_commit']=source_commit
  replacements[p]=(json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
 backups={p:p.read_bytes() for p in replacements}
 try:
  for p,b in replacements.items():p.write_bytes(b)
  c.require(d.native_build_inventory(native,aftermap,Path(os.environ['DEPENDS']))==links,'native build links or unrelated inputs changed')
  proof=dict(source_commit=source_commit,protected_source_commit=c.COMMIT,original_source_count=9404,final_source_count=9404,protected_source_count=9404-len(PATHS),before={p:expected[p] for p in sorted(PATHS)},after={p:aftermap[p] for p in sorted(PATHS)},all_other_sources_byte_identical=True,unchanged_build_links=links,essential_first_guards_unchanged=True,cobra_changed=False,physical_fold_verified=False,final_lock=False)
  for n,v in [('FOLD101-NATIVE-BINDING.json',proof),('FOLD101-NATIVE-SOURCE-MAP.json',aftermap)]: (checkpoint/n).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
  return proof
 except BaseException:
  for p,b in backups.items():p.write_bytes(b)
  raise
