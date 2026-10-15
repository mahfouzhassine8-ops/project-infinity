#!/usr/bin/env python3
"""Executable extracted production policy/navigation/reset tests, not real-device video decoding."""
from pathlib import Path
import argparse,importlib.util,json,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));import apply
REPO=ROOT.parents[1]

def extracted(text,name,kind='method'):
 a,b=apply.span(text,name,kind);return text[a:b]
def execute(out,name,source):
 out.mkdir(parents=True,exist_ok=True);path=out/(name+'.java');path.write_text(source)
 subprocess.run(['javac','-encoding','UTF-8','--release','8','-d',str(out),str(path)],check=True)
 r=subprocess.run(['java','-cp',str(out),name],capture_output=True,text=True,timeout=30)
 (out/(name+'.txt')).write_text(r.stdout+r.stderr);print(r.stdout)
 if r.returncode:raise RuntimeError(r.stderr)
 return r.stdout

def main():
 p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 before=a.baseline.read_text();after,receipt=apply.patch(before);out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
 (out/'InfinityLiveActivity.java.in').write_text(after)
 try:apply.patch(after)
 except ValueError:pass
 else:raise AssertionError('Patch allowed twice')
 for k in ['startCobraPreview','buildPlayer','cobraAttachVideo','cobraDisposePlayer','loadGuideAsync','cobraParseGuide','startSinglePlayer','onDestroy','returnToInfinity','cobraLayoutGuide']:
  assert extracted(before,k)==extracted(after,k),k
 # Preserve the entire existing geometry assertion body, execute it on the NEW production class.
 txt=(REPO/'tests/cobra_2103154/test_modes.py').read_text();harness=txt.split("HARNESS=r'''",1)[1].split("'''",1)[0]
 stdout=execute(out/'modes','CobraModesHarness','import java.util.*;public class CobraModesHarness{\n'+extracted(after,'CobraModeLayout','class')+harness+'}')
 policies='\n'.join(extracted(after,n,'class') for n in ('CobraAppearancePolicy','CobraNavigationEpoch','CobraModeLayout'))
 tests=r'''
  static int checks;static void check(boolean b,String s){checks++;if(!b)throw new AssertionError(s);}
  public static void main(String[] args){
    for(String mode:new String[]{"system","light","dark","oled","bad"})for(String variant:new String[]{"dark","oled","bad"})for(boolean night:new boolean[]{true,false}){
      String expected="system".equals(mode)?night?"oled".equals(variant)?"oled":"dark":"light":"light".equals(mode)?"light":"oled".equals(mode)?"oled":"dark";
      check(expected.equals(CobraAppearancePolicy.effective(mode,variant,night)),"independent palette "+mode+variant+night);
    }
    CobraNavigationEpoch nav=new CobraNavigationEpoch();
    for(int i=0;i<500;i++){
      long movies=nav.advance();check(nav.accepts(movies),"current Movies may render");
      long live=nav.advance();check(!nav.accepts(movies),"late Movies rejected on Live TV");check(nav.accepts(live),"current live epoch");
      long series=nav.advance();long settings=nav.advance();check(!nav.accepts(series),"late series rejected on Settings");check(nav.accepts(settings),"latest settings owns stage");
    }
    for(int w:new int[]{280,320,360,412,540,658})for(int h:new int[]{720,915,1536})for(float font:new float[]{1f,1.5f,2f}){
      CobraModeLayout p=CobraModeLayout.solve("grid",w,h,font,true);
      check(p.browser[0]==0&&p.browser[2]==w,"portrait guide spans viewport");
      if(w<540)check(p.video[2]==w,"portrait preview spans width");
      check(p.browser[3]>=h/3,"EPG majority after compact header");
      check(p.browser[0]+p.browser[2]==w,"no unused right column");
    }
    for(int w:new int[]{760,768,960,1280,1920})for(int h:new int[]{540,768,1080}){
      CobraModeLayout p=CobraModeLayout.solve("grid",w,h,1,true);check(p.directory[2]>0,"groups dock on wide viewports");
      check(p.browser[2]>w*.50f,"EPG remains primary workspace");check(p.browser[0]+p.browser[2]==w,"wide guide reaches right edge");
    }
    System.out.println("PASS: "+checks+" new production geometry, palette and navigation policy assertions");
  }
'''
 policies_out=execute(out/'policies','Policies','import java.util.*;public class Policies{'+policies+tests+'}')
 # Execute the actual stop method against an exact minimal view/decoder adapter. The original
 # leaves last dimensions equal to the upcoming same-sized viewport, suppressing its layout callback.
 support='''int mCobraLastGuideWidth=360,mCobraLastGuideHeight=800;Object mCobraModeLayout=new Object();String mCobraRenderedMode="grid";Object mCobraGuideRuler,mCobraPreviewTexture,mCobraPreviewHost,mCobraGuideShell,mCobraGuideVideo,mCobraGuideAdapter,mCobraGuideList;
void stopCobraPreviewPlayerOnly(){}void cobraRememberModeScroll(){}
'''
 reset=[]
 for name,text,expect in [('BeforeReset',before,'false'),('AfterReset',after,'true')]:
  method=extracted(text,'stopCobraPreview')
  body='public static void main(String[]args){'+name+' h=new '+name+'();h.stopCobraPreview();boolean willLayout=h.mCobraLastGuideWidth!=360||h.mCobraLastGuideHeight!=800;if(willLayout!='+expect+')throw new AssertionError("reset reproduction");System.out.println("PASS: '+name+' same-sized return triggers layout="+willLayout);}'
  reset.append(execute(out/name,name,'public class '+name+'{'+support+method+body+'}'))
 # Callback is tested at DELIVERY time, not just when work is scheduled.
 navsrc=extracted(after,'CobraNavigationEpoch','class')+extracted(after,'cobraPublishNavigation')
 delivery='''private final CobraNavigationEpoch mCobraNavigation=new CobraNavigationEpoch();ArrayList<Runnable> queue=new ArrayList<>();void publishCobraUi(Runnable r){queue.add(r);}int rendered;
public static void main(String[]args){Delivery h=new Delivery();long old=h.mCobraNavigation.advance();h.cobraPublishNavigation(old,()->h.rendered++);h.mCobraNavigation.advance();h.queue.remove(0).run();if(h.rendered!=0)throw new AssertionError("stale callback ran");h.cobraPublishNavigation(h.mCobraNavigation.current(),()->h.rendered++);h.queue.remove(0).run();if(h.rendered!=1)throw new AssertionError("fresh callback lost");System.out.println("PASS: obsolete Movies/Shows UI rejected at delivery, current response retained");}
'''
 deliver=execute(out/'delivery','Delivery','import java.util.*;public class Delivery{'+navsrc+delivery+'}')
 report={**receipt,'inherited_geometry':stdout,'new_policy':policies_out,'reset_reproduction':reset,'delivery':deliver,'physical_video_decode_verified':False}
 (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
