package com.projectinfinity.kodi;
import java.io.*;import java.util.*;
public class ResourceProbe {
 static int checks;static void need(boolean condition,String what){checks++;if(!condition)throw new AssertionError(what);}
 interface Work {void run()throws Exception;}
 static void rejects(Work work,String reason)throws Exception{try{work.run();throw new AssertionError("accepted "+reason);}catch(IOException expected){need(expected.getMessage().equals(reason),reason+":"+expected.getMessage());}}
 static byte[] fragment(int sequence)throws Exception{ByteArrayOutputStream b=new ByteArrayOutputStream();DataOutputStream d=new DataOutputStream(b);d.writeInt(24);d.writeBytes("moof");d.writeInt(16);d.writeBytes("mfhd");d.writeInt(0);d.writeInt(sequence);d.writeInt(12);d.writeBytes("mdat");d.writeInt(sequence);return b.toByteArray();}
 public static void main(String[]args)throws Exception{
  InfinityCastResource.Store store=new InfinityCastResource.Store();InfinityCastResource r=store.create(18);byte[] bytes=fragment(577);r.append(bytes,bytes.length);rejects(()->store.pin(r),"mkv_resource_not_ready");r.seal(true);
  try(InfinityCastResource.Lease lease=store.pin(r)){ByteArrayOutputStream out=new ByteArrayOutputStream();lease.copyTo(out,7,19);need(Arrays.equals(out.toByteArray(),Arrays.copyOfRange(bytes,7,26)),"exact range");store.retire(r);rejects(()->store.pin(r),"mkv_resource_not_ready");need(store.reserved==65536,"pinned resource retained");}
  need(store.reserved==0,"last pin releases retirement");
  InfinityCastResource wrong=store.create(2);wrong.append(bytes,bytes.length);rejects(()->wrong.seal(true),"mkv_resource_sequence");wrong.abort();
  InfinityCastResource multi=store.create(0);for(int n=1;n<=32;n++){byte[] f=fragment(n);multi.append(f,f.length);}multi.seal(true);need(multi.complete,"32 disjoint moofs accepted");multi.abort();
  InfinityCastResource incomplete=store.create(0);incomplete.append(bytes,24);rejects(()->incomplete.seal(true),"mkv_resource_sequence");incomplete.abort();
  byte[] page=new byte[65536];InfinityCastResource a=store.create(0);for(int n=0;n<512;n++)a.append(page,page.length);a.seal(false);InfinityCastResource.Lease pinA=store.pin(a);InfinityCastResource b=store.create(1);for(int n=0;n<512;n++)b.append(page,page.length);b.seal(false);InfinityCastResource.Lease pinB=store.pin(b);
  InfinityCastResource blocked=store.create(2);rejects(()->blocked.append(page,page.length),"mkv_resource_working_set_limit");need(store.peak==64L*1024*1024,"total quota includes pinned");blocked.abort();store.close();need(store.reserved==64L*1024*1024,"close defers pinned free");pinA.close();pinB.close();need(store.reserved==0,"close eventually releases pages");
  for(int n=0;n<100;n++){InfinityCastResource.Store race=new InfinityCastResource.Store();InfinityCastResource x=race.create(0);byte[] f=fragment(1);x.append(f,f.length);Thread close=new Thread(race::close);close.start();try{x.seal(true);}catch(IOException expected){need(expected.getMessage().equals("mkv_cancelled")||expected.getMessage().equals("mkv_resource_empty"),"safe seal cancel");}close.join();need(race.reserved==0,"race frees");}
  System.out.println("PASS_RESOURCE "+checks);
 }
}
