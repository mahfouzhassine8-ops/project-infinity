package com.projectinfinity.kodi;

import android.net.Credentials;
import android.net.LocalServerSocket;
import android.net.LocalSocket;
import android.os.Process;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

/** RAM-only read-only clock channel, restricted to the same app UID/PID.
 * No files, provider credentials, playback URL or arbitrary control commands.
 */
final class InfinityCastChannel implements AutoCloseable {
    final String name,token,fileHash,originHash;
    private final LocalServerSocket server;
    private volatile boolean closed;
    private volatile LocalSocket current;
    private volatile byte[] state="{}\n".getBytes(StandardCharsets.UTF_8);
    private volatile String occurrence="";

    InfinityCastChannel(String token,String fileHash,String originHash) throws Exception {
        if(!token.matches("[a-f0-9]{32}") || !fileHash.matches("[a-f0-9]{64}") ||
            !originHash.matches("[a-f0-9]{64}"))throw new IllegalArgumentException("Cast channel identity");
        this.token=token;this.fileHash=fileHash;this.originHash=originHash;
        name="infinity-cast-"+Process.myPid()+"-"+token;
        server=new LocalServerSocket(name);
        Thread worker=new Thread(this::serve,"InfinityCastClock");worker.setDaemon(true);worker.start();
    }
    void publish(JSONObject value) {
        try { value.put("occurrence",occurrence); } catch(Exception error) { throw new IllegalArgumentException("Cast clock identity"); }
        byte[] next=(value.toString()+"\n").getBytes(StandardCharsets.UTF_8);
        if(next.length>2048)throw new IllegalArgumentException("Cast clock state size");
        state=next;
    }
    boolean acknowledged() { return !occurrence.isEmpty(); }
    private void serve() {
        while(!closed) {
            LocalSocket accepted;
            try { accepted=server.accept(); }
            catch(Exception listenerFailure) { close();break; }
            try(LocalSocket socket=accepted) {
                current=socket;
                Credentials peer=socket.getPeerCredentials();
                if(peer.getUid()!=Process.myUid() || peer.getPid()!=Process.myPid())continue;
                socket.setSoTimeout(300);
                socket.getOutputStream().write(state);
                socket.getOutputStream().flush();
                InputStream input=socket.getInputStream();ByteArrayOutputStream bytes=new ByteArrayOutputStream();
                int ch;
                while(bytes.size()<=512 && (ch=input.read())!=-1 && ch!='\n')bytes.write(ch);
                if(bytes.size()==0 || bytes.size()>512)continue;
                JSONObject ack=new JSONObject(bytes.toString(StandardCharsets.UTF_8.name()));
                String next=ack.optString("occurrence");
                if(token.equals(ack.optString("session")) && fileHash.equals(ack.optString("file_sha256")) &&
                   originHash.equals(ack.optString("origin_sha256")) && next.matches("[a-f0-9]{32}"))
                    if(occurrence.isEmpty() || occurrence.equals(next))occurrence=next;
            } catch(Exception ignored) {
                // Deadline, EOF and a closing listener are normal. No retry
                // thread or sensitive exception/stream logging is created.
            } finally { current=null; }
        }
    }
    @Override public void close() {
        closed=true;
        try { if(current!=null)current.close(); } catch(Exception ignored) {}
        try { server.close(); } catch(Exception ignored) {}
    }
}
