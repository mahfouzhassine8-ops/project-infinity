"""Only the corrected Search outcome contract; no application or build suite."""
import importlib.util
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('android_acceptance', HERE/'verify_three_android.py')
subject = importlib.util.module_from_spec(spec);spec.loader.exec_module(subject)


def snapshot(umbrella=0, pov=2):
    rows = []
    for aid, name, count in (('plugin.video.umbrella', 'Umbrella', umbrella), ('plugin.video.pov', 'POV', pov)):
        rows.append(dict(index=len(rows), provider=aid, label=name+' — '+str(count)+' results', file='plugin://'+aid+'/?search=Re%3Azero'))
        for i in range(count):
            rows.append(dict(index=len(rows), provider=aid, label='Native result '+str(i), file='plugin://'+aid+'/?native='+str(i)))
    return dict(window=10025, dialog=9999, labels={'Container.FolderPath':'plugin://script.infinity.commandcenter/?action=search-all&media=tv&query=Re%3Azero'}, rows=rows)


class OutcomeContract(unittest.TestCase):
    def test_successful_results(self):
        value = subject.completed_search(snapshot(2, 3), 'tv', 'Re:zero')
        self.assertEqual({v['status'] for v in value[3].values()}, {'PASS_WITH_RESULTS'})

    def test_successful_empty_is_valid_and_independent_of_other_catalog(self):
        value = subject.completed_search(snapshot(0, 2), 'tv', 'Re:zero')
        self.assertEqual(value[3]['plugin.video.umbrella']['status'], 'PASS_SUCCESSFUL_EMPTY')
        self.assertEqual(value[3]['plugin.video.pov']['status'], 'PASS_WITH_RESULTS')
        self.assertIsNotNone(subject.completed_search(snapshot(0, 0), 'tv', 'Re:zero'))

    def test_actual_provider_timeout_and_error_are_never_empty_success(self):
        for reason in ('timeout', 'failed', 'busy', 'State changed; search again'):
            value = snapshot();value['rows'][0]['label'] = 'Umbrella — '+reason
            with self.assertRaises(subject.ProviderResponseFailure) as caught:
                subject.completed_search(value, 'tv', 'Re:zero')
            self.assertEqual(caught.exception.outcome, reason)

    def test_unfinished_wrong_query_and_modal_states_do_not_pass(self):
        value = snapshot();value['dialog']=10101
        self.assertIsNone(subject.completed_search(value, 'tv', 'Re:zero'))
        self.assertIsNone(subject.completed_search(snapshot(), 'tv', 'Different query'))
        value = snapshot();value['rows']=value['rows'][:1]
        self.assertIsNone(subject.completed_search(value, 'tv', 'Re:zero'))

    def test_loading_rows_do_not_create_false_results_or_empty_success(self):
        value = snapshot(1, 1);value['rows']=[r for r in value['rows'] if r['label'].startswith(('Umbrella —', 'POV —'))]
        self.assertIsNone(subject.completed_search(value, 'tv', 'Re:zero'))

    def test_live_reads_navigation_and_native_deadlines_preserved(self):
        source=(HERE/'android_qa_extension.py.txt').read_text()
        self.assertIn("xbmc.getInfoLabel('Container(50).ListItem.FileNameAndPath')", source)
        host=(HERE/'verify_three_android.py').read_text()
        self.assertIn('NATIVE_ENGINE_DIED_OR_RESTARTED', (HERE.parents[1]/'repairs/infinity-final-release-462-20261107/verify_android_release.py').read_text())
        self.assertIn('actual native TV directory rows after heading',host)
        self.assertIn("device.command('select-row'",host)


if __name__ == '__main__':
    unittest.main()
