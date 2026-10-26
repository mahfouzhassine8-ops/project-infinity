// POSIX host transport for testing the real adapter algorithm, not Android ABI.
package android.system;
import java.io.*;
import java.nio.channels.FileChannel;
import java.nio.file.*;
import java.nio.file.attribute.FileTime;
import java.util.*;
public final class Os {
  private static final Map<FileDescriptor,Path> paths=new IdentityHashMap<FileDescriptor,Path>();
  private static final Map<FileDescriptor,RandomAccessFile> files=new IdentityHashMap<FileDescriptor,RandomAccessFile>();
  private static int renames;
  private Os() {}
  public static FileDescriptor open(String name,int flags,int mode)throws IOException,ErrnoException {
    Path path=Paths.get(name);
    if(!Files.exists(path,LinkOption.NOFOLLOW_LINKS))throw new ErrnoException("open: missing module file");
    if(Files.isSymbolicLink(path))throw new IOException("Host fixture refuses linked input");
    int kind=((Integer)Files.getAttribute(path,"unix:mode",LinkOption.NOFOLLOW_LINKS)).intValue()&61440;
    if(kind!=32768 && kind!=16384)throw new IOException("Host fixture refuses nonregular input");
    FileDescriptor fd;
    if(kind==16384)fd=new FileDescriptor();
    else {RandomAccessFile file=new RandomAccessFile(name,"r");fd=file.getFD();files.put(fd,file);}
    paths.put(fd,path);return fd;
  }
  public static StructStat fstat(FileDescriptor fd)throws IOException {
    Path path=paths.get(fd);if(path==null)throw new IOException("Unknown host descriptor");
    StructStat s=new StructStat();
    s.st_mode=((Integer)Files.getAttribute(path,"unix:mode",LinkOption.NOFOLLOW_LINKS)).intValue();
    s.st_dev=((Long)Files.getAttribute(path,"unix:dev",LinkOption.NOFOLLOW_LINKS)).longValue();
    s.st_ino=((Long)Files.getAttribute(path,"unix:ino",LinkOption.NOFOLLOW_LINKS)).longValue();
    s.st_size=Files.size(path);
    s.st_mtime=((FileTime)Files.getAttribute(path,"unix:lastModifiedTime",LinkOption.NOFOLLOW_LINKS)).toMillis()/1000;
    s.st_ctime=((FileTime)Files.getAttribute(path,"unix:ctime",LinkOption.NOFOLLOW_LINKS)).toMillis()/1000;
    return s;
  }
  public static void rename(String from,String to)throws IOException {
    String fail=System.getenv("INFINITY_HOST_FAIL_RENAME");
    if(fail!=null && ++renames==Integer.parseInt(fail))throw new IOException("Injected host atomic-write failure");
    Files.move(Paths.get(from),Paths.get(to),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);
  }
  public static void fsync(FileDescriptor fd)throws IOException {
    Path p=paths.get(fd);if(p==null)throw new IOException("Unknown host sync descriptor");
    try(FileChannel channel=FileChannel.open(p,StandardOpenOption.READ)) {channel.force(true);}
  }
  public static void close(FileDescriptor fd)throws IOException {
    paths.remove(fd);RandomAccessFile file=files.remove(fd);if(file!=null)file.close();
  }
}
