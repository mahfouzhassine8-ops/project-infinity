"""Behavioral checks against actual signed APK sources and scoped transforms."""
import importlib.util
import json
import os
import re
import subprocess
from contextlib import contextmanager, nullcontext
from types import SimpleNamespace
from pathlib import Path
import sys
import tempfile
import unittest
import uuid
import xml.etree.ElementTree as ET

import components96 as c
import native96 as n
from popup_geometry import geometry


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class Targeted(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = c.read_parent(Path(os.environ['INFINITY_2103395_APK']))
        cls.after = c.components(cls.before)

    def test_exact_component_delta_and_rails_preservation(self):
        self.assertEqual(c.ledger(self.before, self.after),
            json.loads((c.HERE / 'MEMBER-DELTA.json').read_text()))
        self.assertFalse(set(self.before) - set(self.after))
        for name, body in self.before.items():
            if name.startswith('script.infinity.rails/'):
                self.assertEqual(self.after[name], body)
        self.assertFalse(any('cobra' in p.lower() for p in c.ledger(self.before, self.after)['changed']))

    def test_actual_resident_registration_reproduces_and_repairs_version_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for leaf in ('persistence_participant.py', 'checkpoint_runtime.py'):
                (root / leaf).write_bytes(self.before[c.CC + '/' + leaf])
            sys.path.insert(0, str(root))
            try:
                load('persistence_participant', root / 'persistence_participant.py')
                baseline = load('checkpoint_baseline96_test', root / 'checkpoint_runtime.py')
                api = {'version': lambda: '0.3.5.25'}
                participant = baseline.ResidentCheckpoint(root, None, None, None, api)
                with self.assertRaisesRegex(baseline.PersistenceError, 'unsupported installed'):
                    participant.register()
                (root / 'checkpoint_runtime.py').write_bytes(self.after[c.CC + '/checkpoint_runtime.py'])
                current = load('checkpoint_candidate96_test', root / 'checkpoint_runtime.py')
                control = root / '.android-checkpoint'
                control.mkdir()
                owner = uuid.uuid4().hex
                (control / 'engine.json').write_text(json.dumps(dict(schema=1, native_api=1,
                    pid=os.getpid(), owner=owner)))
                participant = current.ResidentCheckpoint(root, None, None, None,
                    {'version': lambda: '0.3.5.26'})
                self.assertTrue(participant.register())
                receipt = json.loads((control / 'active.json').read_text())
                self.assertEqual(receipt['status'], 'ACTIVE')
                self.assertEqual(receipt['addon_version'], '0.3.5.26')
                self.assertEqual(receipt['owner'], owner)
                self.assertEqual(receipt['pid'], os.getpid())
            finally:
                sys.path.pop(0)

    def test_same_four_actions_fit_cover_inner_and_rotations(self):
        for pw, ph in ((1080, 2400), (2400, 1080), (2160, 1856), (1856, 2160)):
            g = geometry(1080, 2400, pw, ph)
            self.assertGreater(g['x'], 0)
            self.assertGreater(g['y'], 0)
            self.assertLessEqual(g['x'] + g['width'], 1080)
            self.assertLessEqual(g['y'] + g['height'], 2400)
            self.assertEqual(len(g['buttons']), 4)
            for x, y, w, h in g['buttons']:
                self.assertGreaterEqual(x, 0)
                self.assertGreaterEqual(y, 0)
                self.assertLessEqual(x + w, g['width'])
                self.assertLessEqual(y + h, g['height'])
            poster = g['details']['poster']
            self.assertAlmostEqual((poster[2] * pw / 1080) / (poster[3] * ph / 2400),
                                   2/3, delta=.025)
            self.assertGreater(g['details']['synopsis'][3], 0)
            self.assertLess(g['details']['synopsis'][1] + g['details']['synopsis'][3],
                            g['buttons'][0][1])

    def test_popup_resolves_skin_canvas_and_clears_competing_anchors(self):
        root = ET.fromstring(self.after[c.SKIN + '/unified/InfinityHomeOptionB.xml'])
        card = root.find('.//control[@id="100"]')
        for node in (card, *card.findall('control')):
            self.assertFalse(any(node.find(name) is not None
                for name in ('centerleft', 'centertop', 'right', 'bottom')))
        self.assertEqual([root.find('.//control[@id="%d"]/label' % i).text
            for i in (101, 102, 103, 104)], ['Play', 'Trailer', 'Favorite', 'More Info'])

    def test_option_b_identity_and_action_routes_byte_preserved(self):
        # Only geometry/onInit change; all selected-item/security/action functions
        # are exact original source, including rejected-item limits.
        import ast
        def functions(body):
            tree = ast.parse(body.decode())
            return {node.name: ast.get_source_segment(body.decode(), node)
                for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        a = functions(self.before[c.UI + '/home_option_b.py'])
        b = functions(self.after[c.UI + '/home_option_b.py'])
        for name in a:
            if name not in ('geometry', '_show_verified_hold'):
                self.assertEqual(a[name], b[name], name)

    def test_exact_native_controller_and_ambient_pins(self):
        source = Path(os.environ['INFINITY_2103395_NATIVE'])
        before = {p: (source / p).read_bytes() for p in n.PATHS}
        after = n.patches(before, self.before, self.after)
        _, release, _ = n.old_adapters()
        hashes = {p: c.sha(b) for p, b in self.after.items()}
        for endpoint in ('service.py', 'plugin.py', 'context.py', 'default.py'):
            matches = release.coherence.matching_variants(after[n.CONTRACT].decode(),
                c.CC, c.CC + '/' + endpoint, hashes)
            self.assertEqual(len(matches), 1)
            self.assertEqual(len(matches[0]['pins']), 17)
        self.assertIn(b'provider_path_exceeds_4096', after[n.CONTAINER])
        self.assertIn(b'path.size() > 4096', after[n.CONTAINER])
        self.assertIn(b'libinfinityambient.so', after[n.CONTRACT])
        self.assertIn(b'a876a76abe4faea63046953579899b0b7a67572722c2ed92331e41fcd1475684', after[n.CONTRACT])

    def test_actual_native_classifier_executes_all_seventeen_rejection_pairs(self):
        source = Path(os.environ['INFINITY_2103395_NATIVE'])
        patched = n.patches({p: (source / p).read_bytes() for p in n.PATHS}, self.before, self.after)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = {
                'platform/android/activity/InfinityScriptCheckpointContracts.cpp': patched[n.CONTRACT],
                'platform/android/activity/InfinityAndroidCheckpoint.h': b'#pragma once\n#include <string>\n',
                'utils/Digest.h': b'#pragma once\nnamespace KODI {namespace UTILITY {class CDigest {public: enum class Type{SHA256};};}}\n',
                'Util.h': b'''#pragma once
#include "utils/Digest.h"
#include <map>
#include <string>
namespace Test {inline std::map<std::string,std::string> digests;}
class CUtil {public: static std::string GetFileDigest(const std::string& path,KODI::UTILITY::CDigest::Type){return Test::digests[path];}};
''',
                'filesystem/SpecialProtocol.h': b'''#pragma once
#include <string>
class CSpecialProtocol {public: static std::string TranslatePath(const std::string& path){return path;}};
''',
            }
            for name, body in files.items():
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(body)
            pins = json.loads(self.after[c.UI + '/CONTROLLER-PREIMAGES.json'])
            rows = '\n'.join('Test::digests[base+"%s/%s"]="%s";' % (c.CC, name, pin)
                             for name, pin in pins.items())
            names = ','.join(json.dumps(c.CC + '/' + name) for name in pins)
            ambient_pin = c.sha(self.after[c.SKIN + '/resources/lib/infinity_native_ambient.py'])
            harness = r'''
#include "platform/android/activity/InfinityScriptCheckpointContracts.cpp"
#include <cassert>
#include <cstdlib>
using InfinityAndroidCheckpoint::ClassifyScript;
int main(){
 for(const char* root:{"special://home/addons/","special://xbmc/addons/"}){
  const std::string base=root;
  ROWS
  const auto check=[&](bool valid){
   for(const char* endpoint:{"service.py","plugin.py","context.py","default.py"})
    assert(!ClassifyScript(base+"script.infinity.commandcenter/"+endpoint,"script.infinity.commandcenter").empty()==valid);
  };
  check(true);
  for(const char* leaf:{NAMES}){
   const auto path=base+leaf;const auto original=Test::digests[path];
   Test::digests[path]="changed";check(false);
   Test::digests.erase(path);check(false);
   Test::digests[path]=original;check(true);
  }
  const auto ambient=base+"skin.infinity.diggz/resources/lib/infinity_native_ambient.py";
  Test::digests[ambient]="AMBIENT";
  setenv("KODI_ANDROID_LIBS","/trusted-libs",1);
  const std::string library="/trusted-libs/libinfinityambient.so";
  Test::digests[library]="a876a76abe4faea63046953579899b0b7a67572722c2ed92331e41fcd1475684";
  assert(ClassifyScript(ambient,"")=="nonpersistent:ambient-glass");
  assert(ClassifyScript(ambient,"wrong.addon").empty());
  Test::digests[ambient]="changed";assert(ClassifyScript(ambient,"").empty());
  Test::digests[ambient]="AMBIENT";Test::digests[library]="changed";
  assert(ClassifyScript(ambient,"").empty());
 }
 assert(ClassifyScript("/untrusted/service.py","script.infinity.commandcenter").empty());
}
'''.replace('ROWS', rows).replace('NAMES', names).replace('AMBIENT', ambient_pin)
            (root / 'test.cpp').write_text(harness)
            subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror',
                '-I', str(root), str(root / 'test.cpp'), '-o', str(root / 'test')], check=True)
            subprocess.run([str(root / 'test')], check=True, timeout=10)

    def test_ambient_uses_existing_rail_art_for_all_three_saved_modes(self):
        import ast
        body = self.after[c.CC + '/experience.py'].decode()
        tree = ast.parse(body)
        # Execute the actual module's pure definitions against Kodi boundary
        # adapters, with no provider imports or invented artwork responses.
        tree.body = [x for x in tree.body if not isinstance(x, (ast.Import, ast.ImportFrom))]
        namespace = dict(re=re, time=__import__('time'), nullcontext=nullcontext,
            contextmanager=contextmanager, persistence_scope=nullcontext,
            urlsplit=__import__('urllib.parse', fromlist=['urlsplit']).urlsplit)
        exec(compile(tree, '<actual-experience-source>', 'exec'), namespace)
        for mode in ('off', 'subtle', 'immersive'):
            props = {'Infinity.BootStage': 'ready'}
            home = SimpleNamespace(getProperty=lambda key: props.get(key, ''),
                                   getFocusId=lambda: 9000)
            labels = {'Container(9000).ListItem.Property(section)': 'movies',
                      'Container(8801).ListItem.Art(fanart)': 'special://existing/fanart.jpg'}
            kodi = SimpleNamespace(getInfoLabel=lambda key: labels.get(key, ''),
                getCondVisibility=lambda value: value == 'Control.IsVisible(8801)')
            gui = SimpleNamespace(Window=lambda _: home, getCurrentWindowId=lambda: 10000)
            api = {'xbmc': kodi, 'gui': gui, 'set': lambda k,v: props.__setitem__(k,v),
                   'str': lambda k,d: mode if k == 'ambient_home' else d,
                   'bool': lambda k,d: d, 'read': lambda p,d: d}
            observer = namespace['ExperienceController'](Path('/unused'),
                SimpleNamespace(isPlaying=lambda: False), api)
            observer.boot_restore = True
            observer.last_save = 100
            observer.continue_pending_seek = lambda _: None
            observer.tick(1.0)
            observer.tick(1.6)
            self.assertEqual(props['Infinity.AmbientHome.Mode'], mode)
            self.assertEqual(props['Infinity.AmbientHome.Art'],
                '' if mode == 'off' else 'special://existing/fanart.jpg')

    def test_native_fingerprint_streams_the_actual_636mb_entry_and_rejects_size_mismatches(self):
        import hashlib
        original = (c.HERE.parent/'fold-critical-2103395/InfinityEvidence95.java').read_text()
        corrected = (c.HERE/'InfinityEvidence95.java').read_text()
        old = original[original.index('  static String digest('):original.rindex('\n}')]
        new = corrected[corrected.index('  static String digestExact('):corrected.index('  static byte[] read(')]
        # Match the actual signed 2103395 ZIP member size. Constant-memory
        # synthetic input tests stream completeness without reading user data.
        size = 636425552
        digest = hashlib.sha256()
        block = bytes(1024*1024)
        remaining = size
        while remaining:
            count = min(remaining, len(block))
            digest.update(block[:count])
            remaining -= count
        java = '''import java.io.*;import java.security.*;import java.util.*;
public class EvidenceDigest96Check {
''' + old + '\n' + new + '''
 static final class Zeros extends InputStream {
  long left;Zeros(long size){left=size;}
  public int read(){if(left==0)return -1;left--;return 0;}
  public int read(byte[] bytes,int offset,int length){
   if(left==0)return -1;int n=(int)Math.min(left,length);
   Arrays.fill(bytes,offset,offset+n,(byte)0);left-=n;return n;
  }
 }
 public static void main(String[] args)throws Exception {
  boolean rejected=false;
  try{digest(new Zeros(SIZE),400*1024*1024);}catch(IOException expected){rejected=true;}
  if(!rejected)throw new AssertionError("baseline failure not reproduced");
  if(!digestExact(new Zeros(SIZE),SIZE).equals("HASH"))throw new AssertionError("incomplete fingerprint");
  for(long[] pair:new long[][]{{9,10},{11,10},{0,0},{0,-1}}){
   rejected=false;try{digestExact(new Zeros(pair[0]),pair[1]);}catch(IOException expected){rejected=true;}
   if(!rejected)throw new AssertionError("declared-size mismatch accepted");
  }
 }
}
'''.replace('SIZE', str(size)).replace('HASH', digest.hexdigest())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root/'EvidenceDigest96Check.java'
            source.write_text(java)
            subprocess.run(['javac', '--release', '8', '-d', str(root), str(source)], check=True)
            subprocess.run(['java', '-cp', str(root), 'EvidenceDigest96Check'], check=True, timeout=30)


if __name__ == '__main__':
    unittest.main()
