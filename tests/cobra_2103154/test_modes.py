#!/usr/bin/env python3
"""Execute the production layout policy and preserve all non-presentation owners."""
from __future__ import annotations
import argparse,hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from infinity_cobra_2103154_modes import BASELINE,patch,verify
from infinity_cobra_2103153_refinement import method_span
from infinity_cobra_2103152_player_reboot_lock import method_end
HARNESS=r'''
  static int checks=0;
  static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
  static void layout(String mode,int w,int h,float font,boolean groups){
    CobraModeLayout p=CobraModeLayout.solve(mode,w,h,font,groups);
    int[][] boxes={p.toolbar,p.rail,p.directory,p.video,p.details,p.browser,p.footer};
    for(int[] r:boxes){check(r[0]>=0&&r[1]>=0&&r[2]>=0&&r[3]>=0,"nonnegative");check(r[0]+r[2]<=w&&r[1]+r[3]<=h,"inside window "+mode+" "+w+"x"+h);}
    for(int i=0;i<boxes.length;i++)for(int j=i+1;j<boxes.length;j++){
      int[] a=boxes[i],b=boxes[j];if(a[2]==0||a[3]==0||b[2]==0||b[3]==0)continue;
      check(a[0]+a[2]<=b[0]||b[0]+b[2]<=a[0]||a[1]+a[3]<=b[1]||b[1]+b[3]<=a[1],"panes do not overlap "+mode+" "+w+"x"+h+" "+i+"/"+j);
    }
    check(p.browser[2]>=80&&p.browser[3]>=100,"usable browser "+mode+" "+w+"x"+h+" "+Arrays.toString(p.browser));
    check(p.video[2]>0&&p.video[3]>0,"video is reachable");
    check(p.columns>=1&&p.columns<=5,"bounded columns");
    check(CobraModeLayout.cellHeight(mode,font)>=48,"row minimum target");
    if(mode.equals("grid")){check(p.timeSpan>=3600000L,"portrait still has real time window");check(p.channelWidth>0&&p.channelWidth<p.browser[2],"channel column leaves programme area");}
  }
  public static void main(String[] args){
    int[][] sizes={{240,320},{280,600},{320,832},{360,780},{412,915},{540,330},{768,1024},{1024,768},{1920,1080},{2560,1600},{780,360},{640,300}};
    for(String mode:CobraModeLayout.MODES){check(CobraModeLayout.valid(mode),"all modes accepted");for(int[] s:sizes)for(float font:new float[]{1f,1.3f,1.5f,2f})for(boolean groups:new boolean[]{true,false})layout(mode,s[0],s[1],font,groups);}
    check(!CobraModeLayout.valid("wrong"),"invalid mode rejected");
    for(int[] size:new int[][]{{360,800},{960,540}}){Set<String> signatures=new HashSet<>();for(String mode:CobraModeLayout.MODES){CobraModeLayout p=CobraModeLayout.solve(mode,size[0],size[1],1,true);signatures.add(Arrays.toString(p.video)+Arrays.toString(p.browser)+Arrays.toString(p.details)+p.columns);}check(signatures.size()==5,"all five layouts geometrically distinct");}
    check(CobraModeLayout.solve("grid",960,540,1,true).directory[2]>0,"wide TV category rail");
    check(CobraModeLayout.solve("grid",360,800,1,true).directory[2]==0,"cover categories have their own reachable browser route");
    check(CobraModeLayout.solve("mobile",360,800,1,true).footer[3]>0,"mobile has primary bottom navigation");
    check(CobraModeLayout.solve("cards",360,800,1,true).columns>=2,"phone card wall is actually multi-column");
    check(CobraModeLayout.solve("cards",1280,800,1,true).columns>CobraModeLayout.solve("cards",320,800,1,true).columns,"cards expand with available width");
    check(CobraModeLayout.stableId("source:42")==CobraModeLayout.stableId("source:42"),"stable row identity");
    check(CobraModeLayout.stableId("source:42")!=CobraModeLayout.stableId("other:42"),"source-scoped row identity");
    System.out.println("PASS: "+checks+" actual production layout assertions");
  }
'''
def main():
    p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    before=a.before.read_text();after=a.after.read_text();assert hashlib.sha256(before.encode()).hexdigest()==BASELINE
    generated,changed=patch(before);assert generated==after,'Actual final source is not the tested delta'
    try:patch(after)
    except RuntimeError:pass
    else:raise AssertionError('Cannot apply delta twice')
    verify(before,after,changed)
    names=set(re.findall(r'^  (?:@Override(?:[ \t]*\n  |[ \t]+))?(?:private|public|protected) [^\n;=(){}]*\b([A-Za-z0-9_]+)\s*\(',before,re.M));preserved=[]
    for name in sorted(names-set(changed)):
        try:x,y=method_span(before,name);u,v=method_span(after,name)
        except RuntimeError:continue
        assert before[x:y]==after[u:v],name;preserved.append(name)
    for name in ('buildPlayer','startSinglePlayer','startCobraPreview','selectGuidePreview','cobraParseGuide','openMultiView','lockCobraPlayer','onDestroy','returnToInfinity'):
        assert name in preserved,name
    hit=re.search(r'^  private static final class CobraModeLayout\b',after,re.M);assert hit
    clazz=after[hit.start():method_end(after,hit.start())]
    source='import java.util.*;\npublic class CobraModesHarness {\n'+clazz+'\n'+HARNESS+'\n}'
    java=a.out/'CobraModesHarness.java';java.write_text(source)
    subprocess.run(['javac','-d',str(a.out),str(java)],check=True)
    result=subprocess.run(['java','-cp',str(a.out),'CobraModesHarness'],check=True,text=True,capture_output=True)
    (a.out/'results.txt').write_text(result.stdout)
    report={'candidate':2103154,'baseline':2103153,'layout_assertions':int(re.search(r'(\d+) actual',result.stdout).group(1)),'unchanged_existing_methods':len(preserved),'preserved_methods':preserved,'changed_presentation_methods':changed,'all_five_renderers':True,'portrait_tv_grid':True,'device_verified':False,'after_sha256':hashlib.sha256(after.encode()).hexdigest()}
    (a.out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(result.stdout,end='');print('PASS:',len(preserved),'unrelated methods byte-identical')
if __name__=='__main__':main()
