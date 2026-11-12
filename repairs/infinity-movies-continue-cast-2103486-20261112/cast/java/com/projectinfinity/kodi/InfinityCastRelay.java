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
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import okhttp3.Authenticator;
import okhttp3.Call;
import okhttp3.ConnectionPool;
import okhttp3.CookieJar;
import okhttp3.Cookie;
import okhttp3.HttpUrl;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

/** One selected receiver and one actual source; all adaptive URLs stay sender-side. */
final class InfinityCastRelay implements AutoCloseable,InfinityCastAdaptive.Links {
    interface Ready {void ready(InfinityCastRelay relay,String mime,String failure);}
    private static final ThreadPoolExecutor io=new ThreadPoolExecutor(0,6,30,TimeUnit.SECONDS,
        new SynchronousQueue<>(),r->{Thread t=new Thread(r,"InfinityCastMediaIO");t.setDaemon(true);return t;});
    private static final ThreadPoolExecutor lifecycle=new ThreadPoolExecutor(0,1,30,TimeUnit.SECONDS,
        new LinkedBlockingQueue<>(2),r->{Thread t=new Thread(r,"InfinityCastMediaOwner");t.setDaemon(true);return t;});
    private static final Pattern VARIABLE=Pattern.compile("\\$(Number|Time)(?:%0([1-9][0-9]?)d)?\\$");
    private static InfinityCastRelay active;
    private static final class Resource {
        final URI uri;final InfinityCastAdaptive.Kind kind;final String hint,suffix;
        Resource(URI uri,InfinityCastAdaptive.Kind kind,String hint){this.uri=uri;this.kind=kind;this.hint=hint;this.suffix=suffix(uri,kind);}
    }
    private static final class Template {
        final String value,suffix;final String[] names;
        Template(String value,String[] names){this.value=value;this.names=names;this.suffix=suffix(URI.create(value),InfinityCastAdaptive.Kind.MEDIA);}
    }
    private final InfinityCastSource source;
    private final InetAddress receiver;
    private final ServerSocket listener;
    private final String path;
    private final Resource root;
    private final OkHttpClient upstream;
    private final CookieStore cookies=new CookieStore();
    /** Per-transfer RAM only. Standard cookie domain/path/secure/expiry rules. */
    private static final class CookieStore implements CookieJar {
        private static final class Entry {
            final Cookie cookie;final String origin;
            Entry(Cookie cookie,String origin){this.cookie=cookie;this.origin=origin;}
        }
        private final java.util.LinkedHashMap<String,Entry> values=new java.util.LinkedHashMap<>();
        private static String origin(URI uri){return uri.getScheme().toLowerCase(Locale.ROOT)+"://"+uri.getHost().toLowerCase(Locale.ROOT)+":"+(uri.getPort()>=0?uri.getPort():"https".equalsIgnoreCase(uri.getScheme())?443:80);}
        @Override public synchronized void saveFromResponse(HttpUrl url,java.util.List<Cookie> incoming) {
            String owner=origin(url.uri());
            for(Cookie cookie:incoming) {
                if(cookie.name().length()+cookie.value().length()+cookie.domain().length()+cookie.path().length()>4096)continue;
                String key=owner+"|"+cookie.domain()+"|"+cookie.path()+"|"+cookie.name();values.remove(key);values.put(key,new Entry(cookie,owner));
                while(values.size()>128)values.remove(values.keySet().iterator().next());
            }
        }
        @Override public java.util.List<Cookie> loadForRequest(HttpUrl url){return Collections.emptyList();}
        synchronized String header(URI target,String explicit) throws IOException {
            java.util.LinkedHashMap<String,String> merged=new java.util.LinkedHashMap<>();
            if(explicit!=null)for(String field:explicit.split(";")){int eq=field.indexOf('=');if(eq>0)merged.put(field.substring(0,eq).trim(),field.substring(eq+1).trim());}
            long now=System.currentTimeMillis();HttpUrl url=HttpUrl.get(target);String owner=origin(target);
            for(Entry entry:values.values()) {
                Cookie cookie=entry.cookie;
                if(owner.equals(entry.origin) && cookie.matches(url)) {
                    if(cookie.expiresAt()<=now)merged.remove(cookie.name());else merged.put(cookie.name(),cookie.value());
                }
            }
            StringBuilder result=new StringBuilder();for(Map.Entry<String,String> e:merged.entrySet()){if(result.length()>0)result.append("; ");result.append(e.getKey()).append('=').append(e.getValue());}
            if(result.length()>16384)throw new IOException("source_cookie_limit");return result.toString();
        }
        synchronized void clear(){values.clear();}
    }
    private final Map<String,Resource> resources=new ConcurrentHashMap<>();
    private final Map<String,String> ids=new ConcurrentHashMap<>();
    private final Map<String,Template> templates=new ConcurrentHashMap<>();
    private final Set<Socket> clients=Collections.newSetFromMap(new ConcurrentHashMap<Socket,Boolean>());
    private final Set<Call> calls=Collections.newSetFromMap(new ConcurrentHashMap<Call,Boolean>());
    private final Map<Response,Call> responses=new ConcurrentHashMap<>();
    private final AtomicInteger jobs=new AtomicInteger(),requests=new AtomicInteger();
    private volatile boolean closed,ownerDone;
    private volatile String mime,lastFailure="";
    private volatile boolean hlsFmp4,hlsSeparateAudio;
    String hlsVideoFormat(){return hlsFmp4?"fmp4":null;}
    String hlsAudioFormat(){return hlsFmp4 && !hlsSeparateAudio?"fmp4":null;}
    private InfinityCastRelay(InetAddress receiver,InetAddress local,InfinityCastSource source) throws IOException {
        this.receiver=receiver;this.source=source;
        path="/"+UUID.randomUUID().toString().replace("-","");root=new Resource(source.uri,InfinityCastAdaptive.Kind.MEDIA,source.hint);
        upstream=new OkHttpClient.Builder().cookieJar(cookies).authenticator(Authenticator.NONE)
            .proxyAuthenticator(Authenticator.NONE).followRedirects(false).followSslRedirects(false)
            .retryOnConnectionFailure(false).cache(null).connectionPool(new ConnectionPool(6,5,TimeUnit.SECONDS))
            .connectTimeout(3500,TimeUnit.MILLISECONDS).readTimeout(8000,TimeUnit.MILLISECONDS)
            .writeTimeout(4000,TimeUnit.MILLISECONDS).build();
        listener=new ServerSocket();listener.setReuseAddress(false);
        try{listener.bind(new InetSocketAddress(local,0),8);}catch(IOException failed){listener.close();throw failed;}
    }
    static synchronized InfinityCastRelay start(InetAddress receiver,InfinityCastSource source,Ready callback) throws IOException {
        if(active!=null)throw new IOException("previous_transport_draining");
        if(!(receiver instanceof Inet4Address) || receiver.isAnyLocalAddress() || source==null)throw new IOException("unsupported_receiver_route");
        InfinityCastRelay relay=new InfinityCastRelay(receiver,localAddress(receiver),source);active=relay;relay.jobs.incrementAndGet();
        try {
            io.execute(()->{
                String problem=null,type=null;
                try {
                    type=relay.probe();if(relay.closed)return;
                    if(type==null)throw new IOException("unsupported_media_type");
                    relay.mime=type;lifecycle.execute(relay::accept);
                    InfinityCastDiagnostics.event("relay","prepared",0);
                } catch(Exception failure){problem=relay.reason(failure);relay.close();}
                finally {relay.jobs.decrementAndGet();relay.retired();}
                try{callback.ready(relay,type,problem);}catch(RuntimeException rejected){relay.close();}
            });
        } catch(RuntimeException unavailable){relay.jobs.decrementAndGet();relay.close();throw new IOException("transport_busy");}
        return relay;
    }
    private String reason(Exception error) {
        String code=error.getMessage();if(code==null || !code.matches("[a-z_]{1,48}(?:_[0-9]{3})?"))code="source_network_or_transport_failure";
        lastFailure=code;InfinityCastDiagnostics.event("relay",code,0);return code;
    }
    private static InetAddress localAddress(InetAddress peer) throws IOException {
        for(NetworkInterface network:Collections.list(NetworkInterface.getNetworkInterfaces())) {
            if(!network.isUp())continue;
            for(InterfaceAddress address:network.getInterfaceAddresses()) {
                InetAddress value=address.getAddress();
                if(!(value instanceof Inet4Address) || value.isAnyLocalAddress() || (value.isLoopbackAddress()!=peer.isLoopbackAddress()))continue;
                int prefix=address.getNetworkPrefixLength();if(prefix<1 || prefix>32)continue;
                byte[] a=value.getAddress(),b=peer.getAddress();boolean match=true;
                for(int bit=0;bit<prefix;bit++)if((a[bit/8]&(1<<(7-bit%8)))!=(b[bit/8]&(1<<(7-bit%8)))){match=false;break;}
                if(match)return value;
            }
        }
        throw new IOException("no_direct_receiver_route");
    }
    private static String suffix(URI uri,InfinityCastAdaptive.Kind kind) {
        if(kind==InfinityCastAdaptive.Kind.HLS)return ".m3u8";if(kind==InfinityCastAdaptive.Kind.DASH)return ".mpd";
        if(kind==InfinityCastAdaptive.Kind.KEY)return ".key";if(kind==InfinityCastAdaptive.Kind.TEXT)return ".txt";
        String path=uri.getPath()==null?"":uri.getPath().toLowerCase(Locale.ROOT);
        for(String value:new String[]{".ts",".m4s",".mp4",".m4v",".webm",".vtt",".aac",".mp3"})if(path.endsWith(value))return value;
        return ".mp4"; // Opaque media endpoint; actual Content-Type still comes from source.
    }
    private String base(){return "http://"+listener.getInetAddress().getHostAddress()+":"+listener.getLocalPort()+path;}
    String address(){return base()+"/media"+("application/vnd.apple.mpegurl".equals(mime)?".m3u8":"application/dash+xml".equals(mime)?".mpd":root.suffix);}
    boolean closed(){return closed;}
    String failure(){return lastFailure;}
    static synchronized boolean busy(){return active!=null;}
    private static boolean sameOrigin(URI a,URI b) {
        int ap=a.getPort()<0?("https".equalsIgnoreCase(a.getScheme())?443:80):a.getPort();
        int bp=b.getPort()<0?("https".equalsIgnoreCase(b.getScheme())?443:80):b.getPort();
        return a.getScheme().equalsIgnoreCase(b.getScheme()) && a.getHost().equalsIgnoreCase(b.getHost()) && ap==bp;
    }
    @Override public boolean owned(String value){return value.startsWith(base()+"/r/") || value.startsWith(base()+"/t/");}
    @Override public synchronized String resource(URI uri,InfinityCastAdaptive.Kind kind) throws IOException {
        String key=kind+":"+uri.toASCIIString(),id=ids.get(key);
        if(id==null) {
            if(closed || resources.size()+templates.size()>=8192)throw new IOException("manifest_resource_limit");
            id=UUID.randomUUID().toString().replace("-","");ids.put(key,id);
            String hint=kind==InfinityCastAdaptive.Kind.HLS?"application/vnd.apple.mpegurl":kind==InfinityCastAdaptive.Kind.DASH?"application/dash+xml":null;
            resources.put(id,new Resource(uri,kind,hint));
        }
        return base()+"/r/"+id+"/media"+resources.get(id).suffix;
    }
    @Override public synchronized String template(URI base,String value,String representation,String bandwidth) throws IOException {
        if(value.contains("$RepresentationID$") && !representation.matches("[a-zA-Z0-9_.-]{1,128}"))throw new IOException("unsupported_representation_id");
        if(value.contains("$Bandwidth$") && !bandwidth.matches("[0-9]{1,16}"))throw new IOException("invalid_representation_bandwidth");
        String expanded=value.replace("$RepresentationID$",representation).replace("$Bandwidth$",bandwidth);
        expanded=InfinityCastAdaptive.resolve(base,expanded).toASCIIString();
        Matcher matcher=VARIABLE.matcher(expanded);java.util.LinkedHashSet<String> names=new java.util.LinkedHashSet<>();
        while(matcher.find()){if(matcher.group(2)!=null && Integer.parseInt(matcher.group(2))>20)throw new IOException("template_format_limit");names.add(matcher.group(1));}
        if(expanded.replace("$$","").replaceAll(VARIABLE.pattern(),"").contains("$"))throw new IOException("unsupported_dash_template");
        if(names.isEmpty())return resource(URI.create(expanded.replace("$$","$")),InfinityCastAdaptive.Kind.MEDIA);
        String key="template:"+expanded,id=ids.get(key);
        if(id==null) {
            if(closed || resources.size()+templates.size()>=8192)throw new IOException("manifest_resource_limit");
            id=UUID.randomUUID().toString().replace("-","");ids.put(key,id);templates.put(id,new Template(expanded,names.toArray(new String[0])));
        }
        StringBuilder local=new StringBuilder(base()+"/t/"+id);for(String name:names)local.append("/$").append(name).append('$');return local.append("/segment").append(templates.get(id).suffix).toString();
    }
    private Resource resolveRequest(String raw) throws IOException {
        int question=raw.indexOf('?');
        if(question>=0) {
            String query=raw.substring(question+1);
            if(query.length()>256 || !query.matches("(?:_HLS_(?:msn|part)=[0-9]{1,18}|_HLS_skip=(?:YES|v2))(?:&(?:_HLS_(?:msn|part)=[0-9]{1,18}|_HLS_skip=(?:YES|v2))){0,2}"))return null;
            Resource plain=resolveRequest(raw.substring(0,question));if(plain==null)return null;
            if(plain.kind!=InfinityCastAdaptive.Kind.HLS && !(plain==root && "application/vnd.apple.mpegurl".equals(mime)))return null;
            return new Resource(URI.create(plain.uri.toASCIIString()+(plain.uri.getRawQuery()==null?"?":"&")+query),InfinityCastAdaptive.Kind.HLS,"application/vnd.apple.mpegurl");
        }
        if(raw.equals(URI.create(address()).getRawPath()))return root;
        if(!raw.startsWith(path+"/"))return null;
        String rest=raw.substring(path.length()+1);String[] bits=rest.split("/",-1);
        if(bits.length==3 && bits[0].equals("r") && bits[1].matches("[a-f0-9]{32}")) {Resource r=resources.get(bits[1]);return r!=null && bits[2].equals("media"+r.suffix)?r:null;}
        if(bits.length>=3 && bits[0].equals("t")) {
            Template template=templates.get(bits[1]);if(template==null || bits.length!=template.names.length+3 || !bits[bits.length-1].equals("segment"+template.suffix))return null;
            Map<String,String> values=new java.util.HashMap<>();
            for(int i=0;i<template.names.length;i++){if(!bits[i+2].matches("[0-9]{1,18}"))return null;values.put(template.names[i],bits[i+2]);}
            Matcher m=VARIABLE.matcher(template.value);StringBuffer out=new StringBuffer();
            while(m.find()) {
                String number=values.get(m.group(1));if(m.group(2)!=null)number=String.format(Locale.ROOT,"%0"+m.group(2)+"d",Long.parseLong(number));
                m.appendReplacement(out,Matcher.quoteReplacement(number));
            }
            m.appendTail(out);return new Resource(URI.create(out.toString().replace("$$","$")),InfinityCastAdaptive.Kind.MEDIA,null);
        }
        return null;
    }
    private Response open(Resource resource,String method,String range) throws IOException {
        URI target=resource.uri;boolean privateHeaders=sameOrigin(source.uri,target);
        for(int redirects=0;redirects<=5;redirects++) {
            if(closed)throw new IOException("transport_closed");
            Request.Builder request=new Request.Builder().url(target.toASCIIString()).method(method,null)
                .header("Accept-Encoding","identity").header("User-Agent","InfinityCast/1");
            if(privateHeaders)for(Map.Entry<String,String> header:(resource==root || resource.kind==InfinityCastAdaptive.Kind.HLS || resource.kind==InfinityCastAdaptive.Kind.DASH?source.headers:source.streamHeaders).entrySet())request.header(header.getKey(),header.getValue());
            String explicit=privateHeaders?(resource==root || resource.kind==InfinityCastAdaptive.Kind.HLS || resource.kind==InfinityCastAdaptive.Kind.DASH?source.headers:source.streamHeaders).get("cookie"):null;
            String cookie=cookies.header(target,explicit);if(!cookie.isEmpty())request.header("Cookie",cookie);
            if(range!=null)request.header("Range",range);
            Call call=upstream.newCall(request.build());calls.add(call);
            if(closed){call.cancel();calls.remove(call);throw new IOException("transport_closed");}
            Response result;
            try {result=call.execute();}catch(IOException | RuntimeException failed){call.cancel();calls.remove(call);throw new IOException("source_connection_failure");}
            if(closed){result.close();calls.remove(call);throw new IOException("transport_closed");}
            int code=result.code();
            if(code==301 || code==302 || code==303 || code==307 || code==308) {
                String location=result.header("Location");result.close();calls.remove(call);
                if(location==null || redirects==5)throw new IOException("source_redirect_limit");
                URI next=InfinityCastAdaptive.resolve(target,location);if(!sameOrigin(target,next))privateHeaders=false;target=next;continue;
            }
            responses.put(result,call);return result;
        }
        throw new IOException("source_redirect_limit");
    }
    private void release(Response response) {try{response.close();}finally{Call call=responses.remove(response);if(call!=null)calls.remove(call);}}
    private static byte[] read(InputStream input,int limit) throws IOException {
        ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] buffer=new byte[8192];int count;
        while((count=input.read(buffer,0,Math.min(buffer.length,limit+1-out.size())))!=-1){out.write(buffer,0,count);if(out.size()>limit)throw new IOException("manifest_size_limit");}
        return out.toByteArray();
    }
    private String probe() throws IOException {
        Response response=open(root,"HEAD",null);String type=null;
        try {
            if(response.code()==200 || response.code()==206)type=InfinityCastSource.mime(response.header("Content-Type"),source.hint);
            // A method-bound signed source may reject HEAD yet permit GET.
            // Only the actual bounded GET response may reject that source.
            if(type!=null && !InfinityCastAdaptive.adaptive(type))return type;
        } finally {release(response);}
        response=open(root,"GET",null);
        try {
            if(response.code()!=200 || response.body()==null)throw new IOException("source_http_"+response.code());
            InputStream input=response.body().byteStream();byte[] prefix=new byte[8192];int used=0,count;
            while(used<prefix.length && (count=input.read(prefix,used,prefix.length-used))!=-1){used+=count;if(used>=512)break;}
            byte[] sample=java.util.Arrays.copyOf(prefix,used);type=InfinityCastSource.sniff(sample,response.header("Content-Type"),source.hint);
            if(InfinityCastAdaptive.adaptive(type)) {
                ByteArrayOutputStream all=new ByteArrayOutputStream();all.write(sample);all.write(read(input,InfinityCastAdaptive.LIMIT-used));
                InfinityCastAdaptive.rewrite(all.toByteArray(),type,response.request().url().uri(),this);
                if("application/vnd.apple.mpegurl".equals(type)) {
                    String playlist=new String(all.toByteArray(),StandardCharsets.UTF_8);hlsSeparateAudio=playlist.contains("TYPE=AUDIO");
                    hlsFmp4=playlist.contains("#EXT-X-MAP:");URI variant=InfinityCastAdaptive.firstVariant(all.toByteArray(),response.request().url().uri());
                    if(variant!=null) {
                        Response media=open(new Resource(variant,InfinityCastAdaptive.Kind.HLS,"application/vnd.apple.mpegurl"),"GET",null);
                        try {
                            if(media.code()!=200 || media.body()==null)throw new IOException("source_http_"+media.code());
                            byte[] body=read(media.body().byteStream(),InfinityCastAdaptive.LIMIT);
                            InfinityCastAdaptive.rewrite(body,type,media.request().url().uri(),this);
                            hlsFmp4=new String(body,StandardCharsets.UTF_8).contains("#EXT-X-MAP:");
                        } finally{release(media);}
                    }
                }
            }
            return type;
        } finally {release(response);}
    }
    private void accept() {
        try {
            while(!closed) {
                Socket client=listener.accept();
                if(closed || !receiver.equals(client.getInetAddress())){client.close();continue;}
                clients.add(client);if(closed){clients.remove(client);client.close();continue;}
                jobs.incrementAndGet();
                try {io.execute(()->{try{serve(client);}finally{clients.remove(client);try{client.close();}catch(IOException ignored){}jobs.decrementAndGet();retired();}});}
                catch(RuntimeException busy){jobs.decrementAndGet();clients.remove(client);client.close();}
            }
        } catch(IOException stopped){}finally{close();cancelCalls();ownerDone=true;retired();}
    }
    private void serve(Socket client) {
        Response response=null;
        try {
            long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(2);client.setSoTimeout(2000);
            InputStream input=client.getInputStream();ByteArrayOutputStream header=new ByteArrayOutputStream();int value,tail=0;
            while(header.size()<8192){long remaining=deadline-System.nanoTime();if(remaining<=0)return;client.setSoTimeout((int)Math.max(1,TimeUnit.NANOSECONDS.toMillis(remaining)));value=input.read();if(value==-1)break;header.write(value);tail=(tail<<8)|value;if(tail==0x0d0a0d0a)break;}
            if(tail!=0x0d0a0d0a)return;
            String[] lines=header.toString("US-ASCII").split("\r\n"),first=lines[0].split(" ");
            if(first.length!=3 || !(first[2].equals("HTTP/1.1") || first[2].equals("HTTP/1.0")))return;
            Resource resource=resolveRequest(first[1]);if(resource==null)return;
            String method=first[0];OutputStream output=client.getOutputStream();
            if(method.equals("OPTIONS")){reply(output,204,null,0,null);return;}
            if(!(method.equals("GET") || method.equals("HEAD")))return;
            String range=null;for(int i=1;i<lines.length;i++)if(lines[i].toLowerCase(Locale.ROOT).startsWith("range:")) {
                if(range!=null)return;range=lines[i].substring(6).trim();if(!range.matches("bytes=[0-9]{0,16}-[0-9]{0,16}") || range.equals("bytes=-"))return;
            }
            if(requests.incrementAndGet()==1)InfinityCastDiagnostics.event("receiver_access","received",0);
            boolean knownManifest=resource.kind==InfinityCastAdaptive.Kind.HLS || resource.kind==InfinityCastAdaptive.Kind.DASH || (resource==root && InfinityCastAdaptive.adaptive(mime));
            response=open(resource,knownManifest?"GET":method,knownManifest?null:range);
            if(response.code()!=200 && response.code()!=206)throw new IOException("source_http_"+response.code());
            String contentType=response.header("Content-Type"),type=InfinityCastSource.mime(contentType,resource==root?mime:resource.hint);
            if(knownManifest || InfinityCastAdaptive.adaptive(type)) {
                if(response.body()==null || response.code()!=200)throw new IOException("invalid_manifest_response");
                String manifestType=type!=null?type:resource.kind==InfinityCastAdaptive.Kind.DASH?"application/dash+xml":"application/vnd.apple.mpegurl";
                byte[] translated=InfinityCastAdaptive.rewrite(read(response.body().byteStream(),InfinityCastAdaptive.LIMIT),manifestType,response.request().url().uri(),this);
                reply(output,200,manifestType,translated.length,null);if(method.equals("GET"))output.write(translated);return;
            }
            if(type==null) {
                String raw=contentType==null?"":contentType.split(";",2)[0].trim().toLowerCase(Locale.ROOT);
                if(resource==root || raw.contains("html") || raw.contains("xml") || raw.contains("json"))throw new IOException("unsupported_media_response");
                type=resource.kind==InfinityCastAdaptive.Kind.TEXT?"text/plain":resource.kind==InfinityCastAdaptive.Kind.KEY?"application/octet-stream":
                    raw.startsWith("video/") || raw.startsWith("audio/") || raw.equals("text/vtt")?raw:"application/octet-stream";
            }
            if(resource.kind==InfinityCastAdaptive.Kind.KEY && method.equals("GET")) {
                byte[] key=read(response.body().byteStream(),16);if(key.length!=16)throw new IOException("unsupported_hls_key");
                reply(output,200,"application/octet-stream",16,null);output.write(key);return;
            }
            String contentRange=response.header("Content-Range");
            if(response.code()==206 && (contentRange==null || !contentRange.matches("bytes [0-9]{1,16}-[0-9]{1,16}/[0-9]{1,16}")))throw new IOException("invalid_source_range");
            long length=response.body()==null?-1:response.body().contentLength();String declared=response.header("Content-Length");
            if(method.equals("HEAD") && declared!=null && declared.matches("[0-9]{1,16}"))length=Long.parseLong(declared);
            reply(output,response.code(),type,length,contentRange);
            if(method.equals("GET") && response.body()!=null){InputStream body=response.body().byteStream();byte[] buffer=new byte[65536];int count;while(!closed && (count=body.read(buffer))!=-1)output.write(buffer,0,count);}
        } catch(IOException | RuntimeException failure){if(!closed)reason(failure);}
        finally{if(response!=null)release(response);}
    }
    private void reply(OutputStream output,int code,String type,long length,String range) throws IOException {
        String response="HTTP/1.1 "+code+" "+(code==200?"OK":code==206?"Partial Content":code==204?"No Content":"Unavailable")+"\r\n"+
            "Connection: close\r\nCache-Control: no-store\r\nAccess-Control-Allow-Origin: *\r\nAccept-Ranges: bytes\r\n"+
            "Access-Control-Allow-Methods: GET, HEAD, OPTIONS\r\nAccess-Control-Allow-Headers: Range\r\n"+
            "Access-Control-Expose-Headers: Content-Range, Content-Length, Accept-Ranges\r\nAccess-Control-Allow-Private-Network: true\r\n";
        if(type!=null)response+="Content-Type: "+type+"\r\n";if(length>=0)response+="Content-Length: "+length+"\r\n";if(range!=null)response+="Content-Range: "+range+"\r\n";
        output.write((response+"\r\n").getBytes(StandardCharsets.US_ASCII));output.flush();
    }
    private void cancelCalls(){for(Call call:new ArrayList<>(calls))call.cancel();upstream.connectionPool().evictAll();}
    @Override public synchronized void close() {
        if(closed)return;closed=true;try{listener.close();}catch(IOException ignored){}
        for(Socket client:new ArrayList<>(clients))try{client.close();}catch(IOException ignored){}
        // cancel() is nonblocking; do not queue it behind an accept() owner.
        for(Call call:new ArrayList<>(calls))call.cancel();
        try{lifecycle.execute(()->{cancelCalls();ownerDone=true;retired();});}catch(RuntimeException full){/* accept owner still closes and retires */}
    }
    private void retired() {
        if(closed && ownerDone && jobs.get()==0)synchronized(InfinityCastRelay.class){if(active==this){cookies.clear();active=null;InfinityCastDiagnostics.event("relay","retired",0);}}
    }
}
