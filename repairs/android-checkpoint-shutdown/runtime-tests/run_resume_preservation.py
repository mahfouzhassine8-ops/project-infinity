"""Run the original 2103292 behavioral suite against the actual candidate modules."""
import argparse
import json
from pathlib import Path
import sys
import unittest

parser = argparse.ArgumentParser()
parser.add_argument('--runtime', required=True)
arguments = parser.parse_args()
runtime = Path(arguments.runtime).resolve(strict=True)
baseline = Path(__file__).resolve().parents[2] / 'resume-hub-2103292/src/test_resume_hub2.py'
source = baseline.read_text()
source = source.replace("ROOT=Path('/mnt/data/resumehub/work/script.infinity.commandcenter')",
                        'ROOT=Path(' + repr(str(runtime)) + ')')
# The original suite did not need Monitor; the resident checkpoint now defines a
# real Monitor subclass at import. Only add that absent Kodi API double.
source = source.replace('xbmc.log=lambda *a,**k: None',
                        "xbmc.Monitor=type('Monitor', (), {})\nxbmc.log=lambda *a,**k: None")
namespace = {'__name__': 'original_resume_preservation', '__file__': str(baseline)}
exec(compile(source, str(baseline), 'exec'), namespace)
class ResumePreservationTests(namespace['ResumeHub2Tests']):
    """Retain inherited assertions with a checked native-library RPC fixture."""
    def setUp(self):
        super().setUp()
        self.native_playcount = 0
        namespace['conditions']['Library.HasContent(TVShows)'] = True
        original_rpc = namespace['rpc']

        def checked_rpc(payload):
            request = json.loads(payload)
            method = request['method']
            if not method.startswith('VideoLibrary.'):
                return original_rpc(payload)
            namespace['rpc_calls'].append(request)
            if method.startswith('VideoLibrary.Set'):
                self.native_playcount = request['params']['playcount']
                return json.dumps({'result': 'OK'})
            if method == 'VideoLibrary.GetMovieDetails':
                details = {'movieid': 42, 'uniqueid': self.movie['uniqueid'],
                           'playcount': self.native_playcount}
                return json.dumps({'result': {'moviedetails': details}})
            if method == 'VideoLibrary.GetEpisodeDetails':
                details = {'episodeid': 42, 'uniqueid': self.movie['uniqueid'],
                           'playcount': self.native_playcount, 'tvshowid': 7,
                           'showtitle': self.movie['showtitle'],
                           'season': self.movie['season'], 'episode': self.movie['episode']}
                return json.dumps({'result': {'episodedetails': details}})
            if method == 'VideoLibrary.GetTVShowDetails':
                return json.dumps({'result': {'tvshowdetails': {'tvshowid': 7,
                    'title': self.movie['showtitle'], 'uniqueid': {'tmdb': '123'}}}})
            if method == 'VideoLibrary.GetEpisodes':
                return json.dumps({'result': {'episodes': [
                    {'season': 1, 'episode': 2}, {'season': 1, 'episode': 3}],
                    'limits': {'total': 2}}})
            return json.dumps({'error': {'message': 'unexpected fixture RPC'}})

        namespace['xbmc'].executeJSONRPC = checked_rpc


suite = unittest.defaultTestLoader.loadTestsFromTestCase(ResumePreservationTests)
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
