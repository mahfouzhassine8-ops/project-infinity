from pathlib import Path
import importlib.util, argparse, subprocess,json,hashlib
spec=importlib.util.spec_from_file_location('helpers',Path(__file__).resolve().parents[1]/'apply_timeshift.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

def stop_member(s):
 marker='    void stop(){';start=s.index(marker);end=s.index('\n    private static void delete',start);return s[start:end]

def create(source,out):
 s=source.read_text();session=s[s.index('  private static final class CobraLocalTimeshiftSession {'):s.index('  private String mCobraLastLiveDiagnosticsSnapshot',s.index('  private static final class CobraLocalTimeshiftSession {'))] if '  private String mCobraLastLiveDiagnosticsSnapshot' in s else s[s.index('  private static final class CobraLocalTimeshiftSession {'):]
 methods='\n'.join(mod.member(session,name) for name in ('ingestLoop','writePacket','openSegment','finishSegment','delete'))+'\n'+stop_member(session)
 extra='private volatile okhttp3.Call activeProviderCall;' if 'activeProviderCall' in session else ''
 j=r'''import java.io.*;import java.net.*;import java.util.*;import java.util.concurrent.*;import java.util.concurrent.atomic.*;
public class ActualStopHarness {
 static class android {static class os {static class SystemClock {static long elapsedRealtime(){return System.nanoTime()/1000000L;}}}}
 static class CobraTimeshiftTransportPolicy {static final long INITIAL_BACKOFF_MS=250L;static long nextBackoffMs(long n){return 500;}static long publishedSegmentDurationMs(long a,long b){return Math.max(250,b-a);}static volatile CountDownLatch readyEntered,readyRelease;static boolean startupReady(long n){if(readyEntered!=null){readyEntered.countDown();awaitIgnoringInterrupt(readyRelease);}return n>=21000;}}
 static class CobraNetworkFamilyPolicy {static String routeFingerprint(String s){return "safe";}}
 static class okhttp3 {
  static class Request {String u;Url url(){return new Url();}static class Builder {String u;Builder url(String s){u=s;return this;}Builder header(String a,String b){return this;}Request build(){Request r=new Request();r.u=u;return r;}}}
  static class Url {String host(){return "127.0.0.1";}}
  static class Client {final int port;volatile Call last;final AtomicInteger creations=new AtomicInteger();volatile boolean holdCreation=false;final CountDownLatch creationEntered=new CountDownLatch(1),creationRelease=new CountDownLatch(1);Client(int port){this.port=port;}Call newCall(Request r){creations.incrementAndGet();Call c=new Call(port,r);last=c;if(holdCreation){creationEntered.countDown();awaitIgnoringInterrupt(creationRelease);}return c;}}
  static class Call {final Socket socket=new Socket();final int port;final Request request;final CountDownLatch reading=new CountDownLatch(1);volatile boolean cancelled,closed;final AtomicInteger executes=new AtomicInteger();Call(int p,Request r){port=p;request=r;}Response execute()throws IOException{executes.incrementAndGet();if(cancelled)throw new IOException("cancelled");socket.connect(new InetSocketAddress("127.0.0.1",port));return new Response(this);}void cancel(){cancelled=true;try{socket.close();}catch(IOException ignored){}}}
  static class Response implements AutoCloseable {final Call call;Response(Call c){call=c;}int code(){return 200;}Request request(){return call.request;}Object protocol(){return "HTTP/1.1";}String header(String h){return null;}ResponseBody body(){return new ResponseBody(call);}public void close(){call.closed=true;try{call.socket.close();}catch(IOException ignored){}}}
  static class ResponseBody {final Call call;ResponseBody(Call c){call=c;}Object contentType(){return "video/mp2t";}long contentLength(){return -1;}InputStream byteStream()throws IOException{InputStream raw=call.socket.getInputStream();return new FilterInputStream(raw){@Override public int read(byte[] b,int off,int len)throws IOException{call.reading.countDown();return super.read(b,off,len);}};}}
 }
 private static final int PACKET=188,SEGMENT_MS=3000;
 private final File directory;private final String source="http://127.0.0.1/live.ts";private final Map<String,String> headers=new HashMap<>();private final okhttp3.Client providerClient;
 private volatile boolean stopped=false,ready=false,timelineNormalizerActive=false;private volatile String state="STARTING",lastError="",providerFinalHostHash="",providerResponseProtocol="",providerResponseHeaderHash="",providerContentType="";
 private volatile int providerHttpCode=-1;private volatile long providerContentLength=-1,stallMs=0,bytesRead=0,reconnects=0,providerLastPacketElapsed=0;
 private final Object liveLock=new Object(),lock=new Object();private final CountDownLatch readyLatch=new CountDownLatch(1);private final Queue<byte[]> liveQueue=new ArrayDeque<>();private Socket liveSocket;private OutputStream liveOut;private Thread liveWriterThread,serverThread,ingestThread;private ServerSocket server;
 private BufferedOutputStream segmentOut;private File segmentPart;private long sequence=1,totalBytes=0,discontinuitiesBefore=0,segmentStartElapsed=0,segmentLastPacketElapsed=0,segmentStartWall=0,segmentBytes=0,segmentDiscontinuitySequence=0,maxPublishedDurationMs=0,publishedSegments=0,totalSegmentBytes=0,minSegmentBytes=Long.MAX_VALUE,maxSegmentBytes=0,lastSegmentPublishedElapsed=0,readyElapsed=0;
 private boolean segmentDiscontinuity=false,pendingDiscontinuity=false,everConnected=false,synced=false;
 private int carryLen=0;private final int[] continuity=new int[8];private final long[] lastPcr90k=new long[8],lastPts90k=new long[8];
 private final ArrayDeque<Segment> segments=new ArrayDeque<>();private final int storageSegments=20;private final long maxBytes=1024*1024;
 private static class Segment {final long seq,duration,length;final File file;Segment(long a,long b,long c,long d,File f,boolean e,long g){seq=a;duration=b;length=d;file=f;}}
 private final CountDownLatch writerBetweenCheckAndWrite=new CountDownLatch(1),writerMayContinue=new CountDownLatch(1);private boolean holdWriter=false;
 ActualStopHarness(int port)throws Exception{providerClient=new okhttp3.Client(port);directory=java.nio.file.Files.createTempDirectory("cobra-stop-test-").toFile();}
 private void observeProviderRead(int n){}private void broadcastLive(byte[] b,int n){}private void consume(byte[] b,int n)throws IOException{}private void activatePendingTimelineNormalizer(){}private void resetTimelineNormalizerAnchors(){}
 private void observeContinuity(byte[] b,int off){if(!holdWriter)return;writerBetweenCheckAndWrite.countDown();boolean done=false;while(!done)try{writerMayContinue.await();done=true;}catch(InterruptedException ignored){}}
 private void maybeScheduleTimelineNormalizer(){}private void normalizeTimelinePacket(byte[] b,int off){}private void broadcastNormalizedPacket(byte[] b,int off){}private long windowDurationMs(){return 30000;}
''' +extra+'\n'+methods+r'''
 static void awaitIgnoringInterrupt(CountDownLatch latch){boolean done=false;while(!done)try{latch.await();done=true;}catch(InterruptedException ignored){}}
 static void awaitCleanup(File directory)throws Exception{long until=System.nanoTime()+TimeUnit.SECONDS.toNanos(2);while(directory.exists()&&System.nanoTime()<until)Thread.sleep(10);}
 static long cleanupThreads(){return Thread.getAllStackTraces().keySet().stream().filter(t->t.isAlive()&&t.getName().equals("CobraTimeshiftCleanup")).count();}
 static void check(boolean p,String message){if(!p)throw new AssertionError(message);}
 static int failures;
 static void test(String name,ThrowingRunnable task){try{task.run();System.out.println("PASS "+name);}catch(Throwable t){failures++;System.out.println("FAIL "+name+": "+t.getMessage());}}
 interface ThrowingRunnable {void run()throws Exception;}
 public static void main(String[] args)throws Exception{
 test("stop cancels actual blocked socket read promptly",()->{
  try(ServerSocket peer=new ServerSocket(0)) {
   ActualStopHarness h=new ActualStopHarness(peer.getLocalPort());h.ingestThread=new Thread(h::ingestLoop,"ActualIngest");h.ingestThread.start();
   try(Socket accepted=peer.accept()){
    okhttp3.Call call=h.providerClient.last;check(call.reading.await(2,TimeUnit.SECONDS),"read never blocked");long start=System.nanoTime();h.stop();h.ingestThread.join(250);long ms=(System.nanoTime()-start)/1000000;
    boolean alive=h.ingestThread.isAlive();System.out.println("EVIDENCE stop_ms="+ms+" ingest_alive="+alive+" call_cancelled="+call.cancelled+" response_closed="+call.closed);
    if(alive)accepted.close();h.ingestThread.join(2000);
    check(!alive,"blocked provider read survived stop/interrupt");check(call.cancelled,"active provider call was not cancelled");check(call.closed,"response owner did not close response");check(h.providerClient.creations.get()==1,"cancelled stop retried provider");
   }finally{h.stop();h.ingestThread.join(2000);delete(h.directory);}
  }
 });
 test("stop cannot close segment between writer check and write",()->{
  ActualStopHarness h=new ActualStopHarness(1);h.holdWriter=true;AtomicReference<Throwable> writerFailure=new AtomicReference<>();
  h.ingestThread=new Thread(()->{try{h.writePacket(new byte[188],0);}catch(Throwable t){writerFailure.set(t);}finally{h.finishSegment(false);}},"ActualPacketWriter");h.ingestThread.start();
  try {check(h.writerBetweenCheckAndWrite.await(2,TimeUnit.SECONDS),"writer never reached checkpoint");h.stop();h.writerMayContinue.countDown();h.ingestThread.join(2000);
   Throwable error=writerFailure.get();System.out.println("EVIDENCE writer_error="+(error==null?"none":error.getClass().getSimpleName()));check(error==null,"stop invalidated active writer: "+error);
  }finally{h.writerMayContinue.countDown();h.ingestThread.join(2000);delete(h.directory);}
 });
 test("stop racing call publication cancels before execute",()->{
  ActualStopHarness h=new ActualStopHarness(1);h.providerClient.holdCreation=true;h.ingestThread=new Thread(h::ingestLoop,"ActualPublishRace");h.ingestThread.start();
  try {check(h.providerClient.creationEntered.await(2,TimeUnit.SECONDS),"call publication checkpoint missed");h.stop();h.providerClient.creationRelease.countDown();h.ingestThread.join(2000);
   okhttp3.Call c=h.providerClient.last;check(c.cancelled,"call published after stop was not cancelled");check(c.executes.get()==0,"stopped call reached execute");check(h.providerClient.creations.get()==1,"stopped ingest reopened provider");check("STOPPED".equals(h.state),"terminal state lost");
  } finally {h.providerClient.creationRelease.countDown();h.ingestThread.join(2000);awaitCleanup(h.directory);delete(h.directory);}
 });
 test("cleanup waits for ingest and double stop stays idempotent",()->{
  // Drain cleanup workers from earlier scenarios before counting this session.
  Thread.sleep(1000L);
  ActualStopHarness h=new ActualStopHarness(1);h.holdWriter=true;AtomicReference<Throwable> writerFailure=new AtomicReference<>();
  h.ingestThread=new Thread(()->{try{h.writePacket(new byte[188],0);}catch(Throwable t){writerFailure.set(t);}finally{h.finishSegment(false);}},"ActualCleanupOwner");h.ingestThread.start();
  boolean retained=false;long workers=0;long elapsed=0;
  try {check(h.writerBetweenCheckAndWrite.await(2,TimeUnit.SECONDS),"writer checkpoint missed");long before=cleanupThreads(),start=System.nanoTime();h.stop();h.stop();elapsed=(System.nanoTime()-start)/1000000;workers=cleanupThreads()-before;Thread.sleep(1100L);retained=h.directory.exists();
  } finally {h.writerMayContinue.countDown();h.ingestThread.join(2000);awaitCleanup(h.directory);}
  System.out.println("EVIDENCE double_stop_ms="+elapsed+" cleanup_workers="+workers+" directory_retained_until_owner_exit="+retained+" directory_removed="+!h.directory.exists());
  check(elapsed<100L,"stop blocked waiting for ingest");check(workers==1L,"double stop launched redundant cleanup workers");check(retained,"cleanup deleted files before ingest exited");check(!h.directory.exists(),"cleanup did not remove completed session");check(writerFailure.get()==null,"writer failed during cleanup");
 });
 test("late segment readiness cannot replace terminal STOPPED",()->{
  ActualStopHarness h=new ActualStopHarness(1);h.openSegment();h.segmentBytes=188L*50L;
  CobraTimeshiftTransportPolicy.readyEntered=new CountDownLatch(1);CobraTimeshiftTransportPolicy.readyRelease=new CountDownLatch(1);
  h.ingestThread=new Thread(()->h.finishSegment(true),"ActualLateReady");h.ingestThread.start();
  try {check(CobraTimeshiftTransportPolicy.readyEntered.await(2,TimeUnit.SECONDS),"readiness checkpoint missed");h.stop();CobraTimeshiftTransportPolicy.readyRelease.countDown();h.ingestThread.join(2000);check("STOPPED".equals(h.state),"late publication changed state to "+h.state);check(!h.ready,"stopped session published readiness");
  } finally {CobraTimeshiftTransportPolicy.readyRelease.countDown();h.ingestThread.join(2000);CobraTimeshiftTransportPolicy.readyEntered=null;CobraTimeshiftTransportPolicy.readyRelease=null;awaitCleanup(h.directory);delete(h.directory);}
 });
 System.out.println("TOTAL failures="+failures);System.exit(failures==0?0:1);
 }
}
'''
 out.mkdir(parents=True,exist_ok=True);(out/'ActualStopHarness.java').write_text(j)
 c=subprocess.run(['java','com.sun.tools.javac.Main',str(out/'ActualStopHarness.java')],capture_output=True,text=True)
 if c.returncode:raise RuntimeError(c.stderr)
 r=subprocess.run(['java','-cp',str(out),'ActualStopHarness'],capture_output=True,text=True,timeout=15)
 result={'source_sha256':hashlib.sha256(s.encode()).hexdigest(),'kind':'actual Java stop/ingest/write/finish methods; controlled okhttp collaborator backed by real loopback SocketInputStream; not actual OkHttp, Android or device test','exit_code':r.returncode,'output':r.stdout}
 (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();raise SystemExit(create(a.source,a.out)['exit_code'])
