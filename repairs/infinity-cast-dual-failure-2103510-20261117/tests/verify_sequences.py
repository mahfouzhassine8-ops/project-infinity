from pathlib import Path
import gzip,struct,json,hashlib,subprocess
H=Path(__file__).resolve().parents[1];new=Path('/tmp/cast510-media');old=Path('/dev/shm/cast508-reader/sequential');rows=[]
def boxes(b,start=0,end=None):
 end=len(b) if end is None else end;at=start
 while at<end:
  assert end-at>=8;n=int.from_bytes(b[at:at+4],'big');header=8
  if n==1:assert end-at>=16;n=int.from_bytes(b[at+8:at+16],'big');header=16
  assert n>=header and n<=end-at
  yield at,n,b[at+4:at+8],header;at+=n
 assert at==end
def sequence(b):
 moofs=[v for v in boxes(b) if v[2]==b'moof'];assert len(moofs)==1
 at,size,_,header=moofs[0];h=[v for v in boxes(b,at+header,at+size) if v[2]==b'mfhd'];assert len(h)==1 and h[0][1]==16;offset=h[0][0]+12;return offset,int.from_bytes(b[offset:offset+4],'big')
assert (new/'init.mp4').read_bytes()==(old/'init.mp4').read_bytes()
for n in range(6):
 before=gzip.decompress((old/(str(n)+'.m4s.gz')).read_bytes());np=new/(str(n)+'.m4s');after=np.read_bytes() if np.exists() else gzip.decompress(Path(str(np)+'.gz').read_bytes());a,v=sequence(before);b,w=sequence(after);assert a==b and v==1 and w==n+1
 expected=bytearray(before);expected[a:a+4]=(n+1).to_bytes(4,'big');assert expected==after,'ONLY_MFHD_MAY_CHANGE'
 rows.append(dict(index=n,before_sequence=v,after_sequence=w,bytes=len(after),sha256=hashlib.sha256(after).hexdigest(),only_mfhd_changed=True))
requests=[json.loads(line) for line in Path('/tmp/cast510-sequences.jsonl').read_text().splitlines()];seen={}
for r in requests:
 assert r['reason']=='none' and not r['exhausted'] and r['bytes']<=r['budget']<=134217728
 if r['index'] in seen:assert seen[r['index']]==r['sha256']
 seen[r['index']]=r['sha256']
cpp='repairs/infinity-six-repairs-2103502-20261116/cast/native/InfinityCastRemux.cpp';root=H.parents[1];prior=subprocess.check_output(['git','show','cd682193dc78da29cfcfef83c5b0d43dec5b89a2:'+cpp],cwd=root,text=True);now=(root/cpp).read_text();extract=lambda s:s[s.index('uint64_t State::readBudget('):s.index('std::vector<uint8_t> State::segment(')];assert extract(prior)==extract(now),'SOURCE_LIMITS_UNCHANGED'
report=dict(status='PASS_EXACT_INIT_PACKETS_TIMESTAMPS_AND_STABLE_FRAGMENT_SEQUENCE',fragments=rows,requests=requests,quota_planner='BYTE_IDENTICAL_TO_SIGNED510',AAC_payload='BYTE_IDENTICAL_TO_SIGNED510',scope='Single-moof source fragments; hardware outputs selected for later Android gate',TV='NOT_TESTED');(H/'SEQUENCE-HOST.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS6 single-moof fragments: only mfhd n+1 changed; exactinit/mdat/packet/timestamps/AAC;14sequential/randomrequests bounded/deterministic')
