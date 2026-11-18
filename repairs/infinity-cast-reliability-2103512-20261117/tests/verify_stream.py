"""Actual Cast native output, real high-byte-rate media, no persistent movie files."""
import os,gzip,subprocess,json,hashlib,struct,time
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];H=Path(__file__).resolve().parents[1]
ENV=dict(os.environ);fp='/dev/shm/infinity-cast-mkv-local/host-ffmpeg/';ENV['LD_LIBRARY_PATH']=':'.join(fp+x for x in ['libavformat','libavcodec','libavutil','libswresample'])
def command(args,**kwargs):
 p=subprocess.run(args,capture_output=True,env=ENV,**kwargs)
 if p.returncode:raise AssertionError((args[:2],p.returncode,p.stderr[-2500:]))
 return p.stdout
def fdpath(fd):return f'/proc/{os.getpid()}/fd/{fd}'
def mem(data=b''):
 fd=os.memfd_create('cast512-test');os.write(fd,data);return fd
def contents(fd):os.lseek(fd,0,0);return os.read(fd,os.fstat(fd).st_size)
def boxes(data,start=0,end=None):
 end=len(data) if end is None else end
 while start<end:
  size,kind=struct.unpack_from('>I4s',data,start);head=8
  if size==1:size=struct.unpack_from('>Q',data,start+8)[0];head=16
  assert size>=head and size<=end-start
  yield start,size,kind,head;start+=size
 assert start==end
def packets(fd,selector):
 raw=command(['ffprobe','-v','error','-select_streams',selector,'-show_packets','-show_data_hash','sha256','-show_entries','packet=pts_time,dts_time,duration_time,data_hash,flags','-of','json',fdpath(fd)])
 return json.loads(raw)['packets']
source=mem(gzip.open('/dev/shm/cast508-reader/high.mkv.gz','rb').read());report={'fixture_sha256':hashlib.sha256(contents(source)).hexdigest(),'source_raster':'320x180 H264, real coded high byte rate; not a4K hardware qualification','results':[]}
original=packets(source,'v:0');allvideo=[];allaudio=[]
for stride,index in [(2,0),(2,1),(2,2),(3,0),(2,1)]:
 out,init=mem(),mem();raw=command(['/tmp/cast512-stream-native',fdpath(source),fdpath(out),str(stride),str(index),fdpath(init)],text=True);r=json.loads(raw);media=contents(out);initial=contents(init);sequences=[];types=[]
 for at,size,kind,head in boxes(media):
  types.append(kind.decode())
  if kind==b'moof':
   found=[struct.unpack_from('>I',media,p+12)[0] for p,n,k,h in boxes(media,at+head,at+size) if k==b'mfhd'];assert len(found)==1;sequences+=found
 assert types==['moof','mdat']*(len(types)//2);assert sequences==list(range(index*32+1,index*32+1+len(sequences)))
 assert len(sequences)>1 and r['largest_chunk']<=65536 and r['payload_peak']<=8388608 and r['source_bytes']<=r['budget']
 full=mem(initial+media);video=packets(full,'v:0');audio=packets(full,'a:0')
 for p in [video,audio]:assert all(float(p[n]['dts_time'])<float(p[n+1]['dts_time']) for n in range(len(p)-1))
 command(['ffmpeg','-v','error','-xerror','-err_detect','explode','-i',fdpath(full),'-f','null','-'])
 # Packet payloads and presentation timestamps remain unchanged by streaming.
 begin=index*stride*4;end=min(begin+stride*4,24)
 expected=[p for p in original if begin<=float(p['pts_time'])<end]
 assert [p['data_hash'] for p in video]==[p['data_hash'] for p in expected]
 assert all(int(Decimal(a['pts_time'])*1000000)-10000000+r['origin_us']==int(Decimal(b['pts_time'])*1000000) for a,b in zip(video,expected))
 if stride==2 and len(report['results'])<3:allvideo+=video;allaudio+=audio
 r.update(moofs=len(sequences),sha256=hashlib.sha256(media).hexdigest(),strict_decode=True,video_packets=len(video),audio_packets=len(audio));report['results'].append(r)
 for fd in [out,init,full]:os.close(fd)
assert report['results'][1]['sha256']==report['results'][4]['sha256']
assert len(allvideo)==len(original)
assert all(float(allaudio[n]['dts_time'])<float(allaudio[n+1]['dts_time']) for n in range(len(allaudio)-1))
report['status']='PASS_STREAMING_MULTI_MOOF_REAL_PACKETS';(H/'HOST-STREAM.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
