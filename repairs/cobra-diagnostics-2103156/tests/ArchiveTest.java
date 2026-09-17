package com.projectinfinity.kodi;
import java.io.*;import java.nio.charset.StandardCharsets;import java.nio.file.*;import java.util.*;import java.util.zip.*;
public class ArchiveTest {
  static int count;static void check(boolean ok,String label){if(!ok)throw new AssertionError(label);count++;System.out.println("PASS: "+label);}
  static String clean(String s){return CobraDiagnosticArchive.redact(s,Arrays.asList("privateUser","s3cr3t! A"));}
  public static void main(String[] args)throws Exception {
    check(clean(null).isEmpty(),"null handling");check(clean("ERROR_DECODING_FAILED").equals("ERROR_DECODING_FAILED"),"error codes retained");
    for(String url:Arrays.asList("https://privateUser:s3cr3t@host/live/key","http://host/epg?token=abc","smb://user:secret/share","plugin://addon/play?url=https%3A%2F%2Fhost","https:\\/\\/host/path?user=me","www.host/path","https%3A%2F%2Fhost%2Fkey","HTTP%3a%2f%2fhost%3Faccess_token%3Dabc"))check(!clean(url).contains("host"),"URI scrub "+url.split(":")[0]);
    for(String value:Arrays.asList("password=PRIVATE","username: PRIVATE","token=PRIVATE","api_key=PRIVATE","access_token=PRIVATE","refresh_token=PRIVATE","secret=PRIVATE","passwd=PRIVATE","Authorization: Bearer PRIVATE","Cookie: one=PRIVATE; two=PRIVATE","{\"password\":\"PRIVATE VALUE\"}","'password': 'PRIVATE VALUE'"))check(!clean(value).contains("PRIVATE"),"credential form scrub "+value.split("[=:]")[0]);
    check(!clean("{\"password\":\"prefix\\\"PRIVATE\"}").contains("PRIVATE"),"JSON escaped quote credential fully scrubbed");
    check(!clean("password='prefix\\'PRIVATE'").contains("PRIVATE"),"single-quote escaped credential fully scrubbed");
    check(!clean("free text privateUser s3cr3t! A s3cr3t%21+A").contains("s3cr3t"),"known raw and encoded credential values");
    check(clean("Normal text\nsecond line").contains("\n"),"diagnostic line structure retained");
    check(!clean("A\u0001B").contains("\u0001"),"control bytes neutralized");
    Path dir=Files.createTempDirectory("cobra-archive-tests-");
    File file=dir.resolve("tail.log").toFile();Files.write(file.toPath(),"first line\nsecond line\nthird line\n".getBytes(StandardCharsets.UTF_8));
    check(CobraDiagnosticArchive.readTail(file,512).startsWith("first"),"small log complete");
    String tail=CobraDiagnosticArchive.readTail(file,18);check(tail.contains("truncated")&&tail.contains("third")&&!tail.contains("second"),"oversized log drops partial first line");
    Files.write(file.toPath(),"password=PRIVATE".getBytes(StandardCharsets.UTF_8));check(!CobraDiagnosticArchive.readTail(file,5).contains("IVATE"),"credential fragment on partial line excluded");
    Files.write(file.toPath(),new byte[]{1,0,2});check(CobraDiagnosticArchive.readTail(file,512).contains("binary"),"binary traces excluded");
    check(CobraDiagnosticArchive.readTail(dir.resolve("missing.log").toFile(),8).contains("missing"),"missing logs reported");
    boolean invalid=false;try{CobraDiagnosticArchive.readTail(file,0);}catch(IOException expected){invalid=true;}check(invalid,"invalid bound rejected");
    CobraDiagnosticArchive.atomicWrite(file,"old".getBytes(StandardCharsets.UTF_8));CobraDiagnosticArchive.atomicWrite(file,"new".getBytes(StandardCharsets.UTF_8));check(new String(Files.readAllBytes(file.toPath()),StandardCharsets.UTF_8).equals("new"),"atomic replace works");
    Path blocked=Files.createDirectory(dir.resolve("blocked"));Files.write(blocked.resolve("keep"),new byte[]{1});invalid=false;try{CobraDiagnosticArchive.atomicWrite(blocked.toFile(),new byte[]{2});}catch(IOException expected){invalid=true;}check(invalid&&Files.exists(blocked.resolve("keep")),"failed atomic replace retains old destination");
    Map<String,String> entries=new LinkedHashMap<>();entries.put("snapshot.txt","ERROR http://private.example?token=privateUser");entries.put("logs/kodi.log.txt","password=PRIVATE");
    File zip=dir.resolve("report.zip").toFile();CobraDiagnosticArchive.writeZip(zip,entries,Arrays.asList("privateUser"));
    try(ZipFile z=new ZipFile(zip)){check(z.size()==2,"ZIP complete entry count");for(Enumeration<? extends ZipEntry> i=z.entries();i.hasMoreElements();){ZipEntry e=i.nextElement();ByteArrayOutputStream b=new ByteArrayOutputStream();CobraDiagnosticArchive.copy(z.getInputStream(e),b);check(!b.toString("UTF-8").contains("PRIVATE")&&!b.toString("UTF-8").contains("private.example"),"archive member redacted "+e.getName());}}
    byte[] old=Files.readAllBytes(zip.toPath());entries.put("../bad","never");invalid=false;try{CobraDiagnosticArchive.writeZip(zip,entries,Collections.emptyList());}catch(IOException expected){invalid=true;}check(invalid&&Arrays.equals(old,Files.readAllBytes(zip.toPath())),"path traversal rejected without replacing good ZIP");
    for(String name:Arrays.asList("/absolute","a\\b","a/../b","dir/")){Map<String,String> bad=new HashMap<>();bad.put(name,"no");invalid=false;try{CobraDiagnosticArchive.writeZip(zip,bad,Collections.emptyList());}catch(IOException expected){invalid=true;}check(invalid,"unsafe member rejected "+name);}
    invalid=false;try{CobraDiagnosticArchive.writeZip(zip,Collections.emptyMap(),Collections.emptyList());}catch(IOException expected){invalid=true;}check(invalid,"empty bundle rejected");
    InputStream stalled=new InputStream(){public int read(){return 0;}public int read(byte[] b){return 0;}};invalid=false;try{CobraDiagnosticArchive.copy(stalled,new ByteArrayOutputStream());}catch(IOException expected){invalid=true;}check(invalid,"stalled stream fails instead of loop");
    invalid=false;try{CobraDiagnosticArchive.copy(new ByteArrayInputStream(new byte[100]),new OutputStream(){public void write(int b)throws IOException{throw new IOException("full");}});}catch(IOException expected){invalid=true;}check(invalid,"disk-full write failure propagated");
    ByteArrayOutputStream copied=new ByteArrayOutputStream();check(CobraDiagnosticArchive.copy(new ByteArrayInputStream(old),copied)==old.length&&Arrays.equals(old,copied.toByteArray()),"destination copy exact length and bytes");
    try(java.util.stream.Stream<Path> paths=Files.walk(dir)){paths.sorted(Comparator.reverseOrder()).forEach(p->{try{Files.delete(p);}catch(IOException e){throw new RuntimeException(e);}});}
    System.out.println("SUMMARY: "+count+" archive and redaction checks passed");
  }
}
