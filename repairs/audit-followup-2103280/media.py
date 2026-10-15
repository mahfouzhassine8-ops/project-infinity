from pathlib import Path
import subprocess, runpy
runpy.run_path('repairs/end-to-end-2103279/runtime_media.py')
out=Path('runtime-media')
(out/'spanish.srt').write_text('1\n00:00:00,000 --> 00:02:59,000\nSubtitulo de prueba en espanol\n')
subprocess.run(['ffmpeg','-loglevel','error','-y','-i',str(out/'wide.mp4'),'-i',str(out/'spanish.srt'),'-map','0','-map','1','-c','copy','-c:s:1','mov_text','-metadata:s:s:1','language=spa','-movflags','+faststart',str(out/'wide-bilingual.mp4')],check=True)
(out/'wide-bilingual.mp4').replace(out/'wide.mp4')
subprocess.run(['ffmpeg','-loglevel','error','-y','-i',str(out/'wide.mp4'),'-t','15','-map','0:v','-map','0:a:0','-c','copy','-f','mpegts',str(out/'finite.ts')],check=True)
with (out/'audit.m3u').open('a') as f:f.write('#EXTINF:-1 tvg-id="finite" group-title="Audit",Finite\nhttp://10.0.2.2:8765/finite.ts\n')
