"""Cancel stopped local ingest and retain segment ownership on its ingest thread."""
from apply_timeshift import once, edit_method


def transform(text):
    text = once(text,
        'private final okhttp3.OkHttpClient providerClient;private volatile int providerHttpCode',
        'private final okhttp3.OkHttpClient providerClient;private volatile okhttp3.Call activeProviderCall;private volatile int providerHttpCode',
        'publish cancellable provider call')
    old = '    void stop(){stopped=true;state="STOPPED";readyLatch.countDown();synchronized(liveLock){try{if(liveSocket!=null)liveSocket.close();}catch(Exception ignored){}liveSocket=null;liveOut=null;liveQueue.clear();}Thread writer=liveWriterThread;if(writer!=null)writer.interrupt();try{if(server!=null)server.close();}catch(Exception ignored){}try{finishSegment(false);}catch(Exception ignored){}if(ingestThread!=null)ingestThread.interrupt();if(serverThread!=null)serverThread.interrupt();Thread cleanup=new Thread(()->{try{Thread.sleep(900);}catch(InterruptedException ignored){}delete(directory);},"CobraTimeshiftCleanup");cleanup.setDaemon(true);cleanup.start();}'
    new = '''    void stop(){
      synchronized(lock){if(stopped)return;stopped=true;state="STOPPED";}
      readyLatch.countDown();
      okhttp3.Call call=activeProviderCall;if(call!=null)call.cancel();
      synchronized(liveLock){try{if(liveSocket!=null)liveSocket.close();}catch(Exception ignored){}liveSocket=null;liveOut=null;liveQueue.clear();}
      Thread writer=liveWriterThread;if(writer!=null)writer.interrupt();
      try{if(server!=null)server.close();}catch(Exception ignored){}
      final Thread owner=ingestThread;if(owner!=null)owner.interrupt();if(serverThread!=null)serverThread.interrupt();
      // The ingest owner closes its segment before the cleanup worker removes files.
      Thread cleanup=new Thread(()->{try{if(owner!=null)owner.join();}catch(InterruptedException interrupted){Thread.currentThread().interrupt();return;}delete(directory);},"CobraTimeshiftCleanup");
      cleanup.setDaemon(true);cleanup.start();
    }'''
    text = once(text, old, new, 'stop cancels ingest without racing segment writer')
    text = edit_method(text, 'ingestLoop',
        'while(!stopped){okhttp3.Response response=null;try{',
        'while(!stopped){okhttp3.Call call=null;okhttp3.Response response=null;try{')
    text = edit_method(text, 'ingestLoop',
        'response=providerClient.newCall(request.build()).execute();',
        'call=providerClient.newCall(request.build());activeProviderCall=call;if(stopped){call.cancel();break;}response=call.execute();if(stopped)break;')
    text = edit_method(text, 'ingestLoop',
        'everConnected=true;state="RECORDING";',
        'everConnected=true;synchronized(lock){if(!stopped)state="RECORDING";}')
    text = edit_method(text, 'ingestLoop',
        'reconnects++;state="RECONNECTING";',
        'reconnects++;synchronized(lock){if(!stopped)state="RECONNECTING";}')
    text = edit_method(text, 'ingestLoop',
        'finally{if(response!=null)response.close();}',
        'finally{if(response!=null)response.close();if(activeProviderCall==call)activeProviderCall=null;}')
    text = edit_method(text, 'finishSegment',
        'if(!ready&&CobraTimeshiftTransportPolicy.startupReady(windowDurationMs())){ready=true;readyElapsed=android.os.SystemClock.elapsedRealtime();state="READY";readyLatch.countDown();}else if(ready)state="READY";',
        'if(!ready&&CobraTimeshiftTransportPolicy.startupReady(windowDurationMs())){synchronized(lock){if(!stopped){ready=true;readyElapsed=android.os.SystemClock.elapsedRealtime();state="READY";readyLatch.countDown();}}}else if(ready){synchronized(lock){if(!stopped)state="READY";}}')
    return text
