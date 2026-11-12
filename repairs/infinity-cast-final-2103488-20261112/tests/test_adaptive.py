"""Actual authenticated HTTP -> private relay -> FFmpeg decode/seek, not a TV PASS."""
from pathlib import Path
import os,subprocess,sys
root=Path(__file__).resolve().parents[3]
t=root/'repairs/infinity-movies-continue-cast-2103486-20261112/cast'
w=Path('/workspace/scratch/cast-final-adaptive88');w.mkdir(exist_ok=True)
fixtures=w/'fixtures/private';fixtures.mkdir(parents=True,exist_ok=True)
for kind in ('hls','fmp4','dash'):
 p=fixtures/kind;p.mkdir(exist_ok=True)
 args=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','testsrc2=size=320x180:rate=24','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','8','-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p','-g','48','-c:a','aac','-b:a','64k']
 if kind=='dash':args+=['-f','dash','-seg_duration','2','-use_template','1','-use_timeline','1',str(p/'stream.mpd')]
 else:
  args+=['-hls_time','2','-hls_playlist_type','vod']
  if kind=='fmp4':args+=['-hls_segment_type','fmp4']
  args+=[str(p/'movie.m3u8')]
 subprocess.run(args,check=True)
multi=fixtures/'multi';multi.mkdir(exist_ok=True)
common=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','testsrc2=size=320x180:rate=24','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','8','-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p','-g','48','-c:a','aac','-b:a','64k']
subprocess.run(common+['-map','0:v','-map','1:a','-hls_time','2','-hls_playlist_type','vod','-master_pl_name','master.m3u8','-var_stream_map','v:0,agroup:audio a:0,agroup:audio,default:yes','-hls_segment_filename',str(multi/'stream_%v/seg%03d.ts'),str(multi/'stream_%v/movie.m3u8')],check=True)
single=fixtures/'single';single.mkdir(exist_ok=True)
subprocess.run(common+['-f','dash','-single_file','1','-use_template','0','-use_timeline','0','-seg_duration','2',str(single/'stream.mpd')],check=True)
(fixtures/'hls/master.m3u8').write_text('#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=500000\nmovie.m3u8?secret=fixture-token\n')
(fixtures/'key.bin').write_bytes(bytes(range(16)))
encrypted=fixtures/'encrypted';encrypted.mkdir(exist_ok=True)
info=w/'key-info';info.write_text('../key.bin?secret=key-token\n'+str(fixtures/'key.bin')+'\n000102030405060708090a0b0c0d0e0f\n')
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(fixtures/'hls/movie.m3u8'),'-c','copy','-hls_time','2','-hls_playlist_type','vod','-hls_key_info_file',str(info),str(encrypted/'movie.m3u8')],check=True)
(fixtures/'drm.m3u8').write_text('#EXTM3U\n#EXT-X-KEY:METHOD=SAMPLE-AES,KEYFORMAT="com.widevine",URI="private-key"\n#EXTINF:2,\nx.ts\n')
(fixtures/'entity.mpd').write_text('<!DOCTYPE MPD [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><MPD xmlns="urn:mpeg:dash:schema:mpd:2011">&xxe;</MPD>')
(fixtures/'drm.mpd').write_text('<MPD xmlns="urn:mpeg:dash:schema:mpd:2011"><Period><AdaptationSet><ContentProtection schemeIdUri="urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed"/></AdaptationSet></Period></MPD>')
cp=os.pathsep.join(map(str,(Path('/workspace/scratch/cast-sdk86/provided-http').glob('*.jar'))))
out=w/'classes';out.mkdir(exist_ok=True)
java=t/'java/com/projectinfinity/kodi'
sources=[java/n for n in ('InfinityCastSource.java','InfinityCastRelay.java','InfinityCastAdaptive.java','InfinityCastDiagnostics.java')]+[Path(__file__).with_name('AdaptiveHTTPTest.java')]
subprocess.run(['java','com.sun.tools.javac.Main','-source','8','-target','8','-cp',cp,'-d',str(out),*map(str,sources)],check=True)
subprocess.run(['java','-cp',str(out)+os.pathsep+cp,'com.projectinfinity.kodi.AdaptiveHTTPTest',str(fixtures.parent)],check=True)
