"""Guarded companion update; preserve playback, providers and Resume Hub data."""
from pathlib import Path
import argparse,hashlib,json
from native_controls import once
HERE=Path(__file__).resolve().parent

def repair(root):
    baseline=json.loads((HERE/'controller-baseline.json').read_text())
    for name,digest in baseline['files'].items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
    def change(name,fn):
        p=root/name;p.write_text(fn(p.read_text()))
    change('default.py',lambda s:once(s,
'''        choice = xbmcgui.Dialog().select('Infinity Ambient Home', ['Off', 'Subtle', 'Immersive'],
                                         preselect=modes.index(current) if current in modes else 1)''',
'''        home.setProperty('Infinity.Select.Compact', 'true')
        try:
            choice = xbmcgui.Dialog().select('Infinity Ambient Home', ['Off', 'Subtle', 'Immersive'],
                                             preselect=modes.index(current) if current in modes else 1)
        finally:
            home.clearProperty('Infinity.Select.Compact')'''))
    def common(s):
        return once(s,'''def _skin_resolution_dirs(root: Path):
    wanted = ('16x9','20x9','6x5','portrait','5x6')
    return [root / name for name in wanted if (root / name).is_dir()]''','''def _skin_resolution_dirs(root: Path):
    # The add-on declaration owns active layouts. Do not diagnose or restore
    # inactive historical folders instead of the actual unified mobile skin.
    import xml.etree.ElementTree as ET
    try:
        addon = ET.parse(root / 'addon.xml').getroot()
        wanted = [node.get('folder', '') for node in addon.findall("extension[@point='xbmc.gui.skin']/res")]
        return [root / name for name in dict.fromkeys(wanted)
                if name and not Path(name).is_absolute() and '..' not in Path(name).parts
                and (root / name).is_dir()]
    except (OSError, ET.ParseError):
        return []''')
    change('common.py',common)
    def experience(s):
        start=s.index('        if self.seek_pending:',s.index('    def tick(self, now):'))
        end=s.index('        if ready and not self.boot_restore:',start)
        block=s[start:end]
        s=s[:start]+'        self.continue_pending_seek(now)\n'+s[end:]
        anchor='    def tick(self, now):'
        methods='''    def background_tick(self, now):
        self.clear_art()
        # Completing an already requested resume seek remains essential work.
        self.continue_pending_seek(now)

    def continue_pending_seek(self, now):
'''+block+'\n'
        return once(s,anchor,methods+anchor)
    change('experience.py',experience)
    def service(s):
        s=once(s,'import skin_upgrade','import skin_upgrade\nfrom runtime_visibility import ForegroundGate')
        s=once(s,'    last_guardian = time.monotonic()',
            '    foreground_gate = ForegroundGate(xbmc)\n    suspended_at = None\n    last_guardian = time.monotonic()')
        s=once(s,'''        player.poll()
        stability.tick()
        now = time.monotonic()''','''        player.poll()
        now = time.monotonic()
        if not foreground_gate.visible():
            if suspended_at is None:
                suspended_at = now
            experience.background_tick(now)
            if monitor.waitForAbort(1.0):
                break
            continue
        if suspended_at is not None:
            # Background time must not advance staged widget-startup deadlines.
            stability.started += now - suspended_at
            suspended_at = None
        stability.tick()''')
        return s
    change('service.py',service)
    (root/'runtime_visibility.py').write_text('''# SPDX-License-Identifier: GPL-2.0-or-later
"""Read the existing activity-owned atomic gate, without JNI or a player API."""
class ForegroundGate:
    def __init__(self, xbmc):
        self.android = xbmc.getCondVisibility('System.Platform.Android')
        self.allowed = None
        if self.android:
            try:
                import ctypes
                self.library = ctypes.CDLL('libinfinityambient.so')
                self.allowed = self.library.infinity_ambient_allowed
                self.allowed.restype = ctypes.c_int
            except (OSError, AttributeError):
                pass
    def visible(self):
        if not self.android:
            return True
        return self.allowed is not None and self.allowed() == 1
''')
    change('addon.xml',lambda s:once(s,'version="0.3.5.19"','version="0.3.5.20"'))
    after={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
    changed={n:{'before':baseline['files'].get(n),'after':digest} for n,digest in after.items()
             if baseline['files'].get(n)!=digest}
    assert set(changed)=={'default.py','common.py','experience.py','service.py','runtime_visibility.py','addon.xml'}
    (root.parent/'controller-repair-receipt.json').write_text(json.dumps({'changes':changed,
        'resume_hub_py_unchanged':True,'providers_unchanged':True},indent=2)+'\n')
    print('Controller candidate:',len(changed),'declared changes; Resume Hub implementation unchanged')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);repair(p.parse_args().root)
