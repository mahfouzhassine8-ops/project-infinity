"""Bounded read-only validation of retained actual Android direct-copy/AAC output."""
from pathlib import Path
from decimal import Decimal
import gzip,hashlib,json,subprocess,sys

def verify(root,out):
 root=Path(root);out=Path(out);init=list(root.rglob('init.mp4'));fixture=list(root.rglob('hevc-eac3.mkv'));assert len(init)==len(fixture)==1
 def inspect(p):
  pipe=isinstance(p,bytes);r=subprocess.run(['ffprobe','-v','error','-probesize','50331648','-analyzeduration','30000000','-show_streams','-show_format','-show_packets','-show_data_hash','sha256','-of','json','pipe:0' if pipe else str(p)],input=p if pipe else None,capture_output=True,timeout=90,check=True);assert len(r.stdout)<16*1024*1024;return json.loads(r.stdout)
 def us(v):return int(Decimal(v)*1000000)
 parts=[];buffers=[init[0].read_bytes()];assert len(buffers[0])<=1048576
 if True:
  for n in range(6):
   found=list(root.rglob(str(n)+'.m4s.gz'));assert len(found)==1
   with gzip.open(found[0],'rb') as g:b=g.read(8388609)
   assert 0<len(b)<=8388608;buffers.append(b);parts.append({'index':n,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
 joined=b''.join(buffers);assert len(joined)<=49*1024*1024;source,actual=inspect(fixture[0]),inspect(joined);video=actual['streams'][0];audio=actual['streams'][1];assert (video['codec_name'],video['width'],video['height'])==('h264',320,180);assert (audio['codec_name'],audio['profile'],audio['sample_rate'],audio['channels'])==('aac','LC','48000',2)
 src=[p for p in source['packets'] if p['stream_index']==0];dst=[p for p in actual['packets'] if p['stream_index']==0];assert len(src)==len(dst)>500;epoch=10000000-us(source['format']['start_time'])
 assert [p['data_hash'] for p in src]==[p['data_hash'] for p in dst],'DIRECT_VIDEO_PACKET_CHANGED'
 assert [us(p['pts_time'])+epoch for p in src]==[us(p['pts_time']) for p in dst],'VIDEO_PRESENTATION_TIMELINE_CHANGED'
 for index in (0,1):
  p=[q for q in actual['packets'] if q['stream_index']==index];d=[us(q['dts_time']) for q in p];assert all(y>x for x,y in zip(d,d[1:])),('NON_MONOTONIC_DTS',index)
 audioPackets=[p for p in actual['packets'] if p['stream_index']==1];assert len(audioPackets)>1000;assert all((n==0 and 'duration' not in p) or int(p['duration'])==1024 for n,p in enumerate(audioPackets));assert all(int(b['pts'])-int(a['pts'])==1024 for a,b in zip(audioPackets,audioPackets[1:])), 'AAC_SAMPLE_GRID_CHANGED'
 # Validate real decode of the concatenated, contiguous fragments, not labels.
 subprocess.run(['ffmpeg','-nostdin','-v','error','-probesize','50331648','-analyzeduration','30000000','-xerror','-i','pipe:0','-map','0:v:0','-map','0:a:0','-f','null','-'],input=joined,check=True,timeout=90)
 receipt={'status':'PASS_RETAINED_ACTUAL_ANDROID_READER_MEDIA','video_packets':len(dst),'video_packet_data':'EXACT_SOURCE_MKV','video_PTS':'EXACT_SOURCE_PLUS_SINGLE_10S_TRANSPORT_EPOCH','DTS':'MONOTONIC_VIDEO_AND_AUDIO','AAC':'LC48k_stereo_exact1024_sample_grid_full_decode; FFprobe may omit first duration, established by nextPTS; allremainingdurations1024','audio_packets':len(audioPackets),'fragments':parts,'source_duration_us':us(source['format']['duration']),'hardware_conversion':'NOT_EXERCISED','physical_TV':'NOT_TESTED'};out.write_text(json.dumps(receipt,indent=2)+'\n');return receipt
if __name__=='__main__':print(json.dumps(verify(sys.argv[1],sys.argv[2]),indent=2))
