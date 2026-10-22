/* SPDX-License-Identifier: GPL-2.0-or-later */
package com.projectinfinity.kodi;

import android.os.Looper;
import android.system.ErrnoException;
import android.system.Os;
import android.system.OsConstants;
import android.system.StructStat;
import java.io.File;
import java.io.FileDescriptor;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicBoolean;
import org.json.JSONObject;

/** Infinity coordinator receipt only. No provider, shared lifecycle or reader changes.
 * AtomicFile readers may delete its reserved .new path during a live write.
 * A private exclusive stage is renamed only after checked write/sync/close;
 * directory durability and exact inode/content readback precede success.
 */
final class InfinityCheckpointReceipt {
  private static final AtomicBoolean writing=new AtomicBoolean();
  private InfinityCheckpointReceipt(){}
  private static IOException io(String operation,ErrnoException cause){
    return new IOException("checkpoint receipt "+operation+" failed; errno="+cause.errno,cause);
  }
  private static final class Descriptor implements AutoCloseable {
    FileDescriptor value;
    Descriptor(String path,int flags,int mode)throws IOException{
      try{value=Os.open(path,flags,mode);}catch(ErrnoException error){throw io("open",error);}
    }
    public void close()throws IOException{
      FileDescriptor current=value;value=null;
      if(current!=null)try{Os.close(current);}catch(ErrnoException error){throw io("close",error);}
    }
  }
  private static StructStat stat(File file)throws IOException{
    try{return Os.lstat(file.getPath());}
    catch(ErrnoException error){if(error.errno==OsConstants.ENOENT)return null;throw io("lstat",error);}
  }
  private static boolean same(StructStat a,StructStat b){
    return a!=null&&b!=null&&a.st_dev==b.st_dev&&a.st_ino==b.st_ino&&a.st_mode==b.st_mode&&
      a.st_uid==b.st_uid&&a.st_gid==b.st_gid&&a.st_nlink==b.st_nlink;
  }
  private static void require(boolean value,String detail)throws IOException{
    if(!value)throw new IOException("checkpoint receipt "+detail);
  }
  private static void regular(StructStat value)throws IOException{
    require(value!=null&&OsConstants.S_ISREG(value.st_mode)&&value.st_nlink==1&&value.st_uid==Os.getuid(),"file identity unverified");
  }
  private static void noLegacyBackup(File target)throws IOException{
    require(stat(new File(target.getPath()+".bak"))==null,"legacy recovery pending");
  }
  static void atomic(File supplied,JSONObject row)throws IOException{
    require(Looper.getMainLooper()==null||Looper.myLooper()!=Looper.getMainLooper(),"write on GUI thread");
    require("infinity-checkpoint-close.json".equals(supplied.getName()),"unexpected target");
    byte[] bytes=row.toString().getBytes(StandardCharsets.UTF_8);
    require(bytes.length<=262144,"oversized checkpoint receipt");
    require(writing.compareAndSet(false,true),"concurrent coordinator writer");
    try{
      File parent=supplied.getAbsoluteFile().getParentFile().getCanonicalFile();
      File target=new File(parent,supplied.getName());
      StructStat parentBefore=stat(parent);
      require(parentBefore!=null&&OsConstants.S_ISDIR(parentBefore.st_mode),"parent is not a directory");
      StructStat existing=stat(target);if(existing!=null)regular(existing);
      noLegacyBackup(target);
      File stage=new File(parent,".infinity-checkpoint-receipt-"+UUID.randomUUID()+".pending");
      StructStat identity=null;boolean renamed=false;
      try(Descriptor directory=new Descriptor(parent.getPath(),OsConstants.O_RDONLY|OsConstants.O_NONBLOCK|OsConstants.O_NOFOLLOW|OsConstants.O_CLOEXEC,0)){
        StructStat directoryIdentity;
        try{directoryIdentity=Os.fstat(directory.value);}catch(ErrnoException error){throw io("directory identity",error);}
        require(OsConstants.S_ISDIR(directoryIdentity.st_mode)&&directoryIdentity.st_uid==Os.getuid()&&same(directoryIdentity,stat(parent)),"parent identity unverified");
        try{
          try(Descriptor output=new Descriptor(stage.getPath(),OsConstants.O_WRONLY|OsConstants.O_CREAT|OsConstants.O_EXCL|OsConstants.O_NOFOLLOW|OsConstants.O_CLOEXEC,0600)){
            try{
              identity=Os.fstat(output.value);regular(identity);
              require(same(identity,stat(stage)),"stage identity changed");
              int offset=0;while(offset<bytes.length){int count=Os.write(output.value,bytes,offset,bytes.length-offset);require(count>0,"write made no progress");offset+=count;}
              Os.fsync(output.value);
            }catch(ErrnoException error){throw io("stage write/sync",error);}
          }
          require(same(directoryIdentity,stat(parent))&&same(identity,stat(stage)),"namespace changed before replacement");
          StructStat current=stat(target);
          require(existing==null?current==null:same(existing,current),"target changed before replacement");
          noLegacyBackup(target);
          try{Os.rename(stage.getPath(),target.getPath());renamed=true;Os.fsync(directory.value);}
          catch(ErrnoException error){throw io("replacement/directory sync",error);}
          require(same(directoryIdentity,stat(parent))&&same(identity,stat(target)),"replacement identity unconfirmed");
          try(Descriptor input=new Descriptor(target.getPath(),OsConstants.O_RDONLY|OsConstants.O_NOFOLLOW|OsConstants.O_CLOEXEC,0)){
            try{
              require(same(identity,Os.fstat(input.value)),"readback identity changed");
              byte[] actual=new byte[bytes.length+1];int offset=0;
              while(offset<actual.length){int count=Os.read(input.value,actual,offset,actual.length-offset);if(count==0)break;offset+=count;}
              require(offset==bytes.length&&Arrays.equals(bytes,Arrays.copyOf(actual,offset)),"replacement content unconfirmed");
            }catch(ErrnoException error){throw io("readback",error);}
          }
          noLegacyBackup(target);
        }catch(IOException failure){
          // A post-rename failure may have changed the receipt; retain failure.
          // Remove only our proven unchanged stage, never a replacement inode.
          if(!renamed&&identity!=null)try{
            if(same(directoryIdentity,stat(parent))&&same(identity,stat(stage)))Os.remove(stage.getPath());
          }catch(IOException|ErrnoException cleanup){failure.addSuppressed(cleanup);}
          throw failure;
        }
      }
      InfinityCheckpointEvidence.mirror(target,row);
    }finally{writing.set(false);}
  }
}
