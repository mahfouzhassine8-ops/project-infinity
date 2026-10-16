package com.projectinfinity.kodi;

import android.system.ErrnoException;
import android.system.OsConstants;
import android.system.StructStat;
import java.io.FileDescriptor;
import java.io.FileInputStream;
import java.io.IOException;
import java.lang.reflect.Field;
import java.nio.channels.FileChannel;
import java.nio.file.*;
import java.util.*;
import org.robolectric.annotation.Implementation;
import org.robolectric.annotation.Implements;
import org.robolectric.shadows.ShadowLinux;

/** Test-only OS bridge. Robolectric 4.14.1 opens directories through
 * RandomAccessFile, which rejects them, and provides no fsync implementation.
 * This adapter uses actual host file descriptors, stat attributes and fsync
 * through FileChannel.force. It never substitutes a successful save result.
 * No part of this class is packaged into the Android application.
 */
@Implements(className="libcore.io.Linux",minSdk=26,isInAndroidSdk=false)
public final class HostFilesystemShadow extends ShadowLinux {
  private static final Map<FileDescriptor,Opened> opened=Collections.synchronizedMap(new IdentityHashMap<>());
  static volatile boolean failDirectorySync;
  static volatile int directorySyncs;
  private static final class Opened {
    final Path path;final FileChannel channel;
    Opened(Path path,FileChannel channel){this.path=path;this.channel=channel;}
  }
  private static ErrnoException error(String operation,Exception failure){
    return new ErrnoException(operation,failure instanceof NoSuchFileException?OsConstants.ENOENT:OsConstants.EIO,failure);
  }
  @Implementation @Override protected FileDescriptor open(String path,int flags,int mode)throws ErrnoException{
    if(flags!=OsConstants.O_RDONLY)return super.open(path,flags,mode);
    FileChannel channel=null;
    try{
      Path actual=Paths.get(path);channel=FileChannel.open(actual,StandardOpenOption.READ);
      Field field=channel.getClass().getDeclaredField("fd");field.setAccessible(true);
      FileDescriptor fd=(FileDescriptor)field.get(channel);opened.put(fd,new Opened(actual,channel));return fd;
    }catch(Exception failure){if(channel!=null)try{channel.close();}catch(IOException ignored){}throw error("open",failure);}
  }
  private StructStat metadata(String path,LinkOption... options)throws ErrnoException{
    try{
      Map<String,Object> a=Files.readAttributes(Paths.get(path),"unix:*",options);
      return new StructStat(((Number)a.get("dev")).longValue(),((Number)a.get("ino")).longValue(),
          ((Number)a.get("mode")).intValue(),((Number)a.get("nlink")).longValue(),
          ((Number)a.get("uid")).intValue(),((Number)a.get("gid")).intValue(),
          ((Number)a.get("rdev")).longValue(),((Number)a.get("size")).longValue(),0,0,0,4096,0);
    }catch(Exception failure){throw error("stat",failure);}
  }
  @Implementation @Override public StructStat stat(String path)throws ErrnoException{
    return path==null?super.stat(null):metadata(path);
  }
  @Implementation @Override protected StructStat lstat(String path)throws ErrnoException{
    return metadata(path,LinkOption.NOFOLLOW_LINKS);
  }
  @Implementation @Override protected StructStat fstat(FileDescriptor fd)throws ErrnoException{
    Opened item=opened.get(fd);return item==null?super.fstat(fd):metadata(item.path.toString());
  }
  @Implementation protected void fsync(FileDescriptor fd)throws ErrnoException{
    try{
      Opened item=opened.get(fd);
      if(item==null){fd.sync();return;}
      boolean directory=Files.isDirectory(item.path);
      if(directory&&failDirectorySync)throw new IOException("Injected directory sync failure");
      item.channel.force(true);if(directory)directorySyncs++;
    }catch(Exception failure){throw error("fsync",failure);}
  }
  @Implementation protected void close(FileDescriptor fd)throws ErrnoException{
    try{Opened item=opened.remove(fd);if(item==null)new FileInputStream(fd).close();else item.channel.close();}
    catch(Exception failure){throw error("close",failure);}
  }
}
