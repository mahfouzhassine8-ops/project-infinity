"""Native timestamp/CPU parser checks, not device performance claims."""
import unittest
import android_frame_samples as frames


class FrameSampleTests(unittest.TestCase):
    def test_actual_column_sentinels_and_fresh_present_edges(self):
        before='16666666\n1 1000000 2\n'
        after='16666666\n1 1000000 2\n2 17000000 3\n3 34000000 4\n4 68000000 5\n4 68000000 5\n0 0 0\n5 9223372036854775807 6\nbad\n'
        value=frames.summarize(before,after)
        self.assertEqual(value['fresh_presentation_count'],3);self.assertEqual(value['median_present_interval_ms'],17)
        self.assertEqual(value['p95_present_interval_ms'],34);self.assertFalse(value['full_action_jank_or_touch_latency_measured'])
        self.assertTrue(value['partial_ring_buffer'])

    def test_no_new_valid_rows_never_become_measurement(self):
        for raw in ('','16666666\n0 0 0\n','2 9223372036854775807 3\n'):
            self.assertEqual(frames.summarize('',raw)['status'],'NOT_OBSERVED')
        self.assertEqual(frames.summarize('1 200 2','1 200 2')['status'],'NOT_OBSERVED')

    def sample(self,user,system,start=8,at=1):
        fields=['S']+['0']*21;fields[11]=str(user);fields[12]=str(system);fields[19]=str(start)
        return dict(proc_stat='123 (name with spaces) '+' '.join(fields),monotonic=at)

    def test_cpu_uses_real_clock_and_rejects_process_replacement_or_missing_evidence(self):
        a=self.sample(100,200);b=self.sample(200,200,at=3)
        self.assertEqual(frames.cpu_interval(a,b,100)['cpu_percent_of_one_core'],50)
        for changed,clock in ((self.sample(200,200,start=9,at=3),100),(self.sample(0,0,at=3),100),(b,None),(b,0),(a,100),({},100)):
            self.assertEqual(frames.cpu_interval(a,changed,clock)['status'],'UNAVAILABLE')


if __name__=='__main__':unittest.main(verbosity=2)
