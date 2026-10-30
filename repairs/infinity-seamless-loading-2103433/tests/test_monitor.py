"""Real monitor/client integration and upstream native builtin codec; host only."""
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
STAGED=Path(os.environ.get('INFINITY_STAGED','/workspace/cobra-evidence/consolidated434/infinity-stage-v3'))
spec=importlib.util.spec_from_file_location('loading_monitor_actual',ROOT/'overlay/script.infinity.commandcenter/action_loading.py')
loading=importlib.util.module_from_spec(spec);spec.loader.exec_module(loading)

def measure(name,value):
    destination=os.environ.get('INFINITY_HOST_MEASUREMENTS')
    if destination:
        path=Path(destination);path.mkdir(parents=True,exist_ok=True)
        (path/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')

class Window:
    def __init__(self):self.props={};self.writes=[];self.focus=9000
    def getFocusId(self):return self.focus
    def getProperty(self,key):return self.props.get(key,'')
    def setProperty(self,key,value):self.props[key]=value;self.writes.append((key,value))
    def clearProperty(self,key):self.props.pop(key,None);self.writes.append((key,''))

class Platform:
    def __init__(self,decode):
        self.window=Window();self.now=0.;self.commands=[];self.reads=[];self.decode=decode
        self.labels={'Container(9000).CurrentItem':'1','System.ProfileName':'Main, "Fold" α',
          'System.ScreenWidth':'1080','System.ScreenHeight':'2520',
          'Container(9000).ListItem.Property(section)':'movies','Container(9000).ListItem.Property(hubsource)':'infinity',
          'Container(9000).ListItem.Property(Addon.ID)':'plugin.video.infinity.tracked','Container(9000).ListItem.DBID':'42',
          'Container(9000).ListItem.FolderPath':'plugin://PRIVATE-DONT-ANNOUNCE/42',
          'Container(9000).ListItem.FilenameAndPath':'plugin://PRIVATE-DONT-ANNOUNCE/42',
          'Player.Filenameandpath':''}
        self.window.props[loading.PREFIX+'FrameControls.10000']='|9000|9200|'
        self.busy=False;self.dialog=0;self.monitors=0
        platform=self
        class Monitor:
            def __init__(self):platform.monitors+=1
        self.xbmc=types.ModuleType('xbmc');self.xbmc.Monitor=Monitor
        self.xbmc.getInfoLabel=self.info;self.xbmc.getSkinDir=lambda:'skin.infinity.diggz'
        self.xbmc.getCondVisibility=lambda key:self.busy;self.xbmc.executebuiltin=self.execute
        self.gui=types.ModuleType('xbmcgui');self.gui.Window=lambda id:self.window
        self.gui.getCurrentWindowId=lambda:10000;self.gui.getCurrentWindowDialogId=lambda:self.dialog
        self.monitor=None
    def info(self,key):
        self.reads.append(key)
        m=re.fullmatch(r'Window\(Home\).Property\((.*)\)',key)
        return self.window.getProperty(m[1]) if m else self.labels.get(key,'')
    def execute(self,command):
        self.commands.append(command)
        sender,event,raw=self.decode(command)
        if self.monitor:self.monitor.onNotification(sender,'Other.'+event,raw)
    @contextmanager
    def installed(self):
        with mock.patch.dict(sys.modules,{'xbmc':self.xbmc,'xbmcgui':self.gui}),mock.patch.object(loading.time,'monotonic',lambda:self.now),mock.patch.object(loading.threading,'Thread',side_effect=AssertionError('No added worker permitted')):
            self.monitor=loading.make_monitor(self.xbmc,self.gui);self.monitor.tick()
            yield self

class ActualMonitorAndCodecTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='infinity-loading-codec-')
        cls.binary=Path(cls.temp.name)/'split-params'
        source=ROOT/'tests/kodi_split_params.cpp'
        pin=json.loads((ROOT/'tests/KODI-CODEC-SOURCE.json').read_text())
        text=source.read_text();body=text[text.index('void CUtil::SplitParams('):text.index('\nint main()')].strip()+'\n'
        if hashlib.sha256(body.encode()).hexdigest()!=pin['exact_function_sha256']:raise AssertionError('Upstream parser body changed')
        subprocess.run(['g++','-std=c++17','-O2',str(source),'-o',str(cls.binary)],check=True,capture_output=True)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    @classmethod
    def decode(cls,command):
        if not command.startswith('NotifyAll(') or not command.endswith(')'):raise AssertionError(command)
        raw=subprocess.run([str(cls.binary)],input=command[len('NotifyAll('):-1].encode(),stdout=subprocess.PIPE,check=True).stdout
        parts=[]
        while raw:
            size,raw=raw.split(b'\n',1);size=int(size);parts.append(raw[:size].decode());raw=raw[size:]
        if len(parts)!=3:raise AssertionError(parts)
        return parts

    def test_real_client_native_codec_monitor_and_one_completion(self):
        p=Platform(self.decode)
        with p.installed():
            calls=[]
            with loading.preparation('search-prepare:movie'):
                calls.append('actual-operation');p.now=.25;p.monitor.tick()
                self.assertEqual('true',p.window.getProperty(loading.PREFIX+'Active'))
                self.assertEqual('infinity',p.window.getProperty(loading.PREFIX+'Source'))
                writes=len(p.window.writes);p.reads.clear();p.now=.3;p.monitor.tick();self.assertEqual(writes,len(p.window.writes))
                measure('FOREGROUND-MONITOR-OVERHEAD',dict(host_only=True,steady_foreground_label_queries_per_existing_tick=len(p.reads),unchanged_property_writes_per_tick=len(p.window.writes)-writes,new_worker_threads=0,new_timers=0,new_provider_invocations=0,physical_frame_time='NOT_MEASURED'))
            p.now=.4;p.monitor.tick()
            self.assertEqual(['actual-operation'],calls);self.assertEqual(2,len(p.commands));self.assertEqual(1,p.monitors)
            self.assertEqual('false',p.window.getProperty(loading.PREFIX+'Active'));self.assertEqual('false',p.window.getProperty(loading.PREFIX+'Global'))
            for command in p.commands:
                self.assertNotIn('PRIVATE-DONT-ANNOUNCE',command)
                sender,event,raw=self.decode(command);value=json.loads(raw)
                self.assertEqual(loading.SENDER,sender);self.assertEqual(loading.EVENT,event)
                if value['state']=='preparing':self.assertEqual(p.labels['System.ProfileName'],value['owner']['profile'])

    def test_real_exception_fast_and_background_do_not_invent_success(self):
        p=Platform(self.decode)
        with p.installed():
            with loading.preparation('fast-empty'):pass
            p.now=.05;p.monitor.tick();self.assertFalse(any(k==loading.PREFIX+'Active' and v=='true' for k,v in p.window.writes))
            with self.assertRaisesRegex(ValueError,'genuine failure'):
                with loading.preparation('fails'):raise ValueError('genuine failure')
            p.now=.1;p.monitor.tick();self.assertIn('failed',p.monitor.state.retired.values())
            with loading.preparation('widget-directory',background=True):
                p.now=.4;p.monitor.tick();self.assertEqual('false',p.window.getProperty(loading.PREFIX+'Active'));self.assertEqual('true',p.window.getProperty(loading.PREFIX+'Global'))
            p.now=.5;p.monitor.tick();self.assertEqual('false',p.window.getProperty(loading.PREFIX+'Global'))
            p.reads.clear();p.monitor.tick(foreground=False);self.assertEqual([],p.reads)
            measure('BACKGROUND-MONITOR-OVERHEAD',dict(host_only=True,background_label_queries_per_existing_tick=len(p.reads),new_worker_threads=0,new_timers=0))
            count=len(p.commands)
            p.window.props['Infinity.Experience']='Cobra';p.reads.clear()
            with loading.preparation('cobra-no-cue'):pass
            self.assertEqual(count,len(p.commands));self.assertEqual([],p.reads)

    def test_generated_action_payloads_survive_actual_builtin_codec(self):
        p=Platform(self.decode)
        with p.installed():
            tree=ET.parse(STAGED/'members/assets/addons/skin.infinity.diggz/unified/Home.xml')
            commands=[n.text for n in tree.iter('onclick') if 'seamless.loading' in (n.text or '')]
            self.assertGreater(len(commands),20)
            for command in commands:
                command=re.sub(r'\$INFO\[([^\]]*)\]',lambda m:p.info(m[1]),command)
                sender,event,raw=self.decode(command);data=json.loads(raw)
                self.assertIn(data['state'],('action','dispatched'));self.assertEqual(loading.SENDER,sender);self.assertEqual(loading.EVENT,event)
                self.assertEqual(p.monitor.epoch,data['owner']['epoch']);self.assertLess(len(raw),loading.MAX_EVENT_BYTES)
                for key in loading.PUBLIC_IDENTITY:self.assertIn(key,data['owner'])
                self.assertNotIn('PRIVATE-DONT-ANNOUNCE',command)

    def test_original_dispatch_ends_only_its_launch_cue_without_fake_readiness(self):
        p=Platform(self.decode)
        with p.installed():
            owner=loading._context(p.xbmc,p.gui);owner['epoch']=p.monitor.epoch
            begin=dict(state='action',target='d'*64,owner=owner)
            p.monitor.onNotification(loading.SENDER,loading.EVENT,json.dumps(begin));p.now=.25;p.monitor.tick()
            self.assertEqual('true',p.window.getProperty(loading.PREFIX+'Active'))
            p.monitor.onNotification(loading.SENDER,loading.EVENT,json.dumps(dict(begin,state='dispatched')));p.now=.3;p.monitor.tick()
            self.assertIsNone(p.monitor.state.action);self.assertNotIn('ready',p.monitor.state.retired.values())
            with loading.preparation('actual-first-party-preparation'):
                p.now=.6;p.monitor.tick();token=p.monitor.state.action['token']
                p.monitor.onNotification(loading.SENDER,loading.EVENT,json.dumps(dict(begin,state='dispatched')));p.now=.7;p.monitor.tick()
                self.assertEqual(token,p.monitor.state.action['token'])

    def test_same_index_source_or_path_change_and_late_xml_cannot_own_new_tile(self):
        p=Platform(self.decode)
        with p.installed():
            owner=loading._context(p.xbmc,p.gui);owner['epoch']=p.monitor.epoch
            action=dict(state='action',target='d'*64,owner=owner)
            p.monitor.onNotification(loading.SENDER,'Other.'+loading.EVENT,json.dumps(action));p.now=.25;p.monitor.tick()
            self.assertEqual('true',p.window.getProperty(loading.PREFIX+'Active'))
            p.labels['Container(9000).ListItem.FolderPath']='plugin://DIFFERENT-TILE-SAME-INDEX'
            p.now=.3;p.monitor.tick();self.assertEqual('false',p.window.getProperty(loading.PREFIX+'Active'))
            p.labels['Container(9000).ListItem.Property(hubsource)']='trakt'
            p.monitor.onNotification(loading.SENDER,'Other.'+loading.EVENT,json.dumps(action));p.now=.6;p.monitor.tick()
            self.assertIsNone(p.monitor.state.action);self.assertEqual('false',p.window.getProperty(loading.PREFIX+'Global'))

    def test_notification_overflow_filters_and_stale_epoch_clear_only_ui(self):
        p=Platform(self.decode)
        with p.installed():
            owner=loading._context(p.xbmc,p.gui);owner['epoch']=p.monitor.epoch
            action=dict(state='action',target='d'*64,owner=owner);raw=json.dumps(action)
            p.monitor.onNotification('other-addon','Other.'+loading.EVENT,raw);p.monitor.onNotification(loading.SENDER,'unknown',raw)
            p.monitor.onNotification(loading.SENDER,loading.EVENT,'x'*(loading.MAX_EVENT_BYTES+1))
            self.assertEqual(0,len(p.monitor.mailbox))
            for i in range(loading.MAX_EVENTS+1):p.monitor.onNotification(loading.SENDER,'Other.'+loading.EVENT,raw)
            epoch=p.monitor.epoch;p.now=.4;p.monitor.tick()
            self.assertIsNone(p.monitor.state.action);self.assertEqual({},p.monitor.state.jobs);self.assertNotEqual(epoch,p.monitor.epoch)
            p.monitor.onNotification(loading.SENDER,'Other.'+loading.EVENT,raw);p.now=.5;p.monitor.tick();self.assertIsNone(p.monitor.state.action)
            self.assertEqual([],p.commands)

if __name__=='__main__':unittest.main()
