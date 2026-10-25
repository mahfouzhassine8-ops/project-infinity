"""Infinity 2103407: one native Search RPC owner per Kodi process.

Applies only to reviewed, signed 2103406 Command Center infinity_search.py.
The lock uses a Linux abstract Unix socket: no files or Essential-First writes,
automatically released when its Python holder exits. The actual provider
invoker is still allowed to retire naturally. A saturated Search does not
start a second JSON-RPC worker or forge success.
"""
import hashlib
from pathlib import Path
import sys

ORIGINAL_SHA256='a5640a725d07440e914fd5f8d83a29196ea9cbb1104686f1929b5140040b2c44'


def once(text, before, after):
    assert text.count(before)==1,(repr(before[:120]),text.count(before))
    return text.replace(before,after,1)


def patch(source):
    assert hashlib.sha256(source.encode()).hexdigest()==ORIGINAL_SHA256,'Signed Search source mismatch'
    helper='''def _native_search_admission():
    """One foreground plugin.video RPC across all Python subinterpreters in Kodi.

    An abstract Linux Unix socket provides an atomic cross-interpreter lock
    without a lockfile, profile write, global property race, or external app.
    Its descriptor stays owned until the original JSON-RPC thread exits.
    """
    import errno
    import os
    import socket
    owner = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        owner.bind('\\0infinity-search-native-rpc-v1-' + str(os.getpid()))
    except OSError as failure:
        owner.close()
        if failure.errno == errno.EADDRINUSE:
            return None
        raise RuntimeError('Infinity Search native admission is unavailable') from failure
    return owner


'''
    source=once(source, 'def _leased_directory(path,home,progress=None):\n',helper+'def _leased_directory(path,home,progress=None):\n')
    source=once(source,
'''    token=uuid.uuid4().hex
    keys=['Infinity.Search.'+part+token for part in ('Request.','Cancel.','Result.')]
''',
'''    # The native probe is short-lived and has its own capability token.
    # Actual provider RPCs share ONE capacity slot across Search invokers,
    # including separate Kodi subinterpreters and repeated Search All calls.
    admission = _native_search_admission() if path.startswith('plugin://plugin.video.') else False
    if admission is None:
        return 'busy', {'error': {'message': 'A previous Infinity Search is still active'}}
    token=uuid.uuid4().hex
    keys=['Infinity.Search.'+part+token for part in ('Request.','Cancel.','Result.')]
''')
    source=once(source,
'''    worker=threading.Thread(target=request,name='InfinitySearchResult')
    monitor=xbmc.Monitor()
    try:
''',
'''    worker=threading.Thread(target=request,name='InfinitySearchResult')
    monitor=xbmc.Monitor()
    cancel_sent=False
    try:
''')
    source=once(source,
'''            if monitor.abortRequested() or (progress is not None and progress.iscanceled()):
                home.setProperty(keys[1],'1')
            worker.join(.05)
''',
'''            if not cancel_sent and (monitor.abortRequested() or (progress is not None and progress.iscanceled())):
                home.setProperty(keys[1],'1')
                cancel_sent=True
            worker.join(.05)
''')
    source=once(source,
'''        for key in keys:home.clearProperty(key)


def _provider_result''',
'''        # Always release the capacity slot even if Kodi window cleanup fails.
        try:
            for key in keys:home.clearProperty(key)
        finally:
            if admission:
                admission.close()


def _provider_result''')
    source=once(source,
'''            progress.update(int((index+1)*100/max(1,len(ready))),result[0]['name'])
            yield result
''',
'''            progress.update(int((index+1)*100/max(1,len(ready))),result[0]['name'])
            yield result
            if result[1] == 'busy':
                break  # Never hammer other providers while another Search is working.
''')
    compile(source,'infinity_search.py','exec')
    return source

if __name__=='__main__':
    before=Path(sys.argv[1]).read_text(encoding='utf-8')
    result=patch(before)
    destination=Path(sys.argv[2]);destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists():raise RuntimeError('Refuse to overwrite already staged Search source')
    destination.write_text(result,encoding='utf-8')
    print('BASE_SHA256',ORIGINAL_SHA256)
    print('NEW_SHA256',hashlib.sha256(result.encode()).hexdigest())
