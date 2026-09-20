#!/usr/bin/env python3
"""Extract actual provider methods and test bounded HTTP/resource ownership.

Deterministic fake HTTP, descriptors and thread scheduling; no device/network claim.
"""
import argparse, hashlib, json, subprocess
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('--provider',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
text=a.provider.read_text();a.out.mkdir(parents=True,exist_ok=True)
resolver=text[text.index('  private static String getFinalURL('):text.index('  @Override\n  public Cursor query(')]
transfer=text[text.index('  static class TransferThread extends Thread'):text.rfind('}')]
resolver=resolver.replace('  @Override\n','')
HARNESS=r'''
  static final String TAG="host";
  static int assertions;
  static void check(boolean value,String name){assertions++;if(!value)throw new AssertionError(name);}
  static class Log { static void e(String tag,String message){} static void e(String tag,String message,Throwable error){} }
  static class TimingLogger { TimingLogger(String tag,String name){}void addSplit(String name){}void dumpToLog(){} }
  static class Uri { final String value;Uri(String v){value=v;}String getFragment(){return value;} }
  static class Thread { static boolean fail;public void start(){if(fail)throw new IllegalStateException("thread start");run();}public void run(){} }
  static class ParcelFileDescriptor implements Closeable {
    static boolean failCreate,failWrite,failClose;
    static ParcelFileDescriptor[] last;
    boolean closed;
    public void close()throws IOException{closed=true;}
    static ParcelFileDescriptor[] createPipe()throws IOException{
      if(failCreate)throw new IOException("pipe");
      return last=new ParcelFileDescriptor[]{new ParcelFileDescriptor(),new ParcelFileDescriptor()};
    }
    static class AutoCloseOutputStream extends OutputStream{
      final ParcelFileDescriptor p;final ByteArrayOutputStream bytes=new ByteArrayOutputStream();
      AutoCloseOutputStream(ParcelFileDescriptor p){this.p=p;}
      public void write(int b)throws IOException{if(failWrite)throw new IOException("consumer closed");bytes.write(b);}
      public void write(byte[] b,int off,int len)throws IOException{if(failWrite)throw new IOException("consumer closed");bytes.write(b,off,len);}
      public void close()throws IOException{p.close();if(failClose)throw new IOException("output close");}
    }
  }
  static class Input extends ByteArrayInputStream{
    boolean closed,failClose,failRead;
    Input(){super(new byte[]{1,2,3,4});}
    public synchronized int read(byte[] b,int o,int n){if(failRead)throw new IllegalStateException("read failure");return super.read(b,o,n);}
    public void close()throws IOException{closed=true;if(failClose)throw new IOException("input close");super.close();}
  }
  static class Spec {
    final int status;final String location;boolean failHeaders,failInput;final Input input=new Input();
    Spec(int s,String l){status=s;location=l;}
  }
  static final java.util.ArrayDeque<Spec> pending=new java.util.ArrayDeque<>();
  static final java.util.ArrayList<Connection> opened=new java.util.ArrayList<>();
  static class Connection extends HttpURLConnection{
    final Spec spec;boolean disconnected;
    Connection(URL u,Spec s){super(u);spec=s;}
    public void connect(){}
    public boolean usingProxy(){return false;}
    public void disconnect(){disconnected=true;}
    void bounded(){check(getConnectTimeout()==15000,"finite connect timeout");check(getReadTimeout()==15000,"finite read timeout");}
    public int getResponseCode()throws IOException{bounded();check(!getInstanceFollowRedirects(),"manual redirect bound");if(spec.failHeaders)throw new IOException("headers");return spec.status;}
    public String getHeaderField(String name){return "Location".equals(name)?spec.location:null;}
    public InputStream getInputStream()throws IOException{bounded();if(spec.failInput)throw new IOException("stream");return spec.input;}
  }
  static void reset(){pending.clear();opened.clear();ParcelFileDescriptor.last=null;ParcelFileDescriptor.failCreate=false;ParcelFileDescriptor.failWrite=false;ParcelFileDescriptor.failClose=false;Thread.fail=false;}
  static Spec add(int status,String location){Spec s=new Spec(status,location);pending.add(s);return s;}
  static void disconnected(){for(Connection c:opened)check(c.disconnected,"connection disconnected: "+c.getURL());}
  interface Operation {void run()throws Exception;}
  static void ioFailure(Operation action)throws Exception{boolean threw=false;try{action.run();}catch(IOException e){threw=true;}check(threw,"expected IOException");}
  public static void main(String[] ignored)throws Exception{
    URL.setURLStreamHandlerFactory(protocol -> (protocol.equals("http")||protocol.equals("https"))?new URLStreamHandler(){
      protected URLConnection openConnection(URL u)throws IOException{
        if(pending.isEmpty())throw new AssertionError("unexpected connection "+u);
        Connection c=new Connection(u,pending.remove());opened.add(c);return c;
      }
    }:null);
    reset();add(200,null);check(getFinalURL("http://test.example/a").equals("http://test.example/a"),"direct URL preserved");disconnected();
    reset();add(301,"/b");add(302,"https://test.example/c");add(200,null);check(getFinalURL("http://test.example/a").equals("https://test.example/c"),"relative and absolute redirect");check(opened.size()==3,"three requests");disconnected();
    reset();for(int i=0;i<21;i++)add(302,"/loop");ioFailure(()->getFinalURL("http://test.example/loop"));check(opened.size()==21,"redirect budget hard bound");disconnected();
    reset();for(int i=0;i<20;i++)add(301,"/hop"+i);add(200,null);check(getFinalURL("http://test.example/a").endsWith("hop19"),"twenty redirects accepted");disconnected();
    for(String location:new String[]{null,"", "   "}){reset();add(302,location);ioFailure(()->getFinalURL("http://test.example/a"));disconnected();}
    reset();add(500,null);ioFailure(()->getFinalURL("http://test.example/a"));disconnected();
    reset();add(200,null).failHeaders=true;ioFailure(()->getFinalURL("http://test.example/a"));disconnected();
    for(String bad:new String[]{"file:///tmp/benign-test", "ftp://test.example/a"}){
      reset();ioFailure(()->getFinalURL(bad));check(opened.isEmpty(),"unsupported initial protocol does not open");
      reset();add(302,bad);ioFailure(()->getFinalURL("http://test.example/a"));check(opened.size()==1,"unsupported redirect protocol rejected");disconnected();
    }
    YtdlHost provider=new YtdlHost();
    reset();ioFailure(()->provider.openFile(new Uri(null),"r"));check(opened.isEmpty(),"missing URI opens nothing");
    reset();ioFailure(()->provider.openFile(new Uri("file:///tmp/benign-test"),"r"));check(ParcelFileDescriptor.last==null,"non-HTTP openFile allocates no pipe");
    reset();add(200,null);Spec success=add(200,null);ParcelFileDescriptor reader=provider.openFile(new Uri("http://test.example/a"),"r");check(!reader.closed,"read descriptor returned open");check(ParcelFileDescriptor.last[1].closed,"writer closed after EOF");check(success.input.closed,"input closed after EOF");reader.close();disconnected();
    reset();add(200,null);add(200,null).failInput=true;ioFailure(()->provider.openFile(new Uri("http://test.example/a"),"r"));check(ParcelFileDescriptor.last==null,"no descriptors before successful input");disconnected();
    reset();add(200,null);Spec failPipe=add(200,null);ParcelFileDescriptor.failCreate=true;ioFailure(()->provider.openFile(new Uri("http://test.example/a"),"r"));check(failPipe.input.closed,"pipe failure closes input");disconnected();
    reset();add(200,null);Spec failStart=add(200,null);Thread.fail=true;boolean rejected=false;try{provider.openFile(new Uri("http://test.example/a"),"r");}catch(IllegalStateException e){rejected=true;}check(rejected,"thread start failure propagated");check(failStart.input.closed,"thread failure closes input");for(ParcelFileDescriptor fd:ParcelFileDescriptor.last)check(fd.closed,"thread failure closes descriptor");disconnected();
    for(int failure=0;failure<3;failure++){
      reset();add(200,null);Spec stream=add(200,null);
      if(failure==0)ParcelFileDescriptor.failWrite=true;
      if(failure==1)stream.input.failClose=true;
      if(failure==2)ParcelFileDescriptor.failClose=true;
      ParcelFileDescriptor r=provider.openFile(new Uri("http://test.example/a"),"r");check(stream.input.closed,"input closed despite writer/close failure");check(ParcelFileDescriptor.last[1].closed,"writer closed despite input close failure");r.close();disconnected();
    }
    System.out.println("PASS: "+assertions+" bounded redirect/protocol/timeout/resource assertions; fake network/descriptors/scheduling only.");
  }
'''
source=a.out/'YtdlHost.java';source.write_text('import java.io.*;\nimport java.net.*;\npublic final class YtdlHost {\n'+resolver+transfer+HARNESS+'\n}\n')
subprocess.run(['java','com.sun.tools.javac.Main',str(source)],check=True)
result=subprocess.run(['java','-cp',str(a.out.resolve()),'YtdlHost'],text=True,capture_output=True)
report={'provider_sha256':hashlib.sha256(text.encode()).hexdigest(),'exit_code':result.returncode,'stdout':result.stdout.strip(),'stderr':result.stderr.strip(),'verification_level':'extracted production HTTP/resource methods with deterministic fakes','physical_device_verified':False,'real_http_server_tested':False}
(a.out/'ytdl-host-result.json').write_text(json.dumps(report,indent=2)+'\n')
print(result.stdout.strip());print(result.stderr.strip());raise SystemExit(result.returncode)
