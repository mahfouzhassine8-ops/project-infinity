"""Synthetic parser/admission checks, no ADB or application execution."""
import unittest
import android_metrics as metrics


def frames(*rows):
    return '---PROFILEDATA---\nFlags,IntendedVsync,FrameCompleted\n'+''.join(','.join(map(str,row))+'\n' for row in rows)+'---PROFILEDATA---\n'


class MetricsContracts(unittest.TestCase):
    def test_only_new_completed_hwui_frames_count(self):
        before=frames((0,1000000,9000000))
        after=frames((0,1000000,9000000),(0,20000000,30000000),(0,40000000,60000000))
        result=metrics.hwui_delta(before,after)
        self.assertEqual(result['frame_count'],2)
        self.assertEqual(result['median_frame_duration_ms'],10)
        self.assertEqual(result['p95_frame_duration_ms'],20)
        self.assertFalse(result['native_kodi_gl_fps_measured'])

    def test_distinct_windows_do_not_collapse_same_vsync_timestamp(self):
        before='Window: Owner\n'+frames((0,1000000,9000000))
        after=before+'Window: Infinity Search\n'+frames((0,1000000,11000000))
        result=metrics.hwui_delta(before,after)
        self.assertEqual(result['frame_count'],1)
        self.assertEqual(result['max_frame_duration_ms'],10)

    def test_invalid_flagged_and_pending_frames_are_not_zero_time_passes(self):
        result=metrics.hwui_delta('',frames((1,1,100),(0,0,100),(0,10,9),(0,100,2**63-1)))
        self.assertEqual(result['status'],'NOT_OBSERVED')
        self.assertIsNone(result['p95_frame_duration_ms'])

    def test_stat_fields_name_spaces_and_resource_units(self):
        fields=['R']+['0']*21;fields[11]='200';fields[12]='50';fields[19]='1234';fields[21]='512'
        before=metrics.process_stat('123 (kodi worker) '+' '.join(fields))
        after=dict(before,cpu_ticks=300,rss_pages=1024)
        result=metrics.process_delta(before,after,2,100,4096)
        self.assertEqual(result['cpu_percent_of_one_core'],25)
        self.assertEqual(result['rss_after_bytes'],4194304)
        self.assertEqual(metrics.process_delta(before,dict(after,start_ticks=9),2,100,4096)['status'],'PROCESS_REPLACED')

    def test_unknown_units_and_missing_frames_are_explicit(self):
        value=dict(cpu_ticks=1,start_ticks=2,rss_pages=3)
        result=metrics.process_delta(value,dict(value,cpu_ticks=2),1,None,None)
        self.assertIsNone(result['cpu_percent_of_one_core'])
        self.assertIsNone(result['rss_after_bytes'])
        self.assertEqual(metrics.hwui_delta('no hwui renderer','no hwui renderer')['status'],'NOT_OBSERVED')

    def test_admission_rejects_other_api_and_unselected_physical_device(self):
        class Fake(metrics.Device):
            def __init__(self,sdk,emulator):self.sdk=sdk;self.emulator=emulator
            def adb(self,*parts):return 'device\n'
            def shell(self,*parts):
                if parts==('getprop','ro.build.version.sdk'):return self.sdk
                if parts==('getprop','ro.product.model'):return 'SM-F976U1'
                if parts==('getprop','ro.kernel.qemu'):return self.emulator
                return 'PID NAME\n123 com.projectinfinity.kodi:kodi\n999 other.app\n'
        with self.assertRaises(RuntimeError):Fake('35','1').admit()
        with self.assertRaises(RuntimeError):Fake('37','0').admit()
        result=Fake('37','0').admit(allow_fold=True)
        self.assertEqual(result['processes'],[dict(pid=123,name='com.projectinfinity.kodi:kodi')])


if __name__=='__main__':unittest.main()
