package com.projectinfinity.kodi;
import java.io.*;import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.util.*;import java.util.zip.*;
public final class EndpointRedactionTest {
  static int checks;static void check(boolean yes,String name){if(!yes)throw new AssertionError(name);checks++;}
  static byte[] read(InputStream in)throws IOException{ByteArrayOutputStream out=new ByteArrayOutputStream();CobraDiagnosticArchive.copy(in,out);return out.toByteArray();}
  static String clean(String s){return CobraDiagnosticArchive.redact(s,Collections.emptyList());}
  static void endpoint(String text,String name,String...secret){String out=clean(text);for(String s:secret)check(!out.contains(s),name+" privacy");check(out.contains("[redacted-endpoint]"),name+" marker");}
  public static void main(String[] args)throws Exception{
    String endpoint="edge.example.test/203.0.113.29:80";
    String stack="java.io.IOException: java.util.concurrent.ExecutionException: java.net.ConnectException: Failed to connect to "+endpoint+"\n  at androidx.media3.datasource.okhttp.OkHttpDataSource.open(OkHttpDataSource.java:278)\njava.net.ConnectException: Failed to connect to "+endpoint;
    endpoint(stack,"nested real-shape synthetic exception","edge.example.test","203.0.113.29");
    String cleaned=clean(stack);check(cleaned.contains("java.net.ConnectException")&&cleaned.contains("OkHttpDataSource.java:278"),"cause classes and stack location retained");
    endpoint("{\"detail\":\""+stack.replace("\n","\\n")+"\",\"version_code\":2103197}","JSON escaped nested exception","edge.example.test","203.0.113.29");
    endpoint("remote="+endpoint+"; reason=reset","InetSocketAddress diagnostic","edge.example.test","203.0.113.29");
    endpoint("remote=/203.0.113.29:443","unnamed IPv4 endpoint","203.0.113.29");
    endpoint("remote=edge.example.test/203.0.113.29","InetAddress without port","edge.example.test","203.0.113.29");
    endpoint("remote=203.0.113.29:80","standalone IPv4 port","203.0.113.29");
    endpoint("Failed to connect to edge.example.test:443","hostname-only connect endpoint","edge.example.test");
    endpoint("Failed to connect to edge.example.test/[2001:db8::29]:443","IPv6 endpoint","edge.example.test","2001:db8::29");
    endpoint("remote=/[2001:db8::29]:443","unnamed IPv6 endpoint","2001:db8::29");
    endpoint("remote=[fe80::1%wlan0]:443","IPv6 scope","fe80::1","wlan0");
    endpoint("remote=edge.example.test\\/203.0.113.29:80","JSON escaped slash","edge.example.test","203.0.113.29");
    endpoint("Failed to connect to edge.example.test:80\\n  at OkHttpDataSource.open(OkHttpDataSource.java:278)","escaped newline boundary","edge.example.test");
    check(clean("Failed to connect to edge.example.test:80\\n  at OkHttpDataSource.open(OkHttpDataSource.java:278)").contains("\\n  at OkHttpDataSource.open(OkHttpDataSource.java:278)"),"JSON line escape preserved");
    String diagnostic="{\"cobra_version\":\"1.0.9-Cobra-Original-Player-Menu-RC1\",\"skin_version\":\"1.0.5.98\",\"version_code\":2103197,\"at\":\"2026-09-20T05:17:03.534Z\",\"captured_at_ms\":1789881423534,\"network_mode\":\"IPv4 only\",\"format\":\"avc1.640020\",\"size\":\"1280x720\"}";
    check(clean(diagnostic).equals(diagnostic),"version identity timestamp family codecs and geometry retained exactly");
    check(clean(" at com.projectinfinity.kodi.InfinityLiveActivity.foo(InfinityLiveActivity.java:17898)").equals(" at com.projectinfinity.kodi.InfinityLiveActivity.foo(InfinityLiveActivity.java:17898)"),"source class package and line retained exactly");
    check(clean(cleaned).equals(cleaned),"redaction idempotence");
    String huge=String.join("",Collections.nCopies(10000,"not.an.endpoint.and.not.a.secret "));long start=System.nanoTime();check(clean(huge).equals(huge),"large harmless text retained");check(System.nanoTime()-start<5_000_000_000L,"bounded adversarial scan");
    check(clean(String.join("",Collections.nCopies(CobraDiagnosticArchive.TOTAL_LIMIT+1,"x"))).equals("[omitted: oversized text]"),"existing whole-input size gate retained");
    Path dir=Files.createTempDirectory("endpoint-redaction-");File archive=dir.resolve("fixture.zip").toFile();Map<String,String> entries=new LinkedHashMap<>();entries.put("last-error.txt",stack);entries.put("snapshot.txt",diagnostic);CobraDiagnosticArchive.writeZip(archive,entries,Collections.emptyList());
    try(ZipFile z=new ZipFile(archive)){String e=new String(read(z.getInputStream(z.getEntry("last-error.txt"))),StandardCharsets.UTF_8);check(!e.contains("edge.example.test")&&!e.contains("203.0.113.29"),"ZIP final output catches endpoint");String s=new String(read(z.getInputStream(z.getEntry("snapshot.txt"))),StandardCharsets.UTF_8);check(s.equals(diagnostic),"ZIP keeps diagnostic values");}
    Files.delete(archive.toPath());Files.delete(dir);System.out.println("PASS: "+checks+" endpoint-redaction adversarial host assertions");
  }
}
