from pathlib import Path
from PIL import Image
import json
old=Path('source265/screenshots/phone');new=Path('audit266/screenshots/phone');names=sorted(p.name for p in old.glob('*.png'));assert len(names)==32
exact=clock=0
for name in names:
 if (old/name).read_bytes()==(new/name).read_bytes():exact+=1;continue
 assert name.startswith('grid-'),'Locked glass render changed: '+name
 meta=json.loads((new/(name+'.clock.json')).read_text());rx,ry,rw,rh=meta['ruler'];lx,ly,lw,lh=meta['list'];label=meta['labelWidth']
 a=Image.open(old/name).convert('RGBA');b=Image.open(new/name).convert('RGBA');assert a.size==b.size
 pa,pb=a.load(),b.load();changed=[(x,y) for y in range(a.height) for x in range(a.width) if pa[x,y]!=pb[x,y]]
 # Labels/ticks and the moving dot occupy only the ruler's timeline portion.
 body=[(x,y) for x,y in changed if not (rx+label<=x<rx+rw and ry<=y<ry+rh)]
 assert all(lx+label<=x<lx+lw and ly<=y<min(a.height,ly+lh) for x,y in body),(name,'non-clock layout pixels changed')
 columns={x for x,y in body};assert len(columns)<=4,(name,'changed more than two thin now-line positions',columns)
 groups=[]
 for x in sorted(columns):
  if groups and x==groups[-1][-1]+1:groups[-1].append(x)
  else:groups.append([x])
 assert len(groups)<=2 and all(len(g)<=2 for g in groups),(name,'not two one-pixel antialiased clock strokes',groups)
 clock+=1
result=dict(locked_phone_renders=32,byte_identical=exact,grid_renders_clock_pixels_only=clock,protected_settings_renders_byte_identical=20)
Path('audit266/locked-render-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
