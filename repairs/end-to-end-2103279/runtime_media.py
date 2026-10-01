from pathlib import Path
import subprocess
out=Path('runtime-media');out.mkdir(exist_ok=True)
for name,w,h in [('wide',640,360),('classic',480,360),('portrait',180,320),('odd',640,240)]:
 vf='drawgrid=w=40:h=40:t=2:c=white@0.7,drawbox=x=10:y=10:w=80:h=60:color=red:t=fill,drawbox=x=iw-85:y=ih-70:w=70:h=60:color=green:t=fill'
 subprocess.run(['ffmpeg','-loglevel','error','-y','-f','lavfi','-i',f'color=c=0x407bd4:s={w}x{h}:r=12','-f','lavfi','-i','sine=frequency=440:sample_rate=44100','-t','180','-vf',vf,'-c:v','libx264','-preset','ultrafast','-crf','28','-pix_fmt','yuv420p','-c:a','aac','-b:a','48k','-movflags','+faststart',str(out/(name+'.mp4'))],check=True)
subprocess.run(['ffmpeg','-loglevel','error','-y','-i',str(out/'classic.mp4'),'-vf','pad=640:360:80:0:black','-c:v','libx264','-preset','ultrafast','-crf','28','-c:a','copy','-movflags','+faststart',str(out/'baked.mp4')],check=True)
(out/'audit.m3u').write_text('#EXTM3U\n'+''.join(f'#EXTINF:-1 tvg-id="{name}" group-title="Audit",{name.title()}\nhttp://10.0.2.2:8765/{name}.mp4\n' for name in ['wide','classic','portrait','odd','baked']))
(out/'peek.m3u').write_text('#EXTM3U\n#EXTINF:-1 tvg-id="peek" group-title="Audit",Peek\nhttp://10.0.2.2:8765/classic.mp4\n')
