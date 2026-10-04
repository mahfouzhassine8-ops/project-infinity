package com.projectinfinity.kodi;

import android.content.Context;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class) @Config(sdk=35)
public class ConditionalPowerRouteTest {
  private String fixture(String profile)throws Exception {
    try(InputStream in=getClass().getResourceAsStream("/power-profiles/"+profile+"/DialogButtonMenu.xml")){
      assertNotNull(profile,in);return new String(in.readAllBytes(),StandardCharsets.UTF_8);
    }
  }
  private String paired(boolean reverse) {
    String normal="<onclick condition=\"!System.Platform.Android\">Quit()</onclick>";
    String android="<onclick condition=\"System.Platform.Android\">"+InfinityPowerMenuRoutes.command(false)+"</onclick>";
    String force="<onclick condition=\"!System.Platform.Android\">ActivateWindow(10001,\"plugin://plugin.program.chef21/?mode=18&amp;name=Force%20Close\",return)</onclick>";
    String androidForce="<onclick condition=\"System.Platform.Android\">"+InfinityPowerMenuRoutes.command(true)+"</onclick>";
    return "<window><control type=\"button\" id=\"200\"><label>CLOSE KODI</label>"+
      (reverse?android+normal:normal+android)+"</control><control type=\"button\" id=\"300\"><label>FORCE CLOSE KODI</label>"+
      (reverse?androidForce+force:force+androidForce)+"</control></window>";
  }
  private void rejects(String xml)throws Exception {
    try{InfinityPowerMenuRoutes.patch(xml);fail("Unknown or ambiguous actions must be preserved");}
    catch(IOException expected){}
  }
  private void write(File file,String value)throws Exception {
    file.getParentFile().mkdirs();Files.write(file.toPath(),value.getBytes(StandardCharsets.UTF_8));
  }
  private String read(File file)throws Exception {
    return new String(Files.readAllBytes(file.toPath()),StandardCharsets.UTF_8);
  }
  @Test public void approvedConditionalRoutesKeepEveryByte()throws Exception {
    for(boolean reverse:new boolean[]{false,true}){
      String source=paired(reverse);assertEquals(source,InfinityPowerMenuRoutes.patch(source));
    }
    String source=fixture("conditional195");
    assertEquals(source,InfinityPowerMenuRoutes.patch(source));
  }
  @Test public void unknownAndroidRouteIsNotOverwritten()throws Exception {
    rejects(paired(false).replace(InfinityPowerMenuRoutes.command(false),"CustomClose()"));
  }
  @Test public void unknownFallbackIsNotOverwritten()throws Exception {
    rejects(paired(false).replace("Quit()","UnknownQuit()"));
  }
  @Test public void duplicateOrUnknownConditionsAreRejected()throws Exception {
    rejects(paired(false).replace("!System.Platform.Android","System.Platform.Android"));
    rejects(paired(false).replace("System.Platform.Android\"","System.Platform.Android + true\""));
  }
  @Test public void extraAttributesAreRejected()throws Exception {
    rejects(paired(false).replace("<onclick condition=","<onclick extra=\"true\" condition="));
  }
  @Test public void singleConditionalLegacyCommandIsRejected()throws Exception {
    rejects(fixture("unified").replace("<onclick>Quit()</onclick>",
      "<onclick condition=\"System.Platform.Android\">Quit()</onclick>"));
  }
  @Test public void rejectedProfileDoesNotAbortLaterProfile()throws Exception {
    Context app=RuntimeEnvironment.getApplication();
    File data=new File(app.getFilesDir(),"conditional-power-data");
    File skin=new File(data,".kodi/addons/skin.infinity.diggz");
    File unified=new File(skin,"unified/DialogButtonMenu.xml");
    File invalid=new File(skin,"16x9/DialogButtonMenu.xml");
    File later=new File(skin,"20x9/DialogButtonMenu.xml");
    String approved=fixture("conditional195"),bad=paired(false).replace(InfinityPowerMenuRoutes.command(false),"Unknown()");
    String legacy=fixture("20x9");
    write(unified,approved);write(invalid,bad);write(later,legacy);
    String previous=System.getProperty("xbmc.data");
    try{
      System.setProperty("xbmc.data",data.getAbsolutePath());
      InfinityPowerMenuRoutes.apply(app);
      assertEquals(approved,read(unified));
      assertEquals(bad,read(invalid));
      assertEquals(InfinityPowerMenuRoutes.patch(legacy),read(later));
      assertTrue(InfinityPowerMenuRoutes.report(app).contains("Validated profiles: 2; commands updated: 1; rejected profiles: 1"));
      File[] backups=new File(app.getFilesDir(),"infinity-power-route-originals-2103299").listFiles();
      assertNotNull(backups);
      boolean original=false;
      for(File backup:backups)if(read(backup).equals(legacy))original=true;
      assertTrue(original);
      InfinityPowerMenuRoutes.apply(app);
      assertTrue(InfinityPowerMenuRoutes.report(app).contains("commands updated: 0"));
    }finally{
      if(previous==null)System.clearProperty("xbmc.data");else System.setProperty("xbmc.data",previous);
    }
  }
}
