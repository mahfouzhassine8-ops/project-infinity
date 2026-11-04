"""Read-only observations of signed 453; no Kodi execution or data mutation."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile

EXPECTED_APK = '08ca19e9ff01e3830253980028dbcdbfb36056fd71b06a18cbfb922158ceaac8'
PREFIX = 'assets/addons/skin.infinity.diggz/'


def inspect(apk):
    with apk.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != EXPECTED_APK:
        raise ValueError('Not the preserved signed 2103453 APK')
    members = {}
    with ZipFile(apk) as archive:
        def read(name):
            path = PREFIX + name
            data = archive.read(path)
            members[path] = hashlib.sha256(data).hexdigest()
            return ET.fromstring(data)

        manifest = read('addon.xml')
        window = read('unified/MyVideoNav.xml')
        selector = read('unified/custom_1130_Views.xml')
        settings = read('unified/custom_1131_ViewSettings.xml')
        showcase = read('unified/View_54_ShowCase.xml')
        drawer = read('unified/Custom_1198_InfinityNav.xml')
        declared = [int(x) for x in window.findtext('views').split(',')]
        offered = sorted({int(n.text.split('(')[1].rstrip(')'))
                          for n in selector.iter('onclick')
                          if (n.text or '').startswith('Container.SetViewMode(')})
        dialogs = {}
        for name, node in [('1130', selector), ('1131', settings)]:
            close = next(c for c in node.iter('control') if c.get('id') == '8999')
            dialogs[name] = {k: close.findtext(k) for k in
                             ('left', 'top', 'width', 'height', 'visible', 'onclick')}
        ids = {'1198101', '1198102', '1198103', '1198104', '1198105', '1198301'}
        routes = {c.get('id'): {'label': c.findtext('label'),
                  'actions': [n.text for n in c.findall('onclick')
                              if not (n.text or '').startswith('NotifyAll')]}
                  for c in drawer.iter('control') if c.get('id') in ids}
        return {
            'kind': 'read-only signed-source observations, not application tests',
            'apk_sha256': digest,
            'skin_resolutions': [n.attrib for n in manifest.findall('./extension/res')],
            'video_registered_views': declared,
            'selector_offered_views': offered,
            'view54_defined': any(c.get('id') == '54' for c in showcase.iter('control')),
            'view54_offered': 54 in offered,
            'view54_registered_in_video_window': 54 in declared,
            'nested_close_geometry': dialogs,
            'view_selector_list_width': next(c.findtext('width') for c in selector.iter('control')
                                             if c.get('id') == '9000'),
            'original_drawer_routes': routes,
            'member_sha256': members,
            'media_inspection': 'BLOCKED: original ZIP bytes unavailable',
            'red_light_runtime_causality': 'NOT ESTABLISHED',
            'android_fold_acceptance': 'NOT RUN',
            'production_changes': 0,
        }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apk', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.apk), indent=2, sort_keys=True))
