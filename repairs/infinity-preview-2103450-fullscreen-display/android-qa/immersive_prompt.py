"""QA-only measured Got it target for the observed Android immersive tutorial.

Never clicks. The caller must independently verify the live trusted OS window,
its touchable region and two fresh identical targets before sending public input.
"""
import io,re,subprocess
from PIL import Image

def locate(image,region):
 x0,y0,x1,y1=region
 if not (0<=x0<x1<=image.width and 0<=y0<y1<=image.height):raise AssertionError('OS tutorial region outside screenshot')
 pixels=image.convert('RGB').load();points=set()
 for y in range(y0,y1,2):
  for x in range(x0,x1,2):
   r,g,b=pixels[x,y]
   if 45<=r<=160 and 45<=g<=175 and 75<=b<=205 and b>r*1.2 and b>g*1.2:points.add((x,y))
 matches=[]
 while points:
  seed=points.pop();pending=[seed];xs=[];ys=[]
  while pending:
   x,y=pending.pop();xs.append(x);ys.append(y)
   for p in ((x-2,y),(x+2,y),(x,y-2),(x,y+2)):
    if p in points:points.remove(p);pending.append(p)
  left,top,right,bottom=min(xs),min(ys),max(xs)+2,max(ys)+2;w=right-left;h=bottom-top
  if not (w>=60 and h>=30 and 1.2<w/h<4.5 and len(xs)*4>w*h*.3):continue
  crop=image.crop((left+int(w*.2),top+int(h*.25),right-int(w*.2),bottom-int(h*.25))).convert('RGB')
  binary=Image.new('L',crop.size,255);src=crop.load();dst=binary.load()
  for y in range(crop.height):
   for x in range(crop.width):dst[x,y]=0 if min(src[x,y])>180 else 255
  binary=binary.resize((binary.width*4,binary.height*4));encoded=io.BytesIO();binary.save(encoded,format='PNG')
  observed=subprocess.run(['tesseract','stdin','stdout','-l','eng','--psm','7'],input=encoded.getvalue(),capture_output=True,check=True,timeout=3).stdout.decode().strip()
  if re.fullmatch(r'got\s+it',observed,re.I):matches.append([left,top,right,bottom])
 if len(matches)!=1:raise AssertionError('Exactly one measured OS Got it button required: '+str(matches))
 return matches[0]
