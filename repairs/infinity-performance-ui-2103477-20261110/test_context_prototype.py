"""Selected diagnostic adapter contracts; no Kodi application is executed."""
import json
import unittest
from context_batch_prototype import LabelReader, SUFFIXES


class SDK:
    def __init__(self, response=None):
        self.calls = []
        self.response = response

    def getInfoLabel(self, label):
        self.calls.append(label)
        return '' if label.endswith('DBID') else 'value:'+label

    def executeJSONRPC(self, raw):
        request = json.loads(raw)
        if self.response is not None:
            return self.response
        return json.dumps(dict(jsonrpc='2.0',id=947,result={k:self.getInfoLabel(k) for k in request['params']['labels']}))


class AdapterContracts(unittest.TestCase):
    def test_exact_strings_and_empty_are_preserved(self):
        sdk=SDK();r=LabelReader(sdk,True,8102)
        for suffix in SUFFIXES:
            name='Container(8102).ListItem.'+suffix
            self.assertEqual(r.getInfoLabel(name),'' if suffix=='DBID' else 'value:'+name)
        self.assertTrue(r.batch_valid)
        self.assertEqual(r.batch_calls,1)
        self.assertEqual(r.direct_calls,0)

    def test_invalid_batch_falls_back(self):
        for response in ['[1]','bad json','{}',json.dumps(dict(jsonrpc='2.0',id=947,result={})),
                         json.dumps(dict(jsonrpc='2.0',id=947,error={'code':1})),
                         json.dumps(dict(jsonrpc='2.0',id=948,result={})),
                         json.dumps(dict(jsonrpc='2.0',id=947,result={'Container(8102).ListItem.DBID':None}))]:
            with self.subTest(response=response):
                sdk=SDK(response);r=LabelReader(sdk,True,8102)
                name='Container(8102).ListItem.DBID'
                self.assertEqual(r.getInfoLabel(name),'')
                self.assertFalse(r.batch_valid)
                self.assertEqual(r.direct_calls,1)

    def test_no_other_control_or_expression_is_intercepted(self):
        for control,name in [(0,'Container(9000).ListItem.DBID'),(8102,'Container(9000).ListItem.DBID'),
                             (8102,'System.ScreenWidth'),(-1,'Container(-1).ListItem.DBID')]:
            sdk=SDK();r=LabelReader(sdk,True,control)
            r.getInfoLabel(name)
            self.assertEqual(r.batch_calls,0)
            self.assertEqual(r.direct_calls,1)

    def test_repeated_home_label_uses_original_call(self):
        sdk=SDK();r=LabelReader(sdk,True,9000);name='Container(9000).ListItem.Property(section)'
        r.getInfoLabel(name);r.getInfoLabel(name)
        self.assertEqual(r.batch_calls,1)
        self.assertEqual(r.direct_calls,1)


if __name__=='__main__':unittest.main()
