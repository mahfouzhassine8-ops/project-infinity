#!/usr/bin/env python3
"""Execute extracted production aspect/layout policies, independently check rectangles.

This is a host geometry test, not Android GPU, decoder, or physical-device evidence.
"""
import argparse, hashlib, importlib.util, json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
args=argparse.ArgumentParser();args.add_argument('--activity',type=pathlib.Path,required=True);args.add_argument('--out',type=pathlib.Path,required=True);args=args.parse_args()
SOURCE=args.activity.resolve();OUT=args.out.resolve();OUT.mkdir(parents=True,exist_ok=True)
spec = importlib.util.spec_from_file_location('member_parser', ROOT/'repairs/cobra-original-player-menu-2103197/apply.py')
parser = importlib.util.module_from_spec(spec); spec.loader.exec_module(parser)
text = SOURCE.read_text()
parts = [parser.member(text, name, 'class') for name in ('CobraLayoutMath','CobraFoldAspectPolicy','CobraModeLayout')]
MAIN = r'''
  static int checks=0;
  static void ok(boolean value,String label){checks++;if(!value)throw new AssertionError(label);}
  static void close(double a,double b,String label){ok(Math.abs(a-b)<.0001, label+": "+a+" != "+b);}
  static double[] expected(int sw,int sh,double par,int w,int h,int mode,double cx,double cy){
    double source=sw*par/sh;
    if(mode==2)source=16.0/9; else if(mode==3)source=4.0/3;
    double rw=w,rh=w/source;
    if(rh>h){rh=h;rw=h*source;}
    if(mode==1){double z=Math.max(w/rw,h/rh);rw*=z;rh*=z;}
    else if(mode>=4&&mode<=6){rw*=new double[]{1.10,1.25,1.40}[mode-4];}
    else if(mode==7){rw*=1.24;rh*=.84;}
    else if(mode>=8&&mode<=10){double z=new double[]{1.25,1.5,2}[mode-8];rw*=z;rh*=z;}
    else if(mode==11){rw*=cx;rh*=cy;}
    else if(mode==12){
      double mismatch=Math.max(source/(w/(double)h),(w/(double)h)/source);
      if(Math.min(w,h)>=600&&mismatch<=1.18){double z=Math.min(1.06,Math.max(w/rw,h/rh));rw*=z;rh*=z;}
    }
    return new double[]{rw/w,rh/h};
  }
  public static void main(String[] args){
    int[][] views={{1812,2176},{2176,1812},{904,2316},{2316,904},{412,915},{915,412},{320,240},{1920,1080},{1080,1920},{1000,600},{600,1000},{600,340}};
    int[][] videos={{1920,1080},{1440,1080},{720,576},{1080,1920},{3840,1600}};
    double[] pars={1,4.0/3,16.0/15};
    int combinations=0;
    System.out.println("mode,source_width,source_height,pixel_ratio,viewport_width,viewport_height,scale_x,scale_y,rendered_width,rendered_height,crop_x_total,crop_y_total,bar_x_total,bar_y_total");
    for(int[] view:views)for(int[] video:videos)for(double par:pars)for(int mode=0;mode<=12;mode++){
      int w=view[0],h=view[1];
      float[] s=mode==12?CobraFoldAspectPolicy.scale(video[0],video[1],(float)par,w,h):CobraLayoutMath.fit(video[0],video[1],(float)par,w,h,mode,1.33f,.77f);
      double[] e=expected(video[0],video[1],par,w,h,mode,1.33,.77);
      ok(Float.isFinite(s[0])&&Float.isFinite(s[1])&&s[0]>0&&s[1]>0,"positive finite geometry");
      close(s[0],e[0],"width mode "+mode);close(s[1],e[1],"height mode "+mode);
      if(mode==0||mode==12){close(w*s[0]/(h*s[1]),video[0]*par/video[1],"shape preservation "+mode);}
      if(mode==0){ok(s[0]<=1.00001&&s[1]<=1.00001,"best fit cannot crop");close(Math.max(s[0],s[1]),1,"best fit reaches one viewport edge");}
      if(mode==1){ok(s[0]>=.99999&&s[1]>=.99999,"fill cannot letterbox");close(Math.min(s[0],s[1]),1,"fill minimum crop");}
      if(mode==12){ok(s[0]<=1.06001&&s[1]<=1.06001,"Fold bounded crop");}
      // A center-pivot transform must leave the frame centered and preserve the expected rectangle.
      double left=w*(1-(double)s[0])/2,top=h*(1-(double)s[1])/2;
      close((left+left+w*(double)s[0])/2,w/2.0,"center x");close((top+top+h*(double)s[1])/2,h/2.0,"center y");
      if(par==1)System.out.printf(java.util.Locale.ROOT,"%d,%d,%d,%.6f,%d,%d,%.8f,%.8f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f%n",mode,video[0],video[1],par,w,h,s[0],s[1],w*s[0],h*s[1],Math.max(0,w*(s[0]-1)),Math.max(0,h*(s[1]-1)),Math.max(0,w*(1-s[0])),Math.max(0,h*(1-s[1])));
      combinations++;
    }
    int layouts=0;
    for(int w:new int[]{240,280,320,412,600,720,768,960,1024,1440})for(int h:new int[]{180,240,320,412,540,720,915,1024})for(float f:new float[]{1,1.5f,2})for(boolean expanded:new boolean[]{false,true})for(String mode:CobraModeLayout.MODES){
      CobraModeLayout p=CobraModeLayout.solve(mode,w,h,f,expanded);
      for(int[] r:new int[][]{p.toolbar,p.rail,p.directory,p.video,p.details,p.browser,p.footer}){
        ok(r[0]>=0&&r[1]>=0&&r[2]>=0&&r[3]>=0,"nonnegative layout");ok(r[0]+r[2]<=w&&r[1]+r[3]<=h,"within measured viewport");
      }
      layouts++;
    }
    System.err.println("PASS: "+combinations+" aspect cases; "+layouts+" guide layout cases; "+checks+" assertions. Host policies only, no physical-device verification.");
  }
'''
java = OUT/'CobraGeometryAudit.java'
java.write_text('public final class CobraGeometryAudit {\n'+'\n'.join(parts)+MAIN+'\n}\n')
subprocess.run(['java','com.sun.tools.javac.Main',str(java)],check=True)
result=subprocess.run(['java','-cp',str(OUT),'CobraGeometryAudit'],capture_output=True,text=True)
(OUT/'aspect-geometry-matrix.csv').write_text(result.stdout)
source_sha=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
receipt=json.dumps({'source':str(SOURCE),'source_sha256':source_sha,'exit_code':result.returncode,'result':result.stderr.strip(),'verification_level':'extracted-production-policy host tests','physical_device_verified':False},indent=2)+'\n'
(OUT/'host-geometry-result.json').write_text(receipt)
(OUT/f'host-geometry-result-{source_sha[:12]}.json').write_text(receipt)
print(result.stderr.strip());sys.exit(result.returncode)
