package com.projectinfinity.kodi;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.InterfaceAddress;
import java.net.NetworkInterface;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.SynchronousQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import okhttp3.Authenticator;
import okhttp3.Call;
import okhttp3.ConnectionPool;
import okhttp3.CookieJar;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

/** One current progressive stream, one chosen receiver, bounded owned I/O.
 * No provider credentials/URI leave the phone. No global client, socket, DNS,
 * proxy or cookie settings are changed. No files/database/server service.
 * Uses private Cast-only HTTP code; no existing Cobra class is called/replaced.
 */
final class InfinityCastRelay implements AutoCloseable {
    interface Ready {void ready(InfinityCastRelay relay,String mime,String failure);}
    private static final ThreadPoolExecutor io=new ThreadPoolExecutor(0,2,30,TimeUnit.SECONDS,
        new SynchronousQueue<>(),r->{Thread t=new Thread(r,"InfinityCastMediaIO");t.setDaemon(true);return t;});
    private static final ThreadPoolExecutor lifecycle=new ThreadPoolExecutor(0,1,30,TimeUnit.SECONDS,
        new LinkedBlockingQueue<>(2),r->{Thread t=new Thread(r,"InfinityCastMediaOwner");t.setDaemon(true);return t;});
    private static InfinityCastRelay active;
    private final InfinityCastSource source;
    private final InetAddress receiver;
    private final ServerSocket listener;
    private final String path;
    private final OkHttpClient upstream;
    private final Set<Socket> clients=Collections.newSetFromMap(new ConcurrentHashMap<Socket,Boolean>());
    private final Set<Call> calls=Collections.newSetFromMap(new ConcurrentHashMap<Call,Boolean>());
    private final Map<Response,Call> responses=new ConcurrentHashMap<>();
    private final AtomicInteger jobs=new AtomicInteger();
    private volatile boolean closed,ownerDone;
    private volatile String mime;
    private InfinityCastRelay(InetAddress receiver,InetAddress local,InfinityCastSource source) throws IOException {
        this.receiver=receiver;this.source=source;
        path="/"+UUID.randomUUID().toString().replace("-","")+"/media";
        upstream=new OkHttpClient.Builder().cookieJar(CookieJar.NO_COOKIES).authenticator(Authenticator.NONE)
            .proxyAuthenticator(Authenticator.NONE).followRedirects(false).followSslRedirects(false)
            .retryOnConnectionFailure(false).cache(null).connectionPool(new ConnectionPool(2,5,TimeUnit.SECONDS))
            .connectTimeout(3500,TimeUnit.MILLISECONDS).readTimeout(4000,TimeUnit.MILLISECONDS)
            .writeTimeout(4000,TimeUnit.MILLISECONDS).build();
        listener=new ServerSocket();listener.setReuseAddress(false);
        try{listener.bind(new InetSocketAddress(local,0),2);}catch(IOException failed){listener.close();throw failed;}
    }
    static synchronized InfinityCastRelay start(InetAddress receiver,InfinityCastSource source,Ready callback) throws IOException {
        if(active!=null)throw new IOException("Previous Cast transport still owned");
        if(!(receiver instanceof Inet4Address) || receiver.isAnyLocalAddress() || source==null)
            throw new IOException("Unsupported receiver address or source");
        InetAddress local=localAddress(receiver);
        InfinityCastRelay relay=new InfinityCastRelay(receiver,local,source);active=relay;relay.jobs.incrementAndGet();
        try {
            io.execute(()->{
                String problem=null;String type=null;
                try {
                    type=relay.probe();
                    if(relay.closed)return;
                    if(type==null)throw new IOException("Unsupported progressive media");
                    relay.mime=type;
                    lifecycle.execute(relay::accept);
                } catch(Exception failure){relay.close();problem="Media transport unavailable or unsupported";}
                finally {relay.jobs.decrementAndGet();relay.retired();}
                // A consumer exception cannot turn a delivered success into a
                // second failure callback, or strand the transport owner.
                try{callback.ready(relay,type,problem);}catch(RuntimeException rejected){relay.close();}
            });
        } catch(RuntimeException unavailable){relay.jobs.decrementAndGet();relay.close();throw new IOException("Cast transport busy");}
        return relay;
    }
    private static InetAddress localAddress(InetAddress peer) throws IOException {
        for(NetworkInterface network:Collections.list(NetworkInterface.getNetworkInterfaces())) {
            if(!network.isUp())continue;
            for(InterfaceAddress address:network.getInterfaceAddresses()) {
                InetAddress value=address.getAddress();
                if(!(value instanceof Inet4Address) || value.isAnyLocalAddress() ||
                    (value.isLoopbackAddress()!=peer.isLoopbackAddress()))continue;
                int prefix=address.getNetworkPrefixLength();if(prefix<1 || prefix>32)continue;
                byte[] a=value.getAddress(),b=peer.getAddress();boolean match=true;
                for(int bit=0;bit<prefix;bit++)if((a[bit/8]&(1<<(7-bit%8)))!=(b[bit/8]&(1<<(7-bit%8)))){match=false;break;}
                if(match)return value;
            }
        }
        throw new IOException("No direct local route to receiver");
    }
    String address(){return "http://"+listener.getInetAddress().getHostAddress()+":"+listener.getLocalPort()+path;}
    boolean closed(){return closed;}
    static synchronized boolean busy(){return active!=null;}
    private boolean sameOrigin(URI a,URI b) {
        int ap=a.getPort()<0?("https".equalsIgnoreCase(a.getScheme())?443:80):a.getPort();
        int bp=b.getPort()<0?("https".equalsIgnoreCase(b.getScheme())?443:80):b.getPort();
        return a.getScheme().equalsIgnoreCase(b.getScheme()) && a.getHost().equalsIgnoreCase(b.getHost()) && ap==bp;
    }
    private Response open(String method,String range) throws IOException {
        URI target=source.uri;boolean privateHeaders=true;
        for(int redirects=0;redirects<=5;redirects++) {
            if(closed)throw new IOException("Cast transport closed");
            Request.Builder request=new Request.Builder().url(target.toASCIIString()).method(method,null)
                .header("Accept-Encoding","identity").header("User-Agent","InfinityCast/1");
            if(privateHeaders)for(Map.Entry<String,String> header:source.headers.entrySet())request.header(header.getKey(),header.getValue());
            if(range!=null)request.header("Range",range);
            Call call=upstream.newCall(request.build());calls.add(call);
            if(closed){call.cancel();calls.remove(call);throw new IOException("Cast transport closed");}
            Response result;
            try {result=call.execute();} catch(IOException | RuntimeException failed){call.cancel();calls.remove(call);throw new IOException("Source connection unavailable");}
            if(closed){result.close();calls.remove(call);throw new IOException("Cast transport closed");}
            int code=result.code();
            if(code==301 || code==302 || code==303 || code==307 || code==308) {
                String location=result.header("Location");result.close();calls.remove(call);
                if(location==null || redirects==5)throw new IOException("Source redirect unavailable");
                URI next;
                try {next=target.resolve(location);}catch(IllegalArgumentException invalid){throw new IOException("Invalid source redirect");}
                if(next.getHost()==null || next.getRawUserInfo()!=null ||
                    !("http".equalsIgnoreCase(next.getScheme()) || "https".equalsIgnoreCase(next.getScheme())) ||
                    ("https".equalsIgnoreCase(target.getScheme()) && !"https".equalsIgnoreCase(next.getScheme())))
                    throw new IOException("Unsupported source redirect");
                if(!sameOrigin(target,next))privateHeaders=false;
                target=next;continue;
            }
            responses.put(result,call);return result;
        }
        throw new IOException("Source redirect limit");
    }
    private void release(Response response) {
        try{response.close();}finally{Call call=responses.remove(response);if(call!=null)calls.remove(call);}
    }
    private String probe() throws IOException {
        Response response=open("HEAD",null);
        try {
            if(response.code()==200 || response.code()==206)return InfinityCastSource.mime(response.header("Content-Type"),source.hint);
            if(response.code()!=405 && response.code()!=501)throw new IOException("Source metadata unavailable");
        } finally {release(response);}
        response=open("GET","bytes=0-0");
        try {
            if(response.code()!=200 && response.code()!=206)throw new IOException("Source metadata unavailable");
            return InfinityCastSource.mime(response.header("Content-Type"),source.hint);
        } finally {release(response);}
    }
    private void accept() {
        try {
            while(!closed) {
                Socket client=listener.accept();
                if(closed || !receiver.equals(client.getInetAddress())){client.close();continue;}
                clients.add(client);
                if(closed){clients.remove(client);client.close();continue;}
                jobs.incrementAndGet();
                try {io.execute(()->{try{serve(client);}finally{clients.remove(client);try{client.close();}catch(IOException ignored){}
                    jobs.decrementAndGet();retired();}});}
                catch(RuntimeException busy){jobs.decrementAndGet();clients.remove(client);client.close();}
            }
        } catch(IOException stopped) {} finally {close();cancelCalls();ownerDone=true;retired();}
    }
    private void serve(Socket client) {
        Response response=null;
        try {
            long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(2);
            client.setSoTimeout(2000);InputStream input=client.getInputStream();ByteArrayOutputStream header=new ByteArrayOutputStream();
            int value,tail=0;
            while(header.size()<8192) {
                long remaining=deadline-System.nanoTime();if(remaining<=0)return;
                client.setSoTimeout((int)Math.max(1,TimeUnit.NANOSECONDS.toMillis(remaining)));
                value=input.read();if(value==-1)break;
                header.write(value);tail=(tail<<8)|value;if(tail==0x0d0a0d0a)break;
            }
            if(tail!=0x0d0a0d0a)return;
            String[] lines=header.toString("US-ASCII").split("\r\n");String[] first=lines[0].split(" ");
            if(first.length!=3 || !first[1].equals(path) || !(first[2].equals("HTTP/1.1") || first[2].equals("HTTP/1.0")))return;
            String method=first[0];OutputStream output=client.getOutputStream();
            if(method.equals("OPTIONS")){reply(output,204,null,-1,null);return;}
            if(!(method.equals("GET") || method.equals("HEAD")))return;
            String range=null;
            for(int i=1;i<lines.length;i++)if(lines[i].toLowerCase(Locale.ROOT).startsWith("range:")) {
                if(range!=null)return;range=lines[i].substring(6).trim();
                if(!range.matches("bytes=[0-9]{0,16}-[0-9]{0,16}") || range.equals("bytes=-"))return;
            }
            response=open(method,range);
            if(response.code()!=200 && response.code()!=206){reply(output,502,null,-1,null);return;}
            if(!mime.equals(InfinityCastSource.mime(response.header("Content-Type"),source.hint))){reply(output,502,null,-1,null);return;}
            String contentRange=response.header("Content-Range");
            if(response.code()==206 && (contentRange==null || !contentRange.matches("bytes [0-9]{1,16}-[0-9]{1,16}/[0-9]{1,16}"))){reply(output,502,null,-1,null);return;}
            long length=response.body()==null?-1:response.body().contentLength();
            String declared=response.header("Content-Length");
            if(method.equals("HEAD") && declared!=null && declared.matches("[0-9]{1,16}"))length=Long.parseLong(declared);
            reply(output,response.code(),mime,length,contentRange);
            if(method.equals("GET") && response.body()!=null) {
                InputStream body=response.body().byteStream();byte[] buffer=new byte[65536];int count;
                while(!closed && (count=body.read(buffer))!=-1)output.write(buffer,0,count);
            }
        } catch(IOException | RuntimeException ignored) {
            // No URI, upstream headers, credentials, cookies or exception text.
        } finally {if(response!=null)release(response);}
    }
    private void reply(OutputStream output,int code,String type,long length,String range) throws IOException {
        String response="HTTP/1.1 "+code+" "+(code==200?"OK":code==206?"Partial Content":code==204?"No Content":"Unavailable")+"\r\n"+
            "Connection: close\r\nCache-Control: no-store\r\nAccess-Control-Allow-Origin: *\r\n"+
            "Access-Control-Allow-Methods: GET, HEAD, OPTIONS\r\nAccess-Control-Allow-Headers: Range\r\nAccess-Control-Allow-Private-Network: true\r\n";
        if(type!=null)response+="Content-Type: "+type+"\r\n";
        if(length>=0)response+="Content-Length: "+length+"\r\n";
        if(range!=null && range.matches("bytes [0-9]{1,16}-[0-9]{1,16}/[0-9]{1,16}"))response+="Content-Range: "+range+"\r\n";
        output.write((response+"\r\n").getBytes(StandardCharsets.US_ASCII));output.flush();
    }
    private void cancelCalls(){for(Call call:new ArrayList<>(calls))call.cancel();upstream.connectionPool().evictAll();}
    @Override public synchronized void close() {
        if(closed)return;closed=true;
        try{listener.close();}catch(IOException ignored){}
        for(Socket client:new ArrayList<>(clients))try{client.close();}catch(IOException ignored){}
        try {lifecycle.execute(()->{cancelCalls();ownerDone=true;retired();});}
        catch(RuntimeException full){/* one accept and one cancellation only; original owner retains cleanup */}
    }
    private void retired() {
        if(closed && ownerDone && jobs.get()==0)synchronized(InfinityCastRelay.class){if(active==this)active=null;}
    }
}
