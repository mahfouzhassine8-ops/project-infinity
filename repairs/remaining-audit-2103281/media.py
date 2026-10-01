from pathlib import Path
import runpy
runpy.run_path('repairs/audit-followup-2103280/media.py')
with Path('runtime-media/audit.m3u').open('a') as f:
 for name in ['wide','classic']:
  f.write(f'#EXTINF:-1 tvg-id="sports-{name}" group-title="Sports",Sports {name.title()}\nhttp://10.0.2.2:8765/{name}.mp4\n')
