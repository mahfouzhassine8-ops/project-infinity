"""Verify actual Android media, retaining original H264/AAC/GPU checks."""
from pathlib import Path
import subprocess,sys,json,hashlib
ROOT=Path(__file__).resolve().parents[2];OLD='repairs/infinity-cast-hardware-pipeline-2103506-20261117/tests/verify_android_media.py'
raw=subprocess.check_output(['git','show','caf4109e:'+OLD]);assert raw==(ROOT/OLD).read_bytes()
base=Path(sys.argv[1]);out=Path(sys.argv[2]);control=out.with_name('MEDIA-HARDWARE-CONTROL.json');original_argv=sys.argv[:];sys.argv=[sys.argv[0],str(base),str(control)]
source_origin=int(__import__('decimal').Decimal(json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-of','json',str(base/'cast510-dual-work/fixtures/hevc-eac3.mkv')]))['format']['start_time'])*1000000)
s=raw.decode().replace('cast506-pipeline-work','cast510-dual-work').replace('cast506-pipeline-results','cast510-dual-results');s=s.replace("micros(p['pts_time']) for p in original","micros(p['pts_time'])-source_origin for p in original");exec(compile(s,str(__file__),'exec'),{'__file__':str(__file__),'__name__':'_retained_media_verifier','source_origin':source_origin});sys.argv=original_argv
media=base/'cast510-dual-results/media';work=base/'cast510-dual-work';r=json.loads(control.read_text())
def inspect(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_packets','-show_data_hash','sha256','-of','json',str(p)]))
def micros(v):
 from decimal import Decimal
 return int(Decimal(v)*1000000)
direct_origin=micros(json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-of','json',str(work/'fixtures/direct-hevc.mkv')]))['format']['start_time'])
source=inspect(work/'fixtures/direct-hevc.mkv');direct=inspect(media/'direct-converted.mp4');srcvideo=next(v for v in source['streams'] if v['codec_type']=='video');video=next(v for v in direct['streams'] if v['codec_type']=='video');assert video['codec_name']=='hevc' and video['profile']=='Main 10' and video['level']==153 and (video['width'],video['height'])==(srcvideo['width'],srcvideo['height'])
for name,p in [('source',source),('direct',direct)]:
 packets=[q for q in p['packets'] if q['stream_index']==0]
 if name=='source':expected=[(micros(q['pts_time'])-direct_origin,q['data_hash']) for q in packets]
 else:assert [(micros(q['pts_time'])-10000000,q['data_hash']) for q in packets]==expected,'DIRECT_HEVC_PACKETS_OR_PTS_CHANGED'
for index in(0,1):
 packets=[q for q in direct['packets'] if q['stream_index']==index];times=[micros(q['dts_time']) for q in packets];assert all(b>a for a,b in zip(times,times[1:])),('DIRECT_NONMONOTONIC_DTS',index)
def strict_decode(p):
 r=subprocess.run(['ffmpeg','-nostdin','-v','error','-xerror','-i',str(p),'-map','0:v','-map','0:a','-f','null','-'],capture_output=True,text=True);assert r.returncode==0 and not r.stderr.strip(),('MEDIA_DECODE_ERROR',str(p),r.returncode,r.stderr)
for p in (media/'direct-converted.mp4',media/'converted.mp4'):strict_decode(p)
def boxes(b,start=0,end=None):
 end=len(b) if end is None else end;at=start
 while at<end:
  assert end-at>=8;size=int.from_bytes(b[at:at+4],'big');header=8
  if size==1:assert end-at>=16;size=int.from_bytes(b[at+8:at+16],'big');header=16
  assert size>=header and size<=end-at;yield at,size,b[at+4:at+8],header;at+=size
 assert at==end
sequences={}
for mode in ('','direct-'):
 rows=[]
 for n in range(6):
  p=media/(mode+str(n)+'.m4s');b=p.read_bytes();joined=media/('strict-'+mode+str(n)+'.mp4');joined.write_bytes((media/(mode+'init.mp4')).read_bytes()+b);strict_decode(joined);joined.unlink();moofs=[v for v in boxes(b) if v[2]==b'moof'];assert len(moofs)==1;at,size,_,h=moofs[0];headers=[v for v in boxes(b,at+h,at+size) if v[2]==b'mfhd'];assert len(headers)==1 and headers[0][1]==16;seq=int.from_bytes(b[headers[0][0]+12:headers[0][0]+16],'big');assert seq==n+1;rows.append(dict(index=n,sequence=seq,sha256=hashlib.sha256(b).hexdigest()))
 sequences['hardware' if not mode else 'direct']=rows
r.update(status='PASS_ACTUAL_ANDROID_DUAL_CAST_OUTPUT_MEDIA',direct_HEVC='Main10L153; exactsourcecompressedpacketbytes_and_PTS; monotonicDTS; fullAVdecode',sequences=sequences,Main10_Android_playback='SeeRESULT.direct_HEVC.codec_inventory; unsupportedisNOTPASS',hardware_fixture='GenuineMain8L3_RADL',cache='Successful actualMediaCodec bootstrap followed bynonzero key requests whose inbandPSwere removed; sourceCSDcache reused',source_quota='UNCHANGED',physical_TV='NOT_TESTED',Fold_hardware_performance='NOT_TESTED')
out.write_text(json.dumps(r,indent=2)+'\n');print(out.read_text())
