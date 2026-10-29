"""Finite UI-only candidate journey. Four explicitly synthetic loopback streams.
No root, app-data injection, restart, stop, Close, profile reset or Infinity.
"""
import json,re,subprocess,time,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from android_probe import adb
COLORS=[(36,79,172),(43,150,69),(121,59,158),(204,118,29)]

def generate_media(root):
 root.mkdir(exist_ok=True)
 for i,color in enumerate(COLORS,1):
  rgb='0x'+''.join('%02x'%n for n in color)
  subprocess.run(['ffmpeg','-loglevel','error','-y','-f','lavfi','-i','color=c='+rgb+':s=320x180:r=12','-f','lavfi','-i','sine=frequency='+str(300+i*110)+':sample_rate=44100','-t','1800','-vf','drawtext=text=QA'+str(i)+'_%{n}:fontcolor=white:fontsize=22:x=8:y=8','-c:v','libx264','-preset','ultrafast','-crf','28','-g','24','-pix_fmt','yuv420p','-c:a','aac','-b:a','32k','-movflags','+faststart',str(root/('qa'+str(i)+'.mp4'))],check=True)
 (root/'qa.m3u').write_text('#EXTM3U\n'+''.join('#EXTINF:-1 tvg-id="qa%d" group-title="Cobra QA",QA %d\nhttp://10.0.2.2:8765/qa%d.mp4\n'%(i,i,i) for i in range(1,5)))

def bounds(n):return tuple(map(int,re.findall(r'\d+',n.get('bounds',''))))
def center(b):return (b[0]+b[2])//2,(b[1]+b[3])//2

def journey(out):
 out.mkdir(parents=True);steps=[];report={'scope':'EXACT_SIGNED_COBRA_CANDIDATE_UI_ONLY_SYNTHETIC_STREAMS','physical_Fold':'NOT_RUN','shutdown':'NOT_RUN','steps':steps};seq=0
 def ui():
  nonlocal seq
  adb('shell','uiautomator','dump','/sdcard/cobra-qa-journey.xml');raw=adb('shell','cat','/sdcard/cobra-qa-journey.xml');seq+=1;(out/('%03d-ui.xml'%seq)).write_text(raw)
  return list(ET.fromstring(raw).iter('node'))
 def labels(nodes):return [n.get('text','') or n.get('content-desc','') for n in nodes]
 def find(pattern,nodes):
  for n in reversed(nodes):
   if re.search(pattern,n.get('text','')) or re.search(pattern,n.get('content-desc','')):
    b=bounds(n)
    if len(b)==4 and b[2]>b[0] and b[3]>b[1]:return n
  return None
 def scroll_menu(nodes):
  # Native sheets clip offscreen accessibility nodes. Scroll only the top
  # sheet's ScrollView, never a covered Guide list.
  for n in reversed(nodes):
   if n.get('class')=='android.widget.ScrollView' and n.get('scrollable')=='true':
    b=bounds(n);x=(b[0]+b[2])//2;lo=b[3]-max(30,(b[3]-b[1])//8);hi=b[1]+max(30,(b[3]-b[1])//8)
    adb('shell','input','swipe',str(x),str(lo),str(x),str(hi),'350');steps.append({'scrolled_native_sheet':list(b)});return True
  return False
 def tap(pattern,attempts=8):
  for i in range(attempts):
   nodes=ui();n=find(pattern,nodes)
   if n is not None:
    x,y=center(bounds(n));adb('shell','input','tap',str(x),str(y));steps.append({'tap':pattern});return
   scroll_menu(nodes);time.sleep(.5)
  raise RuntimeError('Visible UI action missing: '+pattern+'; labels='+repr(labels(nodes)))
 def wait(pattern,attempts=10):
  for i in range(attempts):
   nodes=ui()
   if find(pattern,nodes) is not None:return nodes
   time.sleep(.5)
  raise RuntimeError('UI state missing: '+pattern+'; labels='+repr(labels(nodes)))
 def shot(name):
  p=out/(name+'.png');p.write_bytes(subprocess.check_output(['adb','exec-out','screencap','-p'],timeout=15));return p
 def panes():
  rects=set()
  for n in ui():
   b=bounds(n)
   if n.get('class')=='android.widget.FrameLayout' and 'hold for channel actions' in n.get('content-desc','') and n.get('long-clickable')=='true' and len(b)==4 and b[2]-b[0]>100 and b[3]-b[1]>100:rects.add(b)
  return sorted(rects,key=lambda b:(b[2]-b[0])*(b[3]-b[1]),reverse=True)
 def menu():
  boxes=panes();assert boxes,'No accessible live pane bounds'
  x,y=center(boxes[0]);adb('shell','input','swipe',str(x),str(y),str(x),str(y),'700');wait('^Move Screen$|^Use audio here$');return boxes
 def arrangement(name,count):
  menu();tap('^Multi-View layout$');wait('^Fit$');shot('picker-'+name.replace('/','-').replace(' ','-'));tap('^'+re.escape(name)+'$');time.sleep(.3);shot('layout-'+str(count)+'-'+name.replace('/','-').replace(' ','-'));steps.append({'applied_arrangement':name,'screen_count':count})
 def add(name):
  menu();tap('^Add screen$');tap('^All$');tap('^'+re.escape(name)+'(?:\n|$)');time.sleep(1)
 try:
  tap('ADD TV SOURCE');tap('M3U / M3U8 playlist');nodes=ui();fields=[n for n in nodes if n.get('class')=='android.widget.EditText'];assert len(fields)==3
  for index,value in enumerate(['CobraQA','http://10.0.2.2:8765/qa.m3u']):
   # IME repositions the dialog after focus. Re-read every field rectangle;
   # never reuse pre-keyboard coordinates (which can hit outside/cancel).
   current=[n for n in ui() if n.get('class')=='android.widget.EditText'];assert len(current)==3
   x,y=center(bounds(current[index]));adb('shell','input','tap',str(x),str(y))
   focused=[n for n in ui() if n.get('class')=='android.widget.EditText'];assert focused[index].get('focused')=='true'
   adb('shell','input','text',value);steps.append({'filled_field':index})
  tap('^TEST & SAVE$')
  nodes=wait('^QA 1,|^Multi-View$',15)
  # Source validation can already open fullscreen. Its covered Guide remains
  # in the accessibility tree; never click that background's QA1/details row.
  if find('^Multi-View$',nodes) is None:
   if find('^Pause preview$',nodes) is None:tap('^QA 1,');time.sleep(2)
   tap('^Fullscreen$')
  shot('one-channel');tap('^Multi-View$');wait('^Pick a second screen$');tap('^All$');tap('^QA 2(?:\n|$)');time.sleep(2);shot('two-playing')
  for name in ['50/50','Picture in Picture — Bottom Right','Picture in Picture — Bottom Left','Picture in Picture — Top Right','Picture in Picture — Top Left']:arrangement(name,2)
  arrangement('50/50',2);boxes=panes();assert len(boxes)>=2
  boxes=sorted(boxes[:2],key=lambda b:(b[1],b[0]));a,b=center(boxes[0]),center(boxes[1])
  before=Image.open(shot('swap-before')).convert('RGB');ids=[]
  for point in (a,b):
   pixel=before.getpixel(point);d=[sum((pixel[j]-c[j])**2 for j in range(3)) for c in COLORS];assert min(d)<2500,('Live fixture color absent',pixel);ids.append(d.index(min(d)))
  adb('shell','input','draganddrop',str(a[0]),str(a[1]),str(b[0]),str(b[1]),'800');time.sleep(.5)
  after=Image.open(shot('swap-after')).convert('RGB');actual=[]
  for point in (a,b):
   pixel=after.getpixel(point);d=[sum((pixel[j]-c[j])**2 for j in range(3)) for c in COLORS];assert min(d)<2500;actual.append(d.index(min(d)))
  assert actual==ids[::-1],('Actual rendered pane swap failed',ids,actual);steps.append({'actual_pixel_swap':{'before':ids,'after':actual}})
  add('QA 3')
  for name in ['Main + Two','Main + Two Overlays','Three Columns']:arrangement(name,3)
  add('QA 4')
  for name in ['2×2 Grid','Main + Three','Main + Three Overlays']:arrangement(name,4)
  menu();nodes=ui();assert find('^Add screen$',nodes) is None;assert find('^Move Screen$',nodes) is not None;assert find('^Arrange Screen$',nodes) is not None
  shot('four-capacity-native-menu');report['status']='PASS_LIVE_FIXTURE_ALL11_AND_RENDERED_SWAP_MOBILE';report['mode_limit']='Mobile actual Android; all5 modes host. No physical/decoder-state identity claim from pixels.'
 finally:
  report.setdefault('status','FAILED_AT_RECORDED_UI_STEP');(out/'OUTCOME.json').write_text(json.dumps(report,indent=2)+'\n');shot('last-screen');(out/'logcat.txt').write_text(adb('logcat','-d','-v','threadtime',check=False));(out/'meminfo.txt').write_text(adb('shell','dumpsys','meminfo','com.projectinfinity.kodi',check=False))
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--generate-media',type=Path);p.add_argument('--out',type=Path);a=p.parse_args()
 if a.generate_media:generate_media(a.generate_media)
 if a.out:journey(a.out)
