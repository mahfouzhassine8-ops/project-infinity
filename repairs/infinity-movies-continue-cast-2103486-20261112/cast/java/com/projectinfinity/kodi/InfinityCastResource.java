package com.projectinfinity.kodi;

import java.io.*;
import java.security.*;
import java.util.*;

/** Cast-only RAM storage. Reservations include unpublished and client-pinned pages. */
final class InfinityCastResource {
 static final int PAGE=65536, LIMIT=64*1024*1024, SEQUENCES=32;
 static final class Store {
  final LinkedHashMap<Integer,InfinityCastResource> entries=new LinkedHashMap<>(8,.75f,true);
  long reserved,peak;boolean closed;
  synchronized InfinityCastResource create(int index)throws IOException {
   if(closed)throw new IOException("mkv_cancelled");InfinityCastResource old=entries.get(index);
   if(old!=null)throw new IOException("mkv_resource_duplicate_producer");InfinityCastResource r=new InfinityCastResource(this,index);entries.put(index,r);return r;
  }
  synchronized InfinityCastResource get(int index){return entries.get(index);}
  synchronized void page(InfinityCastResource writer)throws IOException {
   if(closed||writer.retired)throw new IOException("mkv_cancelled");
   while(reserved+PAGE>LIMIT){InfinityCastResource victim=null;for(InfinityCastResource r:entries.values())if(r!=writer&&r.complete&&r.pins==0){victim=r;break;}if(victim==null)throw new IOException("mkv_resource_working_set_limit");retire(victim);}
   reserved+=PAGE;peak=Math.max(peak,reserved);
  }
  synchronized void retire(InfinityCastResource r){if(r.retired)return;if(r.pins!=0){r.retireWhenUnpinned=true;return;}r.retired=true;reserved-=(long)r.pages.size()*PAGE;r.pages.clear();entries.remove(r.index);}
  synchronized Lease pin(InfinityCastResource r)throws IOException{if(closed||r.retired||!r.complete||r.retireWhenUnpinned)throw new IOException("mkv_resource_not_ready");r.pins++;return new Lease(r);}
  synchronized void unpin(InfinityCastResource r){if(r.pins<=0)throw new IllegalStateException("mkv_resource_pin_underflow");r.pins--;if(r.retireWhenUnpinned||closed)retire(r);}
  synchronized void close(){closed=true;for(InfinityCastResource r:new ArrayList<>(entries.values()))retire(r);}
 }
 static final class Lease implements AutoCloseable {
  private InfinityCastResource resource;
  Lease(InfinityCastResource r){resource=r;}
  long length(){return resource.length;}
  String digest(){return resource.digest;}
  void copyTo(OutputStream out,long offset,long count)throws IOException {
   InfinityCastResource r=resource;if(r==null||offset<0||count<0||offset>r.length||count>r.length-offset)throw new IOException("mkv_resource_range");
   while(count>0){int page=(int)(offset/PAGE),at=(int)(offset%PAGE),n=(int)Math.min(count,PAGE-at);out.write(r.pages.get(page),at,n);offset+=n;count-=n;}
  }
  byte[] smallArray()throws IOException{long n=length();if(n>8*1024*1024)throw new IOException("mkv_legacy_array_limit");ByteArrayOutputStream out=new ByteArrayOutputStream((int)n);copyTo(out,0,n);return out.toByteArray();}
  @Override public void close(){InfinityCastResource r=resource;if(r!=null){resource=null;r.store.unpin(r);}}
 }
 final Store store;final int index;final List<byte[]> pages=new ArrayList<>();final MessageDigest hash;
 long length;String digest;boolean complete,retired,retireWhenUnpinned;int pins;
 InfinityCastResource(Store owner,int index)throws IOException{store=owner;this.index=index;try{hash=MessageDigest.getInstance("SHA-256");}catch(NoSuchAlgorithmException e){throw new IOException("mkv_resource_hash_unavailable");}}
 /** JNI producer callback; publication is impossible until complete validation. */
 void append(byte[] data,int count)throws IOException {synchronized(store){
  if(data==null||count<0||count>data.length||count>PAGE||complete||retired||length>LIMIT-count)throw new IOException("mkv_resource_output_limit");
  int from=0;while(from<count){int at=(int)(length%PAGE);if(at==0){store.page(this);try{pages.add(new byte[PAGE]);}catch(OutOfMemoryError failure){synchronized(store){store.reserved-=PAGE;}throw new IOException("mkv_resource_memory_limit");}}
   int n=Math.min(count-from,PAGE-at);System.arraycopy(data,from,pages.get(pages.size()-1),at,n);hash.update(data,from,n);length+=n;from+=n;
  }
 }}
 private int octet(long p)throws IOException{if(p<0||p>=length)throw new IOException("mkv_resource_box_bounds");return pages.get((int)(p/PAGE))[(int)(p%PAGE)]&255;}
 private long word(long p)throws IOException{long n=0;for(int i=0;i<4;i++)n=(n<<8)|octet(p+i);return n;}
 private long box(long at,long end)throws IOException{if(end-at<8)throw new IOException("mkv_resource_box_bounds");long n=word(at);int minimum=n==1?16:8;if(n==1){if(end-at<16||word(at+8)!=0)throw new IOException("mkv_resource_box_bounds");n=word(at+12);}if(n<minimum||n>end-at)throw new IOException("mkv_resource_box_bounds");return n;}
 void seal(boolean media)throws IOException {synchronized(store){
  if(length<=0||complete||retired)throw new IOException("mkv_resource_empty");
  if(media){if(index<0||index>=8192)throw new IOException("mkv_resource_index");long at=0,sequence=(long)index*SEQUENCES+1;int moofs=0,mdats=0;
   while(at<length){long size=box(at,length),type=word(at+4);if(type==0x6d6f6f66L){if(moofs!=mdats)throw new IOException("mkv_resource_incomplete_media");if(++moofs>SEQUENCES)throw new IOException("mkv_resource_moof_limit");long p=at+(word(at)==1?16:8);int found=0;while(p<at+size){long child=box(p,at+size);if(word(p+4)==0x6d666864L){if(child!=16||word(p+12)!=sequence++)throw new IOException("mkv_resource_sequence");found++;}p+=child;}if(found!=1)throw new IOException("mkv_resource_sequence");}else if(type==0x6d646174L){if(moofs!=mdats+1)throw new IOException("mkv_resource_incomplete_media");mdats++;}else throw new IOException("mkv_resource_box_type");at+=size;
   }if(moofs==0||moofs!=mdats)throw new IOException("mkv_resource_incomplete_media");
  }
  StringBuilder text=new StringBuilder();for(byte b:hash.digest())text.append(String.format(Locale.ROOT,"%02x",b&255));digest=text.toString();synchronized(store){if(store.closed)throw new IOException("mkv_cancelled");complete=true;}
 }
 }
 void abort(){store.retire(this);}
}
