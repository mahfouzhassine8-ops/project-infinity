from copy import deepcopy
from pathlib import Path
import types
import unittest
import readonly_resume_observer as observer


class ReadonlyObserverTests(unittest.TestCase):
    def source(self):
        return Path('/workspace/scratch/7aaf34f5a62d/signed411-modules/script.infinity.commandcenter/resume_hub.py').read_bytes()

    def test_projection_is_exact_pure_source_and_keeps_original_movie_episode_aliases(self):
        raw=self.source();text,functions=observer.source(raw)
        self.assertFalse(set(functions)&observer.FORBIDDEN)
        scope={};exec(compile(text,'actual-pure-projection','exec'),scope)
        def row(key,media,ids,updated,episode=-1):
            identity={'schema':1,'kind':'movie' if media=='movie' else 'episode',
                'scope':'movie' if media=='movie' else 'show_episode','ids':ids}
            if media=='tv':identity.update(season=1,episode=episode)
            return dict(key=key*64,media=media,identity=identity,updated=updated,season=-1 if media=='movie' else 1,
                        episode=episode,position=60.125,title='Same name is never an ID')
        values=[row('a','movie',{'tmdb':'603','imdb':'tt0133093'},10),row('b','movie',{'imdb':'tt0133093'},20),
                row('c','tv',{'tmdb':'1396'},3,3),row('d','tv',{'tmdb':'1396'},4,2)]
        data=dict(items={v['key']:v for v in values});before=deepcopy(data)
        self.assertEqual([e['key'] for e in scope['entries'](data,'movie')],['b'*64])
        self.assertEqual([e['episode'] for e in scope['entries'](data,'tv')],[2])
        self.assertEqual(scope['entries'](data,'movie')[0]['position'],60.125)
        self.assertEqual(data,before)
        data['resume_hidden']={'a'*64:True,'b'*64:True}
        self.assertFalse(scope['entries'](data,'movie'))

    def test_a_future_io_or_writer_dependency_is_rejected(self):
        raw=self.source()
        for changed in (raw.replace(b"def entries(data, media=",b"def entries(data, media=",1)+
                        b"\n# source fixture append\n",
                        raw.replace(b"    data = _normalize(data)\n    if bucket == 'list':",
                                    b"    save(data)\n    data = _normalize(data)\n    if bucket == 'list':",1),
                        raw.replace(b"    data = _normalize(data)\n    if bucket == 'list':",
                                    b"    Path('/unowned').write_text('bad')\n    data = _normalize(data)\n    if bucket == 'list':",1)):
            if b'save(data)' in changed or b"Path('/unowned')" in changed:
                with self.assertRaises(ValueError):observer.source(changed)
            else:self.assertTrue(observer.source(changed)[1])


if __name__=='__main__':unittest.main(verbosity=2)
