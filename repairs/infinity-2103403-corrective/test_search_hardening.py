"""Host behavior checks for targeted Search cancellation and GUI teardown."""
import ast, hashlib, json, os, pathlib, threading, types, unittest, uuid
from urllib.parse import urlencode

SOURCE=pathlib.Path(os.environ['PATCHED_SEARCH'])
def selected(names,extra=None):
    wanted=set(names)
    tree=ast.parse(SOURCE.read_text(encoding='utf-8'))
    nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in wanted]
    space={'threading':threading,'hashlib':hashlib,'uuid':uuid,'json':json,'urlencode':urlencode}
    space.update(extra or {})
    exec(compile(ast.fix_missing_locations(ast.Module(nodes,type_ignores=[])),'infinity_search.py','exec'),space)
    return space
class Home:
    def __init__(self):self.props={};self.cancel_seen=False
    def setProperty(self,k,v):
        self.props[k]=v
        if k.startswith('Infinity.Search.Cancel.'):self.cancel_seen=True
    def getProperty(self,k):
        if k.startswith('Infinity.Search.Result.'):return 'completed'
        return self.props.get(k,'')
    def clearProperty(self,k):self.props.pop(k,None)
class Progress:
    def __init__(self):self.cancelled=False;self.values=[]
    def iscanceled(self):return self.cancelled
    def update(self,*args):self.values.append(args)
class Monitor:
    def abortRequested(self):return False
class Tests(unittest.TestCase):
    def test_sequential_order_and_no_nested_provider_threads(self):
        work=[]
        ns=selected(['_Cancellation','_bounded_results'],dict(xbmc=types.SimpleNamespace(Monitor=Monitor)))
        def fake(provider,query,home,cancel,progress):
            work.append((provider['id'],len(threading.enumerate())))
            return provider,'completed',{'result':{'files':[]}},'plugin://'
        ns['_provider_result']=fake
        ready=[dict(id=str(i),name='provider'+str(i)) for i in range(4)]
        progress=Progress()
        got=list(ns['_bounded_results'](ready,'rezero',Home(),ns['_Cancellation'](),progress))
        self.assertEqual([row[0]['id'] for row in got],['0','1','2','3'])
        self.assertEqual(len(work),4)
        self.assertEqual(len(progress.values),4)
        self.assertNotIn('InfinitySearchProvider',SOURCE.read_text())
    def test_progress_cancel_before_next_provider(self):
        progress=Progress()
        ns=selected(['_Cancellation','_bounded_results'],dict(xbmc=types.SimpleNamespace(Monitor=Monitor)))
        called=[]
        def first(provider,query,home,cancel,shown):
            called.append(provider['id']);progress.cancelled=True
            return provider,'completed',{},''
        ns['_provider_result']=first
        ready=[dict(id='a',name='A'),dict(id='b',name='B')]
        cancel=ns['_Cancellation']()
        self.assertEqual(list(ns['_bounded_results'](ready,'q',Home(),cancel,progress)),[])
        self.assertEqual(called,['a'])
        self.assertTrue(cancel.iscanceled())
    def test_progress_cancel_while_native_rpc_waits(self):
        import time
        home=Home(); progress=Progress(); entered=threading.Event()
        def rpc(method,params):
            entered.set()
            while not home.cancel_seen:time.sleep(0.003)
            return {'error':{'message':'cancelled'}}
        ns=selected(['_Cancellation','_VisibleCancellation','_leased_directory'],
           dict(xbmc=types.SimpleNamespace(Monitor=Monitor),rpc=rpc,PROPERTIES=[],
                MAX_RESULTS=40))
        cancel=ns['_Cancellation']()
        def stop():
            assert entered.wait(2)
            progress.cancelled=True
        t=threading.Thread(target=stop);t.start()
        status,answer=ns['_leased_directory']('plugin://plugin.video.seren/?a=1',home,
            ns['_VisibleCancellation'](cancel,progress))
        t.join(2)
        self.assertTrue(home.cancel_seen)
        self.assertTrue(cancel.iscanceled())
        self.assertEqual(home.props,{})
        self.assertEqual(answer['error']['message'],'cancelled')
        self.assertEqual(status,'completed')  # Native status is final, not faked.
    def test_ime_wrapper_destroyed_before_history_and_window_transition(self):
        events=[]
        class Keyboard:
            def __init__(self,current,heading,hidden):
                self.token=json.loads(heading.split(':',1)[1])['token']
            def doModal(self):events.append('modal')
            def isConfirmed(self):return True
            def getText(self):
                return json.dumps(dict(token=self.token,query='re:zero',provider='all'))
            def __del__(self):events.append('keyboard_released')
        class Window:
            def getProperty(self,key):return ''
        class Addon:
            def __init__(self,*a):pass
            def getAddonInfo(self,k):return ''
        fake_xbmc=types.SimpleNamespace(getSkinDir=lambda:'skin.infinity.diggz',
            getInfoLabel=lambda *a:'',Monitor=Monitor,Keyboard=Keyboard,
            executebuiltin=lambda cmd:events.append('activated'),
            getCondVisibility=lambda *a:False)
        def history(*a,**kw):
            events.append('history_written' if kw else 'history_read');return []
        ns=selected(['_open_search'],dict(xbmc=fake_xbmc,xbmcgui=types.SimpleNamespace(Window=lambda _:Window()),
            xbmcaddon=types.SimpleNamespace(Addon=Addon),xbmcvfs=types.SimpleNamespace(translatePath=lambda p:p),
            providers=lambda *a,**kw:([dict(id='plugin.video.seren',name='Seren',contract={})],[]),
            shared_history=history))
        ns['_open_search']('movie')
        self.assertLess(events.index('keyboard_released'),events.index('history_written'))
        self.assertLess(events.index('keyboard_released'),events.index('activated'))
    def test_retains_native_lease_and_provider_contracts(self):
        s=SOURCE.read_text()
        self.assertIn("directory=path+'|infinity_search='+token",s)
        self.assertIn('route(provider,query)',s)
        self.assertIn('if cancel.iscanceled():return provider',s)
        self.assertIn('home.clearProperty(key)',s)
        self.assertIn('MAX_ACTIVE_CONSUMERS=1',s)
if __name__=='__main__':unittest.main(verbosity=2)
