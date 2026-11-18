"""Exact packet timing under both duration-estimation directions; real NALs."""
from pathlib import Path
p=Path(__file__).with_name('verify_stream.py');ns={'__file__':str(p)};exec(compile(p.read_text().split('source=mem')[0],str(p),'exec'),ns);globals().update({k:v for k,v in ns.items()if not k.startswith('__')})
import sys
sys.path.insert(0,str(H));from sparse_cues import elements,sparse
raw=gzip.open('/dev/shm/cast508-reader/high.mkv.gz','rb').read();rows=[]
def hints(data,value):
 b=bytearray(data);found=0
 for tag,at,start,end in elements(b,0,len(b)):
  if tag!=0x18538067:continue
  for tag,at,start,end in elements(b,start,end):
   if tag!=0x1654ae6b:continue
   for tag,at,start,end in elements(b,start,end):
    if tag!=0xae:continue
    fields=list(elements(b,start,end));video=any(t==0x83 and int.from_bytes(b[a:e],'big')==1 for t,p,a,e in fields)
    if video:
     for t,p,a,e in fields:
      if t==0x23e383:b[a:e]=value.to_bytes(e-a,'big');found+=1
 assert found==1
 return b
for label,source in [('normal',sparse(raw)),('duration_40ms',hints(sparse(raw),40000000)),('duration_42ms',hints(sparse(raw),42000000))]:
 sf=mem(source);expected=packets(sf,'v:0');video=[];audio=[]
 for n in range(3):
  out,init=mem(),mem();row=json.loads(command(['/tmp/cast512-stream-native',fdpath(sf),fdpath(out),'1',str(n),fdpath(init)],text=True));full=mem(contents(init)+contents(out));v=packets(full,'v:0');a=packets(full,'a:0');video+=v;audio+=a
  command(['ffmpeg','-v','error','-xerror','-err_detect','explode','-i',fdpath(full),'-f','null','-']);assert row['payload_peak']<=8388608 and row['source_bytes']<=row['budget'];rows.append(dict(case=label,index=n,output_bytes=row['output_bytes'],payload_peak=row['payload_peak'],origin_us=row['origin_us'],exact_PTS=True))
  for fd in [out,init,full]:os.close(fd)
 assert len(video)==len(expected)==576
 for before,after in zip(expected,video):
  assert before['data_hash']==after['data_hash']
  assert int(Decimal(after['pts_time'])*1000000)-10000000+row['origin_us']==int(Decimal(before['pts_time'])*1000000),(label,before,after)
 assert all(Decimal(video[n]['dts_time'])<Decimal(video[n+1]['dts_time'])for n in range(len(video)-1))
 assert all(Decimal(audio[n]['dts_time'])<Decimal(audio[n+1]['dts_time'])for n in range(len(audio)-1))
 os.close(sf)
report={'status':'PASS_EXACT_BOTH_DURATION_DIRECTIONS_SOURCE_PTS_PACKET_PAYLOAD_AND_DTS','cases':rows,'source_bytes_and_PTS_untouched':'Only declared Matroska default duration hint40/42ms varies; real compressed NALs/timestamps unchanged','AAC':'continuous canonical packets, monotonic sample clock','old_ARM64_failure':'six packet PTSshifts before correction; retained as failed gate44223360240'};(H/'HOST-BOUNDARY-TIMESTAMPS.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'],len(rows))
