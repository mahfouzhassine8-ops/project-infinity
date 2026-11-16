from pathlib import Path
import subprocess,os,json,hashlib
W=Path('/dev/shm/infinity502-cast-ptl-correction');O=Path('/dev/shm/infinity502-cast-ptl-repro');R=Path('/workspace/infinity-cast96-root-cause');F=Path('/dev/shm/infinity-cast-mkv-local');src=R/'repairs/infinity-six-repairs-2103502-20261116/cast/native/InfinityCastRemux.cpp'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
selection=dict(selected='Review-approved overlay: exact two retained fixtures native inspect/init/segment0; helper truncated/conflicting/layered/noVPS/invalidescape refusals and no partial mutation',source_sha256=sha(src),production_edit_by_reviewer=False)
(W/'SELECTION.json').write_text(json.dumps(selection,indent=2))
def run(a,**kw):
 p=subprocess.run(list(map(str,a)),capture_output=True,text=True,**kw);(W/'commands.log').open('a').write(json.dumps(list(map(str,a)))+'\n'+p.stdout+'\n'+p.stderr+'\n');p.check_returncode();return p.stdout
baseline=R/'repairs/infinity-cast-mkv-2103494-20261113/native/InfinityCastRemux.cpp'
driver=(O/'driver.cpp').read_text().replace(str(baseline),str(src));(W/'driver.cpp').write_text(driver)
flags=['g++','-std=c++17','-O2','-Wno-deprecated-declarations','-I'+str(F/'ffmpeg-6.0.1'),'-I'+str(F/'host-ffmpeg')]
run(flags+[W/'driver.cpp','-ldl','-o',W/'driver'])
env=dict(os.environ,LD_LIBRARY_PATH=':'.join(str(F/'host-ffmpeg'/x) for x in ['libavformat','libavcodec','libavutil']))
rows=[]
for case in ['control','ptl01']:
 run([W/'driver',O/(case+'.mkv'),W/case],env=env)
 m=json.loads((W/case/'inspection.json').read_text());assert m==json.loads((O/'control/inspection.json').read_text())
 for name in ['init.mp4','seg0.m4s']:assert (W/case/name).read_bytes()==(O/'control'/name).read_bytes()
 rows.append(dict(case=case,metadata_equals_retained_control=True,init_equals_retained_control=True,fragment_equals_retained_control=True,codecs=m['codecs']))
b=(O/'control/init.mp4').read_bytes();i=b.index(b'hvcC');size=int.from_bytes(b[i-4:i],'big');good=b[i+4:i-4+size];bad=bytearray(good);bad[1]=0;bad[12]=1
# Parse exact hvcC NAL array framing for fixture-only mutations.
arrays=[];at=23
for k in range(good[22]):
 begin=at;kind=good[at]&63;count=int.from_bytes(good[at+1:at+3],'big');at+=3;nodes=[]
 for n in range(count):
  length=int.from_bytes(good[at:at+2],'big');at+=2;nodes.append((at,length));at+=length
 arrays.append((kind,begin,at,nodes))
assert at==len(good)
vps=next(a for a in arrays if a[0]==32);sps=next(a for a in arrays if a[0]==33)
def rebuild_nal(payload,arr,nodeidx,newnal):
 start,length=arr[3][nodeidx];return bytes(payload[:start-2])+len(newnal).to_bytes(2,'big')+newnal+bytes(payload[start+length:])
def unescape(x):
 out=bytearray();i=0;zeros=0
 while i<len(x):
  c=x[i]
  if zeros==2 and c==3:zeros=0;i+=1;continue
  out.append(c);zeros=min(2,zeros+1) if c==0 else 0;i+=1
 return out
def escape(x):
 out=bytearray();zeros=0
 for c in x:
  if zeros==2 and c<=3:out.append(3);zeros=0
  out.append(c);zeros=min(2,zeros+1) if c==0 else 0
 return bytes(out)
cases={}
cases['truncated']=bytes(bad[:-1])
a,l=sps[3][0];rbsp=unescape(good[a+2:a+l]);rbsp[1]=(rbsp[1]&0xe0)|2
cases['conflicting']=rebuild_nal(bad,sps,0,good[a:a+2]+escape(rbsp))
x=bytearray(bad);x[vps[3][0][0]]|=1;cases['layered']=bytes(x)
x=bytearray(bad[:vps[1]]+bad[vps[2]:]);x[22]-=1;cases['noVPS']=bytes(x)
x=bytearray(bad);a,l=vps[3][0];k=bytes(x).index(b'\x00\x00\x03',a+2,a+l);x[k+3]=4;cases['invalidescape']=bytes(x)
for name,data in cases.items():(W/(name+'.hvcc')).write_bytes(data)
(W/'good.hvcc').write_bytes(good);(W/'repair.hvcc').write_bytes(bad)
helper='''#define INFINITY_REMUX_HOST
#include "SOURCE"
#include <fstream>
#include <iostream>
using namespace InfinityMkv;
std::vector<uint8_t> read(const char* p){std::ifstream f(p,std::ios::binary);return {std::istreambuf_iterator<char>(f),std::istreambuf_iterator<char>()};}
int main(int argc,char**argv){if(argc!=4)return 2;auto b=read(argv[1]);auto before=b;AVCodecParameters p{};p.codec_id=AV_CODEC_ID_HEVC;p.extradata=b.data();p.extradata_size=b.size();try{repairReservedHevcLevel(&p);if(std::string(argv[3])!="success")return 3;if(b!=read(argv[2]))return 4;std::cout<<"SUCCESS_EXACT_EXPECTED_BYTES\\n";}catch(const Failure&e){if(std::string(argv[3])=="success")return 5;if(b!=before)return 6;if(std::string(e.what())!=argv[3])return 7;std::cout<<e.what()<<" NO_PARTIAL_MUTATION\\n";}return 0;}
'''.replace('SOURCE',str(src));(W/'helper.cpp').write_text(helper);run(flags+[W/'helper.cpp','-ldl','-o',W/'helper'])
helperRows=[]
for case in ['good','repair']:
 result=run([W/'helper',W/(case+'.hvcc'),W/'good.hvcc','success'],env=env);helperRows.append(dict(case=case,result=result.strip()))
for case in cases:
 expected='mkv_hevc_ptl_conflict' if case=='conflicting' else 'mkv_hevc_ptl_unverified';result=run([W/'helper',W/(case+'.hvcc'),W/'good.hvcc',expected],env=env);helperRows.append(dict(case=case,result=result.strip()))
report=dict(status='PASS_FOCUSED_PTL_CORRECTION',source_sha256=sha(src),baseline_source_sha256=sha(baseline),native_cases=rows,helper_cases=helperRows,source_review='No blocker in selected bounded PTL reconciliation',source_review_limits='PTL-only parser; deliberately refuses disagreements and layered VPS/SPS. Existing level>=30 configurations pass through unchanged.',physical_root_cause='NOT_PROVEN',physical_receiver='NOT_TESTED',Android='NOT_RUN',production_edits_by_reviewer=False,Java_changes=False,broader_tests=False,files={p.name:sha(p) for p in [W/'check.py',W/'driver.cpp',W/'driver',W/'helper.cpp',W/'helper']})
(W/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
