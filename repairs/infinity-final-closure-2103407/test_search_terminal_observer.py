import unittest
from search_terminal_observer import classify


class ActualTerminalTests(unittest.TestCase):
    def test_content_is_distinct_from_graceful_timeout_and_empty_results(self):
        p='plugin.video.umbrella'
        row=lambda label:dict(provider=p,label=label)
        self.assertTrue(classify([row('Umbrella — 22 results'),row('The Matrix')],{p})['content_success'])
        value=classify([row('Umbrella — timeout')],{p})
        self.assertFalse(value['content_success']);self.assertEqual(value['graceful_provider_failures'][0]['status'],'timeout')
        self.assertFalse(classify([row('Umbrella — 0 results')],{p})['content_success'])
        self.assertFalse(classify([row('Umbrella — unavailable')],{p})['content_success'])

    def test_missing_attribution_is_not_a_terminal_and_unknown_busy_cancelled_invalid_fail(self):
        p='plugin.video.umbrella'
        self.assertIsNone(classify([dict(provider=p,label='The Matrix')],{p}))
        for status in ('busy','busy_or_unsupported','cancelled','invalid_result','unknown','41 results'):
            with self.assertRaises(ValueError):classify([dict(provider=p,label='Umbrella — '+status)],{p})
        for rows in ([],[dict(provider='foreign',label='Umbrella — timeout')],
                     [dict(provider=p,label='Umbrella — timeout')]*2):
            with self.assertRaises(ValueError):classify(rows,{p})

    def test_all_requested_providers_are_required(self):
        required={'plugin.video.pov','plugin.video.umbrella','plugin.video.seren'}
        rows=[dict(provider='plugin.video.umbrella',label='Umbrella — timeout')]
        self.assertIsNone(classify(rows,required))
        rows.extend([dict(provider='plugin.video.pov',label='POV — 10 results'),dict(provider='plugin.video.seren',label='Seren — 20 results')])
        value=classify(rows,required)
        self.assertEqual(set(value['providers']),required);self.assertFalse(value['content_success'])


if __name__=='__main__':unittest.main(verbosity=2)
