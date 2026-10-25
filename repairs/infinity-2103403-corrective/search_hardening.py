"""Apply bounded Search worker and Android keyboard transition hardening.

Exact input is the currently signed Infinity 2103402 Search module.
Does not change provider contracts, identity, result data, history, Search UI,
or the native request/lease protocol.
"""
from pathlib import Path
import hashlib, sys
EXPECTED = 'fb469b20cea3fd86e7eec454aba7ae25d14472d9ebddea36120841925c170be0'

def replace_once(text, old, new):
    assert text.count(old)==1, (old[:100], text.count(old))
    return text.replace(old, new, 1)

def patch(text):
    assert hashlib.sha256(text.encode()).hexdigest()==EXPECTED, 'Wrong signed Search source'
    text=replace_once(text,
"""class _Cancellation:
    def __init__(self): self.event=threading.Event()
    def iscanceled(self): return self.event.is_set()
    def cancel(self): self.event.set()


def _leased_directory""",
"""class _Cancellation:
    def __init__(self): self.event=threading.Event()
    def iscanceled(self): return self.event.is_set()
    def cancel(self): self.event.set()


class _VisibleCancellation:
    # Check foreground Search dismissal during the real native consumer wait.
    # A cancelled native lease must not be abandoned; _leased_directory waits
    # for the original owned invoker to exit before clearing the cancel token.
    def __init__(self, cancel, progress):
        self.cancel, self.progress = cancel, progress
    def iscanceled(self):
        if self.cancel.iscanceled():
            return True
        if self.progress is not None and self.progress.iscanceled():
            self.cancel.cancel()
            return True
        return False


def _leased_directory""")
    text=replace_once(text,
"""def _provider_result(provider,query,home,cancel):""",
"""def _provider_result(provider,query,home,cancel,progress=None):""")
    text=replace_once(text,
"""            status,answer=_leased_directory(path,home,cancel)""",
"""            status,answer=_leased_directory(path,home,_VisibleCancellation(cancel,progress))""")
    start=text.index('def _bounded_results(ready,query,home,cancel,progress):')
    end=text.index('\n\ndef _publish_result(',start)
    old=text[start:end]
    assert "completed=queue.Queue(maxsize=MAX_ACTIVE_CONSUMERS)" in old
    assert 'worker.join()' in old
    new='''def _bounded_results(ready,query,home,cancel,progress):
    """Single consumer, one worker per native RPC, and no nested provider threads.

    MAX_ACTIVE_CONSUMERS has already been 1; the former extra wrapper thread
    was redundant. Keep the same provider order, native lease and caching.
    The progress cancellation is observed during _leased_directory's wait,
    not just between providers, while its real RPC owner retires normally.
    """
    monitor=xbmc.Monitor()
    try:
        for index,provider in enumerate(ready):
            if monitor.abortRequested() or progress.iscanceled() or cancel.iscanceled():
                cancel.cancel();break
            try:
                result=_provider_result(provider,query,home,cancel,progress)
            except Exception:
                result=(provider,'unavailable',{},'')
            if monitor.abortRequested() or progress.iscanceled() or cancel.iscanceled():
                cancel.cancel();break
            progress.update(int((index+1)*100/max(1,len(ready))),result[0]['name'])
            yield result
    finally:
        cancel.cancel()'''
    text=replace_once(text,old,new)
    text=replace_once(text,
"""        keyboard=xbmc.Keyboard(current,heading,False)
        keyboard.doModal()
        if not keyboard.isConfirmed():return
        try:choice=json.loads(keyboard.getText())
""",
"""        keyboard=xbmc.Keyboard(current,heading,False)
        try:
            keyboard.doModal()
            accepted=keyboard.isConfirmed()
            submitted=keyboard.getText() if accepted else ''
        finally:
            # Release the native IME/dialog owner before validating providers,
            # writing history, or activating a different Kodi window. Retaining
            # this wrapper through ActivateWindow overlapped two GUI lifetimes.
            del keyboard
        if not accepted:return
        try:choice=json.loads(submitted)
""")
    compile(text,'infinity_search.py','exec')
    return text

if __name__=='__main__':
    src=Path(sys.argv[1]);dst=Path(sys.argv[2])
    updated=patch(src.read_text(encoding='utf-8'))
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(updated,encoding='utf-8')
    print('Input Search SHA256',EXPECTED)
    print('New Search SHA256  ',hashlib.sha256(updated.encode()).hexdigest())
