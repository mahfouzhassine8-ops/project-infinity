"""Actual pinned FFmpeg6 core; authenticated Android I/O is checked separately."""
from pathlib import Path
import collections,hashlib,json,subprocess,sys
work=Path(sys.argv[1]);driver=Path(sys.argv[2]);fixtures=work/'fixtures';fixtures.mkdir(exist_ok=True)
checks=[]
def run(args,**kw):return subprocess.run(list(map(str,args)),check=True,capture_output=True,**kw)
def check(value,label):
 if not value:raise AssertionError(label)
 checks.append(label)
def probe(path):return json.loads(run(['ffprobe','-v','error','-show_streams','-show_packets','-show_data_hash','sha256','-of','json',path]).stdout)
base=fixtures/'h264-aac.mkv'
run(['ffmpeg','-v','error','-y','-f','lavfi','-i','testsrc2=size=320x180:rate=24','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','8','-c:v','libx264','-preset','ultrafast','-g','48','-bf','2','-pix_fmt','yuv420p','-c:a','aac','-b:a','96k',base])
output=work/'h264-copy';result=run([driver,base,output]);meta=json.loads((output/'inspection.json').read_text())
check(meta['video']=='h264' and meta['audio']=='aac','actual source video/audio codec inspection')
check(len(meta['starts_us'])>=4,'actual Matroska cue index, not invented fixed boundaries')
check(all(meta['starts_us'][n]>meta['starts_us'][n-1] for n in range(1,len(meta['starts_us']))),'strict source-derived timeline')
text='#EXTM3U\n#EXT-X-VERSION:7\n#EXT-X-PLAYLIST-TYPE:VOD\n#EXT-X-TARGETDURATION:30\n#EXT-X-MAP:URI="init.mp4"\n'
for n in range(len(meta['starts_us'])-1):text+=f"#EXTINF:{(meta['starts_us'][n+1]-meta['starts_us'][n])/1000000:.6f},\nseg{n}.m4s\n"
text+='#EXT-X-ENDLIST\n';playlist=output/'movie.m3u8';playlist.write_text(text)
a=probe(base);b=probe(playlist)
for kind in ['video','audio']:
 ai=next(x['index'] for x in a['streams'] if x['codec_type']==kind);bi=next(x['index'] for x in b['streams'] if x['codec_type']==kind)
 ap=[x for x in a['packets'] if x['stream_index']==ai];bp=[x for x in b['packets'] if x['stream_index']==bi]
 check([x['data_hash'] for x in ap]==[x['data_hash'] for x in bp],kind+' encoded packet bytes and order preserved, zero transcoding')
 delta=[abs(float(x['pts_time'])-float(y['pts_time'])) for x,y in zip(ap,bp)]
 check(max(delta)<0.002,kind+' original presentation timestamps preserved within source tick')
original=run(['ffmpeg','-v','error','-i',base,'-map','0:v:0','-f','framemd5','-']).stdout
copied=run(['ffmpeg','-v','error','-i',playlist,'-map','0:v:0','-f','framemd5','-']).stdout
frames=lambda v:[x.split(b',')[-1].strip() for x in v.splitlines() if x and not x.startswith(b'#')]
check(frames(original)==frames(copied),'all decoded video frames identical')
audioA=run(['ffmpeg','-v','error','-i',base,'-map','0:a:0','-f','s16le','-']).stdout
audioB=run(['ffmpeg','-v','error','-i',playlist,'-map','0:a:0','-f','s16le','-']).stdout
check(audioA==audioB,'decoded audio identical, no boundary gaps or repeated samples')
run(['ffmpeg','-v','error','-ss','4.5','-i',playlist,'-t','1','-f','null','-']);check(True,'real full-VOD HLS seek and decode')
unsupported=fixtures/'h264-dts.mkv'
run(['ffmpeg','-v','error','-y','-i',base,'-c:v','copy','-c:a','dca','-strict','-2',unsupported])
r=subprocess.run([str(driver),str(unsupported),str(work/'must-not-render')],capture_output=True,text=True)
check(r.returncode!=0 and 'mkv_unsupported_audio_codec' in r.stderr and '"audio":"dts"' in r.stderr,'unsupported DTS identified before media output, no codec masquerading')
check(not (work/'must-not-render').exists(),'unsupported source creates no receiver media')
report=dict(schema=1,status='PASS_REAL_FFMPEG6_MKV_STREAM_COPY',checks=checks,fixture_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),inspection=meta,source_packets={k:len([p for p in a['packets'] if p['stream_index']==i]) for k,i in [('video',0),('audio',1)]},transcoding=False,real_receiver=False,shutdown='NOT_SELECTED')
(work/'CAST-MKV-HOST.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
