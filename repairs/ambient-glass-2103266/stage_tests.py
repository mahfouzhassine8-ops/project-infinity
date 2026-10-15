from pathlib import Path
import argparse,shutil
p=argparse.ArgumentParser();p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args();here=Path(__file__).resolve().parent
out=a.build_dir/'xbmc/src/test/java/com/projectinfinity/kodi';shutil.copytree('source265/staged-tests/java/com/projectinfinity/kodi',out,dirs_exist_ok=True);shutil.copy2(here/'AmbientGlassTest.java',out/'AmbientGlassTest.java')
fixture=Path('source265/screenshots/test-video-fixture.webp');assert fixture.exists()
with (a.build_dir/'xbmc/build.gradle').open('a') as f:f.write('''
android.testOptions.unitTests.includeAndroidResources = true
android.testOptions.unitTests.all {
 maxHeapSize = "3g"
 systemProperty "glass.evidence", "'''+str((a.evidence/'protected').resolve())+'''"
 systemProperty "pro.evidence", "'''+str((a.evidence/'pro').resolve())+'''"
 systemProperty "glass.phone.evidence", "'''+str((a.evidence/'phone').resolve())+'''"
 systemProperty "pro.fixture", "'''+str(fixture.resolve())+'''"
 testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" }
}
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1' }
''')
# Record exact time-ruler/list bounds for clock-aware comparison to the locked renders.
p=out/'PhoneGlassTest.java';s=p.read_text();needle='      save(root,mode+"-"+(light?"light":"oled")+"-"+size[0]+"x"+size[1]);'
assert s.count(needle)==1
s=s.replace(needle,'''      if(mode.equals("grid")){
        View ruler=(View)get(a,"mCobraGuideRuler");ViewGroup list=(ViewGroup)get(a,"mCobraGuideList");android.graphics.Rect rr=new android.graphics.Rect(0,0,ruler.getWidth(),ruler.getHeight()),lr=new android.graphics.Rect(0,0,list.getWidth(),list.getHeight());((ViewGroup)root).offsetDescendantRectToMyCoords(ruler,rr);((ViewGroup)root).offsetDescendantRectToMyCoords(list,lr);
        int label=((Number)get(list.getChildAt(0),"labelWidth")).intValue();JSONObject meta=new JSONObject();meta.put("ruler",new org.json.JSONArray(new int[]{rr.left,rr.top,ruler.getWidth(),ruler.getHeight()}));meta.put("list",new org.json.JSONArray(new int[]{lr.left,lr.top,list.getWidth(),list.getHeight()}));meta.put("labelWidth",label);
        File folder=new File(System.getProperty("glass.phone.evidence"));folder.mkdirs();try(FileWriter f=new FileWriter(new File(folder,"grid-"+(light?"light":"oled")+"-"+size[0]+"x"+size[1]+".png.clock.json"))){f.write(meta.toString());}
      }
'''+needle);p.write_text(s)
