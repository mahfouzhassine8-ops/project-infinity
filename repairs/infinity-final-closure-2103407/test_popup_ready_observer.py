from types import SimpleNamespace
from unittest import TestCase,main
from unittest.mock import patch
import popup_ready_observer as observer


class PopupReadinessTests(TestCase):
    def test_delayed_native_rows_and_focus_share_original_deadline(self):
        counts=iter([0,3,3]);focused=iter([False,False,True]);samples=[];result={}
        xbmc=SimpleNamespace(getInfoLabel=lambda key:str(next(counts)),getCondVisibility=lambda key:next(focused))
        gui=SimpleNamespace(getCurrentWindowDialogId=lambda:13000,
            Window=lambda ident:SimpleNamespace(getProperty=lambda key:'1'))
        def until(fn,message,seconds):
            self.assertEqual(seconds,81)
            for _ in range(3):
                value=fn();samples.append(result['popup_readiness_observation'])
                if value:return value
            raise RuntimeError('Not ready')
        with patch.object(observer.time,'monotonic',return_value=109):
            value=observer.wait_rows(xbmc,gui,SimpleNamespace(until=until),100,result)
        self.assertEqual(value['count'],3);self.assertEqual(len(samples),3)

    def test_empty_overbound_wrong_popup_and_expired_deadline_refused(self):
        for count,popup in [(0,'1'),(1001,'1'),(3,'')]:
            xbmc=SimpleNamespace(getInfoLabel=lambda key:str(count),getCondVisibility=lambda key:True)
            gui=SimpleNamespace(getCurrentWindowDialogId=lambda:13000,
                Window=lambda ident:SimpleNamespace(getProperty=lambda key:popup))
            def until(fn,message,seconds):
                self.assertIsNone(fn());raise RuntimeError('Original deadline')
            with patch.object(observer.time,'monotonic',return_value=109),self.assertRaises(RuntimeError):
                observer.wait_rows(xbmc,gui,SimpleNamespace(until=until),100,{})
        with patch.object(observer.time,'monotonic',return_value=190),self.assertRaises(AssertionError):
            observer.wait_rows(None,None,None,100,{})


if __name__=='__main__':main(verbosity=2)
