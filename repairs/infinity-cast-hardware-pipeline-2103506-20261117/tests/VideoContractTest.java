package com.projectinfinity.kodi;
import java.util.*;import java.io.*;
public final class VideoContractTest {
 static int tests;static void check(boolean ok){tests++;if(!ok)throw new AssertionError("contract"+tests);}
 interface Bad {void run()throws Exception;}
 static void refuses(Bad run)throws Exception{tests++;try{run.run();throw new AssertionError("accepted malformed input");}catch(IOException expected){}}
 static byte[] annex(byte... bytes){byte[] out=new byte[bytes.length+4];out[3]=1;System.arraycopy(bytes,0,out,4,bytes.length);return out;}
 static byte[] sample(int size)throws Exception{ByteArrayOutputStream b=new ByteArrayOutputStream();DataOutputStream d=new DataOutputStream(b);d.writeInt(size);byte[] nal=new byte[size];Arrays.fill(nal,(byte)99);nal[0]=0x65;d.write(nal);return b.toByteArray();}
 public static void main(String[] args)throws Exception{
  byte[] sps=annex((byte)0x67,(byte)66,(byte)0xc0,(byte)31,(byte)0x80),pps=annex((byte)0x68,(byte)0x80);byte[] config=InfinityCastVideoContract.configuration(sps,pps);check(config[0]==1&&config[1]==66&&(config[4]&3)==3);
  for(int n=256;n<512;n++){byte[] data=sample(n);check(InfinityCastVideoContract.idr(data));check(InfinityCastVideoContract.avcc(data).get(0).length==n);}
  byte[] idr=InfinityCastVideoContract.sample(annex((byte)0x65,(byte)0x88),config);check(InfinityCastVideoContract.idr(idr));refuses(()->InfinityCastVideoContract.avcc(new byte[]{0,0,1}));refuses(()->InfinityCastVideoContract.annexB(new byte[]{0,0,0,2,0x65}));refuses(()->InfinityCastVideoContract.sample(sps,config));
  for(double fps:new double[]{24,60})for(long begin:new long[]{0,2005000,2020000,2041667,3999999}){long end=begin+2005000,last=InfinityCastVideoContract.firstSlot(begin)-1;boolean first=true;for(long t=begin;t<end;t+=Math.round(1000000/fps)){if(InfinityCastVideoContract.select(t,begin,end,fps,last)){if(first)check(t==begin);last=InfinityCastVideoContract.slot(t);first=false;}}check(!first);}
  long cut=2005000;Set<Long> prior=new HashSet<>(),next=new HashSet<>();for(long t=0;t<4000000;t+=5000){long slot=InfinityCastVideoContract.slot(t);if(t<cut&&InfinityCastVideoContract.select(t,0,cut,60,slot-1))prior.add(slot);if(t>=cut&&InfinityCastVideoContract.select(t,cut,4000000,60,slot-1))next.add(slot);}prior.retainAll(next);check(prior.isEmpty());
  List<InfinityCastVideoContract.Packet> packets=Arrays.asList(new InfinityCastVideoContract.Packet(idr,0,true),new InfinityCastVideoContract.Packet(idr,40000,true));byte[] batch=InfinityCastVideoContract.batch(config,packets,0,80000);check(batch.length>50);refuses(()->InfinityCastVideoContract.batch(config,Arrays.asList(new InfinityCastVideoContract.Packet(idr,0,false)),0,80000));refuses(()->InfinityCastVideoContract.batch(config,Arrays.asList(new InfinityCastVideoContract.Packet(idr,40000,true),new InfinityCastVideoContract.Packet(idr,0,true)),0,80000));
  System.out.println("PASS_VIDEO_CONTRACT "+tests+"; canonicalAVCC,startcodes,IDR,nonalignedcueownership,batchPTSnegativechecks");
 }
}
