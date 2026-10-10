import importlib.util
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('weather_snapshot',pathlib.Path(__file__).with_name('weather_snapshot.py'))
weather=importlib.util.module_from_spec(spec);spec.loader.exec_module(weather)
class Kodi:
    fetched=True
    values={'Weather.Location':'Configured city','Weather.Temperature':'15°C','Weather.Conditions':'Cloudy','Weather.FanartCode':'28'}
    def getCondVisibility(self,name):assert name=='Weather.IsFetched';return self.fetched
    def getInfoLabel(self,name):return self.values[name]
class Monitor:
    def abortRequested(self):return False
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.target=pathlib.Path(self.tmp.name)/'snapshot.json';self.kodi=Kodi();self.kodi.values=dict(Kodi.values)
    def tearDown(self):self.tmp.cleanup()
    def test_provider_values_and_original_observation_time(self):
        self.assertTrue(weather.publish(self.kodi,str(self.target),Monitor(),1791050000000))
        data=json.loads(self.target.read_text());self.assertEqual(data['source'],'Kodi.Weather');self.assertEqual(data['result'],self.kodi.values);self.assertEqual(data['captured_at_ms'],1791050000000)
    def test_unfetched_weather_cannot_replace_last_reading(self):
        self.target.write_text('old valid reading');self.kodi.fetched=False
        self.assertFalse(weather.publish(self.kodi,str(self.target),Monitor()));self.assertEqual(self.target.read_text(),'old valid reading')
    def test_missing_required_value_preserves_last_reading(self):
        for key in ('Weather.Location','Weather.Temperature','Weather.Conditions'):
            self.kodi.values=dict(Kodi.values);self.kodi.values[key]='';self.target.write_text('previous')
            self.assertFalse(weather.publish(self.kodi,str(self.target),Monitor()));self.assertEqual(self.target.read_text(),'previous')
    def test_na_is_not_a_weather_reading(self):
        self.kodi.values['Weather.Temperature']='N/A';self.assertIsNone(weather.reading(self.kodi,123))
    def test_oversized_values_are_refused(self):
        self.kodi.values['Weather.Location']='x'*513;self.assertIsNone(weather.reading(self.kodi,123))
    def test_abort_prevents_publication(self):
        monitor=Monitor();monitor.abortRequested=lambda:True
        self.assertFalse(weather.publish(self.kodi,str(self.target),monitor));self.assertFalse(self.target.exists())
    def test_atomic_replace_failure_keeps_existing_reading(self):
        self.target.write_text('previous')
        with patch.object(weather.os,'replace',side_effect=OSError('simulated')):self.assertFalse(weather.publish(self.kodi,str(self.target),Monitor()))
        self.assertEqual(self.target.read_text(),'previous')
        self.assertFalse(pathlib.Path(str(self.target)+'.pending').exists())
    def test_checkpoint_system_exit_cleans_pending_namespace(self):
        self.target.write_text('previous')
        with patch.object(weather.os,'replace',side_effect=SystemExit()):
            with self.assertRaises(SystemExit):
                weather.publish(self.kodi,str(self.target),Monitor())
        self.assertEqual(self.target.read_text(),'previous')
        self.assertFalse(pathlib.Path(str(self.target)+'.pending').exists())
    def test_abort_before_commit_keeps_existing_reading(self):
        self.target.write_text('previous');monitor=Monitor();calls=[]
        def aborted():calls.append(1);return len(calls)>=3
        monitor.abortRequested=aborted
        self.assertFalse(weather.publish(self.kodi,str(self.target),monitor));self.assertEqual(self.target.read_text(),'previous');self.assertFalse(pathlib.Path(str(self.target)+'.pending').exists())
    def test_android_json_config_preserves_escaped_filesystem_path(self):
        path=str(pathlib.Path(self.tmp.name)/'weather snapshot.json')
        android_json=json.dumps({'snapshot_file':path}).replace('/', '\\/')
        self.assertEqual(json.loads(android_json)['snapshot_file'],path)
    def test_service_exits_on_abort_without_extra_poll(self):
        monitor=Monitor();monitor.waitForAbort=lambda seconds:True;self.kodi.Monitor=lambda:monitor
        with patch.object(weather,'publish') as publish:weather.main(self.kodi,str(self.target));self.assertEqual(publish.call_count,1)
if __name__=='__main__':unittest.main()
