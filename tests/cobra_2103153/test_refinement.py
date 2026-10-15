#!/usr/bin/env python3
"""Execute extracted production algorithms + final-source preservation checks.

The XML adapter below uses the JDK streaming parser solely for host execution.
These are not Android device/decoder/provider playback acceptance tests.
"""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from infinity_cobra_2103153_refinement import BASELINE_SHA256, method_span, verify
from infinity_cobra_2103152_player_reboot_lock import method_end


def extract_class(text,name):
    hit=re.search(r'^  private (?:static )?(?:final )?class '+name+r'\b',text,re.M)
    if hit is None: raise AssertionError(name)
    return text[hit.start():method_end(text,hit.start())]


def extract_method(text,name):
    a,b=method_span(text,name); return text[a:b]

XML_INTERFACE='''package org.xmlpull.v1;
public interface XmlPullParser {
 int START_DOCUMENT=0,END_DOCUMENT=1,START_TAG=2,END_TAG=3,TEXT=4;
 void setFeature(String name,boolean value) throws XmlPullParserException;
 void setInput(java.io.InputStream stream,String encoding) throws XmlPullParserException;
 int getEventType() throws XmlPullParserException;
 int next() throws XmlPullParserException,java.io.IOException;
 String getName();String getText();String getAttributeValue(String namespace,String name);
}'''
XML_ADAPTER='''package android.util;
import org.xmlpull.v1.*;import javax.xml.stream.*;
public final class Xml {
 public static XmlPullParser newPullParser(){return new Adapter();}
 static final class Adapter implements XmlPullParser {
  XMLStreamReader reader;int event=START_DOCUMENT;
  public void setFeature(String n,boolean v){}
  public void setInput(java.io.InputStream in,String encoding)throws XmlPullParserException{
   try{XMLInputFactory f=XMLInputFactory.newFactory();f.setProperty(XMLInputFactory.SUPPORT_DTD,false);f.setProperty("javax.xml.stream.isSupportingExternalEntities",false);reader=f.createXMLStreamReader(in);}
   catch(XMLStreamException e){throw new XmlPullParserException(e.toString());}
  }
  public int getEventType(){return event;}
  public int next()throws XmlPullParserException{
   try{while(reader.hasNext()){int e=reader.next();if(e==XMLStreamConstants.START_ELEMENT)return event=START_TAG;if(e==XMLStreamConstants.END_ELEMENT)return event=END_TAG;if(e==XMLStreamConstants.CHARACTERS||e==XMLStreamConstants.CDATA)return event=TEXT;}return event=END_DOCUMENT;}
   catch(XMLStreamException e){throw new XmlPullParserException(e.toString());}
  }
  public String getName(){return reader.getLocalName();}public String getText(){return reader.getText();}public String getAttributeValue(String ns,String name){return reader.getAttributeValue(ns,name);}
 }
}'''
HARNESS=r'''
  static int checks=0;
  static void check(boolean okay,String label){checks++;if(!okay)throw new AssertionError(label);}
  static void near(double a,double b,String label){check(Math.abs(a-b)<0.0001,label+": "+a+" != "+b);}
  static String time(long ms){SimpleDateFormat f=new SimpleDateFormat("yyyyMMddHHmmss Z",Locale.US);f.setTimeZone(TimeZone.getTimeZone("UTC"));return f.format(new Date(ms));}
  static String program(String id,long start,long stop,String title){return "<programme channel=\""+id+"\" start=\""+time(start)+"\" stop=\""+time(stop)+"\"><title>"+title+"</title></programme>";}
  static final class Fake {final String id;int disposals;Fake(String key){id=key;}}
  static void testStore(){
    CobraTileStore<Fake> s=new CobraTileStore<>();int[] creates={0};CobraTileStore.Factory<Fake> f=k->{creates[0]++;return new Fake(k);};
    CobraTileStore.Disposer<Fake> d=v->{v.disposals++;check(v.disposals==1,"no duplicate release");};
    s.reconcile(Arrays.asList("A","B"),f,d);Fake a=s.get("A"),b=s.get("B");
    s.reconcile(Arrays.asList("A","B","C"),f,d);Fake c=s.get("C");check(creates[0]==3,"only tile 3 created");check(s.get("A")==a&&s.get("B")==b,"2 to 3 retains player/view identity");
    s.reconcile(Arrays.asList("A","B","C","D"),f,d);Fake fourth=s.get("D");check(creates[0]==4,"only tile 4 created");
    for(int i=0;i<100;i++){s.reconcile(Arrays.asList("D","C","B","A"),f,d);s.reconcile(Arrays.asList("A","B","C","D"),f,d);check(s.get("A")==a&&s.get("C")==c,"reflow retains values");}
    check(creates[0]==4&&a.disposals==0&&b.disposals==0,"no reallocation on reflow");
    s.reconcile(Arrays.asList("A","C","D"),f,d);check(b.disposals==1&&a.disposals==0&&c.disposals==0,"remove releases only selected");
    Fake transferred=s.take("C");check(transferred==c&&c.disposals==0,"multi to single transfer does not release");
    boolean duplicate=false;try{s.reconcile(Arrays.asList("A","A"),f,d);}catch(IllegalArgumentException e){duplicate=true;}check(duplicate&&s.get("A")==a,"duplicates rejected before mutation");
    boolean tooMany=false;try{s.reconcile(Arrays.asList("A","B","C","D","E"),f,d);}catch(IllegalArgumentException e){tooMany=true;}check(tooMany&&creates[0]==4,"maximum capacity enforced");
    boolean failed=false;try{s.reconcile(Arrays.asList("A","E","X"),k->{if(k.equals("X"))throw new IllegalStateException("test");return new Fake(k);},d);}catch(IllegalStateException e){failed=true;}check(failed&&s.get("A")==a&&s.get("D")==fourth,"failed addition preserves committed peers");
    s.clear(d);check(a.disposals==1&&fourth.disposals==1&&c.disposals==0,"close excludes transferred player");s.clear(d);check(s.isEmpty(),"idempotent clear");
  }
  static void testLayout(){
    int[][] screens={{320,832},{360,780},{412,915},{768,1024},{1024,768},{1920,1080},{2560,1600},{780,360}};
    for(int[] screen:screens)for(int count=1;count<=4;count++){
      long area=0;ArrayList<int[]> rects=new ArrayList<>();
      for(int i=0;i<count;i++){int[] r=CobraLayoutMath.tile(i,count,screen[0],screen[1]);rects.add(r);check(r[0]>=0&&r[1]>=0&&r[2]>0&&r[3]>0&&r[0]+r[2]<=screen[0]&&r[1]+r[3]<=screen[1],"tile in bounds");area+=(long)r[2]*r[3];}
      check(area==(long)screen[0]*screen[1],"all space used");
      for(int i=0;i<count;i++)for(int j=i+1;j<count;j++){int[] a=rects.get(i),b=rects.get(j);check(a[0]+a[2]<=b[0]||b[0]+b[2]<=a[0]||a[1]+a[3]<=b[1]||b[1]+b[3]<=a[1],"no overlap");}
    }
    Random random=new Random(3153);
    for(int i=0;i<3000;i++){
      int vw=100+random.nextInt(3000),vh=100+random.nextInt(2000),w=200+random.nextInt(2000),h=200+random.nextInt(2000);float pixel=i%2==0?1:1.2f;
      float[] fit=CobraLayoutMath.fit(vw,vh,pixel,w,h,0,1,1);near(w*(double)fit[0]/(h*fit[1]),vw*(double)pixel/vh,"Best Fit source aspect");check(fit[0]<=1.0001&&fit[1]<=1.0001,"Best Fit never crops");
      for(int mode=0;mode<12;mode++){float[] scale=CobraLayoutMath.fit(vw,vh,pixel,w,h,mode,.8f,1.2f);check(Float.isFinite(scale[0])&&Float.isFinite(scale[1])&&scale[0]>0&&scale[1]>0,"all aspect modes finite");}
    }
    float[] normal=CobraLayoutMath.fit(1920,1080,1,360,800,0,1,1),custom=CobraLayoutMath.fit(1920,1080,1,360,800,11,1.2f,.8f);
    near(custom[0]/normal[0],1.2,"independent width");near(custom[1]/normal[1],.8,"independent height");
  }
  static void testTime(){
    long a=CobraGuideMath.parseTime("20260916210000 -0400"),b=CobraGuideMath.parseTime("20260917010000 +0000");check(a>0&&a==b,"timezone offset");check(a==CobraGuideMath.parseTime("202609170100 +0000"),"12 digits");check(a==CobraGuideMath.parseTime("20260917010000Z"),"Z");check(a==CobraGuideMath.parseTime("20260917010000"),"missing zone UTC");
    for(String bad:new String[]{"20260230210000 +0000","20260917010000 +2560","not a time","20260917","20260917010000 GMT","20261317010000 +0000",""})check(CobraGuideMath.parseTime(bad)==0,"reject invalid date "+bad);
    Map<String,String> aliases=new HashMap<>();CobraGuideMath.alias(aliases,"  Nicktoons   West ","west");check("west".equals(aliases.get("nicktoons west")),"normalized alias");CobraGuideMath.alias(aliases,"Nicktoons West","another-region");check("".equals(aliases.get("nicktoons west")),"ambiguous mapping suppressed");check(!aliases.containsKey("nicktoons"),"no fuzzy regional stripping");check(CobraGuideMath.id(" null ").isEmpty(),"null EPG id normalized");
    near(CobraGuideMath.progress(10,20,15),.5,"progress");near(CobraGuideMath.progress(20,10,15),0,"invalid interval");near(CobraGuideMath.progress(10,20,30),1,"progress clamped");
    float[] range=CobraGuideMath.interval(900,1500,1000,1000);near(range[0],0,"left clipped");near(range[1],.5,"duration width");check(CobraGuideMath.interval(2000,3000,1000,1000)==null,"right boundary exclusive");check(CobraGuideMath.interval(0,1000,1000,1000)==null,"left boundary exclusive");
  }
  void testXml()throws Exception{
    long now=System.currentTimeMillis()/1000*1000;
    String xml="<?xml version=\"1.0\"?><tv><channel id=\" nick.us \" ><display-name>Nicktoons</display-name></channel>"+program("nick.us",now+3600000,now+7200000,"Later &amp; Next")+program("nick.us",now-1000,now+3599000,"Current &amp; Live")+"<programme channel=\"nick.us\" start=\"bad\" stop=\"bad\"><title>Bad</title></programme></tv>";
    CobraEpgData data=cobraParseGuide(new ByteArrayInputStream(xml.getBytes(StandardCharsets.UTF_8)));check(data.programs.get("nick.us").size()==2,"invalid intervals ignored");check(data.programs.get("nick.us").get(0).title.equals("Current & Live"),"entity and sort");check(data.aliases.get("nicktoons").equals("nick.us"),"channel display-name mapped");
    ByteArrayOutputStream compressed=new ByteArrayOutputStream();try(java.util.zip.GZIPOutputStream zip=new java.util.zip.GZIPOutputStream(compressed)){zip.write(xml.getBytes(StandardCharsets.UTF_8));}
    CobraEpgData gzip=cobraParseGuide(new java.util.zip.GZIPInputStream(new ByteArrayInputStream(compressed.toByteArray())));check(gzip.programs.get("nick.us").size()==2,"gzip payload parser");
    boolean rejected=false;try{cobraParseGuide(new ByteArrayInputStream("<html>error</html>".getBytes(StandardCharsets.UTF_8)));}catch(Exception e){rejected=true;}check(rejected,"HTML error not accepted as empty valid XMLTV");
    mCobraAsyncDestroyed=true;boolean cancelled=false;try{cobraParseGuide(new ByteArrayInputStream(xml.getBytes(StandardCharsets.UTF_8)));}catch(java.io.InterruptedIOException e){cancelled=true;}check(cancelled,"destroy cancels parsing");mCobraAsyncDestroyed=false;
    // >300k optional entries followed by the essential channel verifies fairness at the cap.
    StringBuilder large=new StringBuilder("<tv>");String start=time(now-7200000),stop=time(now-3600000);
    for(int i=0;i<300010;i++)large.append("<programme channel=\"g").append(i/1000).append("\" start=\"").append(start).append("\" stop=\"").append(stop).append("\"><title>History</title></programme>");
    large.append(program("late",now-1000,now+1000000,"Still current")).append(program("late",now+1000000,now+2000000,"Still next")).append("</tv>");
    CobraEpgData capped=cobraParseGuide(new ByteArrayInputStream(large.toString().getBytes(StandardCharsets.UTF_8)));check(capped.truncated,"partial schedule declared");check(capped.programs.get("late").size()==2,"late channels retain Now and Next after cap");
  }
  public static void main(String[] args)throws Exception{testStore();testLayout();testTime();new CobraRefinementHarness().testXml();System.out.println("PASS: "+checks+" production-algorithm assertions; device playback remains a separate gate");}
'''


def main():
    p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    before=a.before.read_text();after=a.after.read_text();assert hashlib.sha256(before.encode()).hexdigest()==BASELINE_SHA256
    verify(after);out=a.out;out.mkdir(parents=True,exist_ok=True)
    protected=('onCreate','onPause','onStop','onUserLeaveHint','onMultiWindowModeChanged','closeCobraAsyncWork','isCobraAsyncAlive','submitCobraIo','publishCobraUi','loadXtream','parseM3u','mediaItem','httpGet','xtreamUrl','xtreamEpgUrl','saveVodProgress','playCatchup','toggleRecording','showCobraScheduleRecording','showCobraAddToGroup','shareCobraChannel','toggleFavorite')
    for name in protected:
        assert extract_method(before,name)==extract_method(after,name),name+' changed outside approved scope'
    for name in ('cobraLayoutMultiTiles','cobraLayoutGuide','cobraLayoutPlayerPanels'):
        body=extract_method(after,name)
        assert 'new TextureView' not in body and 'removeView' not in body,name+' may detach surfaces'
    back=extract_method(after,'onBackPressed');assert back.index('mCobraPlayerLocked')<back.index('closeCobraActionSheet')<back.index('moveTaskToBack')
    destroy=extract_method(after,'onDestroy');assert destroy.index('closeCobraAsyncWork')<destroy.index('stopCobraPreview')
    assert 'rememberAndPauseCobraPlayer(mCobraPreviewPlayer)' in extract_method(after,'pauseCobraForBackground')
    assert 'new AlertDialog' not in extract_method(after,'showCobraMultiTileActions')
    assert 'binding.current()' in extract_method(after,'cobraAttachVideo')
    # Repeat application must fail closed, not append duplicates.
    from infinity_cobra_2103153_refinement import patch
    try: patch(after)
    except RuntimeError as e: assert 'preimage mismatch' in str(e)
    else: raise AssertionError('second application accepted')
    declarations='\n'.join(extract_class(after,n) for n in ('CobraGuideMath','CobraLayoutMath','CobraTileStore','CobraEpgData','GuideProgram'))
    methods='\n'.join(extract_method(after,n) for n in ('parseXmlTvTime','cobraBoundedId','cobraParseGuide'))
    java='''import java.io.*;import java.util.*;import java.text.*;import java.util.regex.*;import java.nio.charset.StandardCharsets;import org.xmlpull.v1.*;import android.util.Xml;
public class CobraRefinementHarness {private boolean mCobraAsyncDestroyed=false;\n'''+declarations+'\n'+methods+'\n'+HARNESS+'\n}\n'
    files={'CobraRefinementHarness.java':java,'org/xmlpull/v1/XmlPullParser.java':XML_INTERFACE,'org/xmlpull/v1/XmlPullParserException.java':'package org.xmlpull.v1; public class XmlPullParserException extends Exception { public XmlPullParserException(String text){super(text);} }','android/util/Xml.java':XML_ADAPTER}
    for name,content in files.items():target=out/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content)
    subprocess.run(['javac','-encoding','UTF-8','-d',str(out)]+[str(out/n) for n in files],check=True)
    result=subprocess.run(['java','-Xmx768m','-cp',str(out),'CobraRefinementHarness'],check=True,capture_output=True,text=True)
    print(result.stdout,end='');(out/'results.txt').write_text(result.stdout)
    receipt={'protected_methods_byte_identical':list(protected),'production_helpers_executed':['CobraTileStore','CobraLayoutMath','CobraGuideMath','cobraParseGuide'],'host_xml_adapter':'JDK StAX; not Android device acceptance','actual_decoder_provider_test':False,'stdout':result.stdout}
    (out/'results.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('PASS: final source guards and '+str(len(protected))+' unrelated protected methods byte-identical')
if __name__=='__main__':main()
