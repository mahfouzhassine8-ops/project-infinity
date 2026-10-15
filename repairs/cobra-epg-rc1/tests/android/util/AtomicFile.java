package android.util;
import java.io.*;import java.nio.file.*;
public class AtomicFile {
 final File base,tmp;public AtomicFile(File f){base=f;tmp=new File(f.getPath()+".new");}
 public FileInputStream openRead()throws IOException{return new FileInputStream(base);}
 public FileOutputStream startWrite()throws IOException{base.getParentFile().mkdirs();return new FileOutputStream(tmp);}
 public void finishWrite(FileOutputStream s)throws IOException{s.getFD().sync();s.close();Files.move(tmp.toPath(),base.toPath(),StandardCopyOption.REPLACE_EXISTING);}
 public void failWrite(FileOutputStream s){try{s.close();}catch(IOException ignored){}tmp.delete();}
 public void delete(){base.delete();tmp.delete();}
}