package com.projectinfinity.kodi;
import java.io.*;
import java.nio.charset.StandardCharsets;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class) @Config(sdk=35)
public class PowerMenuRouteTest {
  private String fixture(String profile)throws Exception{
    try(InputStream in=getClass().getResourceAsStream("/power-profiles/"+profile+"/DialogButtonMenu.xml")){
      assertNotNull(profile,in);return new String(in.readAllBytes(),StandardCharsets.UTF_8);
    }
  }
  private String masked(String xml){
    for(String id:new String[]{"200","300"}){
      java.util.regex.Matcher m=java.util.regex.Pattern.compile("<control[^>]*id=\""+id+"\"[^>]*>.*?</control>",java.util.regex.Pattern.DOTALL).matcher(xml);
      assertTrue(m.find());String body=m.group();String mask=body.replaceAll("(?s)<onclick>.*?</onclick>","<onclick>POWER_COMMAND</onclick>");
      xml=xml.substring(0,m.start())+mask+xml.substring(m.end());
    }return xml;
  }
  @Test public void allThirteenProfilesChangeOnlyTwoOnclickBodies()throws Exception{
    assertEquals(13,InfinityPowerMenuRoutes.PROFILES.length);
    for(String profile:InfinityPowerMenuRoutes.PROFILES){
      String before=fixture(profile),after=InfinityPowerMenuRoutes.patch(before);
      assertNotEquals(profile,before,after);assertEquals(profile,masked(before),masked(after));
      assertTrue(after.contains(InfinityPowerMenuRoutes.command(false)));assertTrue(after.contains(InfinityPowerMenuRoutes.command(true)));
      assertEquals(profile,after,InfinityPowerMenuRoutes.patch(after));
    }
  }
  @Test public void commandsHaveExplicitPrivateComponentAndNineArguments(){
    for(boolean force:new boolean[]{false,true}){
      String c=InfinityPowerMenuRoutes.command(force);String[] args=c.substring(c.indexOf('(')+1,c.length()-1).split(",",-1);
      assertEquals(9,args.length);assertEquals("com.projectinfinity.kodi",args[0]);
      assertEquals("com.projectinfinity.kodi.InfinityPowerControlActivity",args[8]);
      assertEquals(force?InfinityExitCompletion.FORCE:InfinityExitCompletion.NORMAL,args[1]);
      for(int i=2;i<8;i++)assertEquals("",args[i]);
    }
  }
  @Test public void unknownExistingCommandsAreNotOverwritten()throws Exception{
    String old=fixture("16x9").replace("<onclick>Quit()</onclick>","<onclick>CustomClose()</onclick>");
    try{InfinityPowerMenuRoutes.patch(old);fail("Unknown command must be preserved");}catch(IOException expected){}
  }
  @Test public void malformedAndDtdXmlAreRejected()throws Exception{
    for(String s:new String[]{"<window>","<!DOCTYPE window [<!ENTITY x SYSTEM 'file:///private'>]><window/>"}){
      try{InfinityPowerMenuRoutes.patch(s);fail("Invalid XML must be preserved");}catch(IOException expected){}
    }
  }
  @Test public void installerBacksUpOriginalAndHonorsConfiguredDataRoot()throws Exception{
    android.content.Context app=org.robolectric.RuntimeEnvironment.getApplication();
    File data=new File(app.getFilesDir(),"power-fixture-data");File skin=new File(data,".kodi/addons/skin.infinity.diggz");
    File file=new File(skin,"16x9/DialogButtonMenu.xml");assertTrue(file.getParentFile().mkdirs());
    String original=fixture("16x9");java.nio.file.Files.write(file.toPath(),original.getBytes(StandardCharsets.UTF_8));
    String previous=System.getProperty("xbmc.data");
    try{
      System.setProperty("xbmc.data",data.getAbsolutePath());InfinityPowerMenuRoutes.apply(app);
      String after=new String(java.nio.file.Files.readAllBytes(file.toPath()),StandardCharsets.UTF_8);assertEquals(masked(original),masked(after));
      assertTrue(after.contains(InfinityPowerMenuRoutes.command(true)));
      File[] backups=new File(app.getFilesDir(),"infinity-power-route-originals-2103299").listFiles();assertNotNull(backups);assertEquals(1,backups.length);
      assertEquals(original,new String(java.nio.file.Files.readAllBytes(backups[0].toPath()),StandardCharsets.UTF_8));
      InfinityPowerMenuRoutes.apply(app);assertEquals(after,new String(java.nio.file.Files.readAllBytes(file.toPath()),StandardCharsets.UTF_8));
    }finally{if(previous==null)System.clearProperty("xbmc.data");else System.setProperty("xbmc.data",previous);}
  }
}
