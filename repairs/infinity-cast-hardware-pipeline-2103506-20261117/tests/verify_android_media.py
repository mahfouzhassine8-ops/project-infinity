"""Read-only media verification on the actual Android-produced fragments."""
from pathlib import Path
from decimal import Decimal
import json,re,subprocess,sys
root=Path(sys.argv[1]);out=Path(sys.argv[2]);source=root/'cast506-pipeline-work/fixtures/hevc-eac3.mkv';media=root/'cast506-pipeline-results/media';converted=media/'converted.mp4'
def inspect(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_packets','-show_data_hash','sha256','-of','json',str(p)]))
def micros(value):return int(Decimal(value)*1000000)
original=inspect(source);actual=inspect(converted);video=next(s for s in actual['streams'] if s['codec_type']=='video');audio=next(s for s in actual['streams'] if s['codec_type']=='audio')
assert (video['codec_name'],video['width'],video['height'],video['level'],video['has_b_frames'])==('h264',1280,720,31,0)
assert all(video[k]=='bt709' for k in ('color_space','color_transfer','color_primaries')) and video['color_range']=='tv'
assert (audio['codec_name'],audio['profile'],audio['sample_rate'],audio['channels'])==('aac','LC','48000',2)
reference=inspect(media/'original-video-AAC-reference.mp4')
ref_audio=[(p['pts_time'],p['dts_time'],p['data_hash']) for p in reference['packets'] if p['stream_index']==1]
new_audio=[(p['pts_time'],p['dts_time'],p['data_hash']) for p in actual['packets'] if p['stream_index']==1]
assert ref_audio==new_audio,'AAC packet bytes or synchronization changed through video conversion'
src=sorted(micros(p['pts_time']) for p in original['packets'] if p['stream_index']==0)
dst=[p for p in actual['packets'] if p['stream_index']==0];assert [micros(p['pts_time'])-10000000 for p in dst]==src,'Original video PTS changed'
for index in (0,1):
 packets=[p for p in actual['packets'] if p['stream_index']==index];times=[micros(p['dts_time']) for p in packets];assert all(b>a for a,b in zip(times,times[1:])),('nonmonotonic DTS',index)
subprocess.run(['ffmpeg','-nostdin','-v','error','-xerror','-i',str(converted),'-map','0:v','-map','0:a','-f','null','-'],check=True)
segments=[]
for p in sorted(media.glob('[0-9]*.m4s')):
 joined=media/('verify-'+p.stem+'.mp4');joined.write_bytes((media/'init.mp4').read_bytes()+p.read_bytes());check=inspect(joined);v=[q for q in check['packets'] if q['stream_index']==0];assert v and v[0]['flags'].startswith('K');subprocess.run(['ffmpeg','-nostdin','-v','error','-xerror','-i',str(joined),'-map','0:v','-map','0:a','-f','null','-'],check=True);segments.append({'name':p.name,'video_packets':len(v),'first_pts_us':micros(v[0]['pts_time']),'last_pts_us':micros(v[-1]['pts_time'])});joined.unlink()
# Frame-by-frame alignment tests actual GPU pixels rather than header claims.
# This catches black, flipped or unrelated frames; it is not a perceptual-quality acceptance claim.
r=subprocess.run(['ffmpeg','-nostdin','-hide_banner','-v','info','-i',str(source),'-i',str(converted),'-lavfi','[0:v]scale=1280:720,settb=1/24000,setpts=N*1000[a];[1:v]settb=1/24000,setpts=N*1000[b];[a][b]ssim','-an','-f','null','-'],capture_output=True,text=True,check=True)
ssim=float(re.search(r'All:([0-9.]+)',r.stderr)[1]);assert ssim>.85,('GPU picture mismatch',ssim)
out.write_text(json.dumps({'status':'PASS_ACTUAL_ANDROID_OUTPUT_MEDIA','video_packets':len(src),'video_PTS':'exact original values plus one fixed10s HLS epoch; DTS monotonic/noB','audio':'AAC-LC48k stereo, full decode; existing continuous AAC adapter unchanged','color':'actual SPS/VUI SDR709 limited','adjacent_independent_fragments':segments,'GPU_frame_alignment_SSIM':ssim,'HDR_hardware_performance':'NOT_TESTED','physical_TV':'NOT_TESTED'},indent=2)+'\n');print(out.read_text())
