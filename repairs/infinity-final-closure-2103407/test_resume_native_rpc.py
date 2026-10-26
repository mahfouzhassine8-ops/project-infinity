import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import resume_native_rpc as native


class RemainingDeadlineTests(unittest.TestCase):
    def test_actual_response_after_general10sec_limit_is_still_inside_original20sec_budget(self):
        clock=[0];timeouts=[];guarded=[]
        class Connection:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def sendall(self,data):self.request=json.loads(data)
            def settimeout(self,timeout):timeouts.append(timeout)
            def recv(self,count):
                clock[0]=12
                return json.dumps(dict(id=731,result=dict(files=[dict(resume=dict(position=60,total=180))]))).encode()
        connection=Connection();device=SimpleNamespace(guard=lambda value:guarded.append(value))
        with patch.object(native.time,'monotonic',side_effect=lambda:clock[0]), \
                patch.object(native.socket,'create_connection',return_value=connection) as create:
            actual=native.read(device,'movie',20)
        self.assertEqual(actual['files'][0]['resume']['position'],60)
        self.assertEqual(connection.request['method'],'Files.GetDirectory')
        self.assertEqual(connection.request['params']['properties'],['resume'])
        self.assertEqual(guarded[0][0],'Files.GetDirectory')
        self.assertEqual(timeouts,[20]);self.assertEqual(create.call_args.kwargs['timeout'],20)

    def test_original20sec_total_is_not_extended_and_arbitrary_targets_refused(self):
        device=SimpleNamespace(guard=lambda value:None)
        with patch.object(native.time,'monotonic',return_value=20), \
                patch.object(native.socket,'create_connection') as create:
            with self.assertRaises(TimeoutError):native.read(device,'tv',20)
            create.assert_not_called()
        with self.assertRaises(ValueError):native.read(device,'arbitrary://target',20)


if __name__=='__main__':unittest.main(verbosity=2)
