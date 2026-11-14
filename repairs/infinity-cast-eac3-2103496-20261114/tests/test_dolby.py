"""Real FFmpeg6 before/after Dolby init and unchanged AAC output, no receiver claim."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
HERE=Path(__file__).resolve().parent;TASK=HERE.parent;ROOT=TASK.parents[1]
OLD=ROOT/'repairs/infinity-cast-mkv-2103494-20261113';CPP=OLD/'native/InfinityCastRemux.cpp'
BASE_SOURCE='cf85829c860f96f0ca2e38d2c4ba485ae6ca32d6'
WORK=Path(sys.argv[1]).resolve();FIXED=Path(sys.argv[2]).resolve();WORK.mkdir(exist_ok=True)
def run(args,**kw):return subprocess.run(list(map(str,args)),check=True,capture_output=True,**kw)
def sha(p):return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
def probe(p):return json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-show_packets','-show_data_hash','sha256','-of','json',p]).stdout)
baseline=WORK/'baseline496.cpp';baseline.write_bytes(subprocess.check_output(['git','-C',str(ROOT),'show',BASE_SOURCE+':'+str(CPP.relative_to(ROOT))]));assert sha(baseline)=='e05ad4fc180e0d90f2d4b6a38445a66e5e46b9b1994a457961502d4685eee3a9'
driver_source=WORK/'baseline-driver.cpp';driver_source.write_text((OLD/'tests/native_driver.cpp').read_text().replace('#include "../native/InfinityCastRemux.cpp"','#include "'+str(baseline)+'"'))
BASE=WORK/'baseline-driver';run(['g++','-std=c++17','-O2','-Wno-deprecated-declarations','-I'+str(WORK/'ffmpeg-6.0.1'),'-I'+str(WORK/'host-ffmpeg'),driver_source,'-ldl','-o',BASE])
checks=[];cases={}
def check(value,name):
 if not value:raise AssertionError(name)
 checks.append(name)
def playlist(out,meta):
 text='#EXTM3U\n#EXT-X-VERSION:7\n#EXT-X-PLAYLIST-TYPE:VOD\n#EXT-X-TARGETDURATION:30\n#EXT-X-MAP:URI="init.mp4"\n'
 for n in range(len(meta['starts_us'])-1):text+='#EXTINF:%.6f,\nseg%d.m4s\n'%((meta['starts_us'][n+1]-meta['starts_us'][n])/1e6,n)
 p=out/'movie.m3u8';p.write_text(text+'#EXT-X-ENDLIST\n');return p
for audio,channels in [('eac3',2),('eac3',6),('ac3',6)]:
 key=audio+'_'+str(channels)+'ch';source=WORK/'fixtures'/('hevc-'+key+'.mkv');run(['ffmpeg','-v','error','-y','-i',WORK/'fixtures/hevc-aac.mkv','-c:v','copy','-c:a',audio,'-b:a','384k','-ac',str(channels),'-ar','48000',source])
 before=subprocess.run([str(BASE),str(source),str(WORK/(key+'-baseline'))],capture_output=True,text=True)
 check(before.returncode!=0 and 'mkv_mux_header_failed' in before.stderr,key+' reproduces496 before real Dolby packets')
 out=WORK/(key+'-fixed');run([FIXED,source,out]);meta=json.loads((out/'inspection.json').read_text());check(meta['audio']==audio,key+' actual codec retained')
 init=(out/'init.mp4').read_bytes();check((b'dec3' if audio=='eac3' else b'dac3') in init,key+' real Dolby configuration box, no guessed header');check(b'moof' not in init and b'mdat' not in init,key+' bootstrap contains no media samples')
 movie=playlist(out,meta);a=probe(source);b=probe(movie);details={}
 for kind in ['video','audio']:
  ai=next(s['index'] for s in a['streams'] if s['codec_type']==kind);bi=next(s['index'] for s in b['streams'] if s['codec_type']==kind);ap=[p for p in a['packets'] if p['stream_index']==ai];bp=[p for p in b['packets'] if p['stream_index']==bi]
  check([p['data_hash'] for p in ap]==[p['data_hash'] for p in bp],key+' '+kind+' every encoded packet unchanged, no dropped or duplicated primer')
  delta=max(abs(float(x['pts_time'])-meta['origin_us']/1e6-(float(y['pts_time'])-float(b['format']['start_time']))) for x,y in zip(ap,bp));check(delta<.002,key+' '+kind+' source clock within original2ms')
  details[kind]=dict(packets=len(ap),max_pts_error_seconds=delta)
  if kind=='audio':check(a['streams'][ai]['channels']==b['streams'][bi]['channels']==channels,key+' full channel layout retained')
 def decoded(p,kind):return run(['ffmpeg','-v','error','-i',p,'-map','0:'+kind+':0','-f','framemd5' if kind=='v' else 's16le','-']).stdout
 def frames(v):return [x.split(b',')[-1].strip() for x in v.splitlines() if x and not x.startswith(b'#')]
 check(frames(decoded(source,'v'))==frames(decoded(movie,'v')),key+' all decoded video frames identical')
 check(decoded(source,'a')==decoded(movie,'a'),key+' all decoded audio samples identical')
 run(['ffmpeg','-v','error','-ss','2.5','-i',movie,'-t','0.5','-f','null','-']);check(True,key+' indexed HLS seek and decode')
 cases[key]=dict(fixture_sha256=sha(source),inspection=meta,packets=details)
# Exactly the previously working bytes, including negative source origin and B frames.
for key in ['h264','hevc']:
 source=WORK/'fixtures'/(key+'-aac.mkv');before=WORK/(key+'-aac-baseline');after=WORK/(key+'-aac-fixed');run([BASE,source,before]);run([FIXED,source,after]);names=[p.name for p in before.iterdir() if p.suffix in ['.mp4','.m4s']];check(all((before/p).read_bytes()==(after/p).read_bytes() for p in names),key+' AAC init and every out-of-order fragment byte-identical to496')
# No silently dropped malformed audio, and no incompatible codec changes beneath one init.
source=WORK/'fixtures/hevc-eac3_2ch.mkv';bad=bytearray(source.read_bytes());packets=probe(source)['packets']
for p in packets:
 if p['stream_index']==1:
  begin=int(p['pos']);at=bad.find(b'\x0b\x77',begin,begin+32);assert at>=begin,'synthetic Dolby packet location';bad[at:at+2]=b'\0\0'
invalid=WORK/'fixtures/invalid-eac3.mkv';invalid.write_bytes(bad)
r=subprocess.run([str(FIXED),str(invalid),str(WORK/'invalid-must-not-render')],capture_output=True,text=True)
check(r.returncode!=0 and 'mkv_invalid_dolby_frame' in r.stderr and not (WORK/'invalid-must-not-render').exists(),'malformed Dolby refused before init or delivery, no silent audio dropping')
for name,ch in [('stereo',2),('surround',6)]:run(['ffmpeg','-v','error','-y','-i',WORK/'fixtures/hevc-aac.mkv','-t','2','-vn','-c:a','eac3','-b:a','384k','-ac',str(ch),'-f','eac3',WORK/(name+'.ec3')])
joined=WORK/'changing.ec3';joined.write_bytes((WORK/'stereo.ec3').read_bytes()+(WORK/'surround.ec3').read_bytes());changed=WORK/'fixtures/changing-eac3.mkv';run(['ffmpeg','-v','error','-y','-i',WORK/'fixtures/hevc-aac.mkv','-f','eac3','-i',joined,'-map','0:v:0','-map','1:a:0','-c','copy',changed])
r=subprocess.run([str(FIXED),str(changed),str(WORK/'changed-must-refuse')],capture_output=True,text=True)
check(r.returncode!=0 and 'mkv_init_changed' in r.stderr,'midstream Dolby configuration change refused; source identity and init remain verified')
report=dict(schema=1,status='PASS_REAL_DOLBY_HEADER_STREAM_COPY_AND_496_AAC_PRESERVATION',checks=checks,cases=cases,transcoding=False,shutdown='NOT_SELECTED',physical_receiver='NOT_TESTED',baseline_cpp_sha256=sha(baseline),source_hashes={str(p.relative_to(ROOT)):sha(p) for p in [CPP,TASK/'build.py',Path(__file__)]})
(WORK/'CAST-DOLBY-HOST.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2))
