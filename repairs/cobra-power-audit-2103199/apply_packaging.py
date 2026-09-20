"""Close only the same-UID background settings bridge to external applications."""
import hashlib
import xml.etree.ElementTree as ET

BASE_MANIFEST_SHA256 = '26c10439e846abcd97804c9abe39c3d8af8337956bf9bdd8e6073f28fcabc7c2'
ANDROID = '{http://schemas.android.com/apk/res/android}'
TARGET = '.InfinityBackgroundControlActivity'


def transform(text: str) -> str:
    if hashlib.sha256(text.encode()).hexdigest() != BASE_MANIFEST_SHA256:
        raise RuntimeError('Background bridge requires the exact 2103198 manifest preimage')
    old = '''            android:name=".InfinityBackgroundControlActivity"
            android:exported="true"'''
    new = old.replace('android:exported="true"', 'android:exported="false"')
    if text.count(old) != 1:
        raise RuntimeError('Background bridge manifest anchor drift')
    after = text.replace(old, new, 1)
    before_tree, after_tree = ET.fromstring(text), ET.fromstring(after)
    before_target = before_tree.find("./application/activity[@%sname='%s']" % (ANDROID, TARGET))
    after_target = after_tree.find("./application/activity[@%sname='%s']" % (ANDROID, TARGET))
    if before_target is None or after_target is None or after_target.get(ANDROID+'exported') != 'false':
        raise RuntimeError('Background bridge was not made private')
    before_target.set(ANDROID+'exported', 'false')
    if ET.tostring(before_tree) != ET.tostring(after_tree):
        raise RuntimeError('Manifest changed outside background bridge export boundary')
    return after


def patch_packager(text: str) -> str:
    marker = '    require(old==new,'
    if text.count(marker) != 1 or 'Private background bridge authorization delta' in text:
        raise RuntimeError('Manifest comparison anchor drift or repeated boundary normalization')
    normalization = '''    # Private background bridge authorization delta: normalize only the
    # named component and retain exact comparison for all other manifest state.
    old_app=[n for n in old['children'] if n['tag']=='application']
    new_app=[n for n in new['children'] if n['tag']=='application']
    require(len(old_app)==1 and len(new_app)==1,'Application manifest inventory drift')
    bridge_name='"com.projectinfinity.kodi.InfinityBackgroundControlActivity" (Raw: "com.projectinfinity.kodi.InfinityBackgroundControlActivity")'
    old_bridge=[n for n in old_app[0]['children'] if n['tag']=='activity' and n['attrs'].get('android:name')==bridge_name]
    new_bridge=[n for n in new_app[0]['children'] if n['tag']=='activity' and n['attrs'].get('android:name')==bridge_name]
    require(len(old_bridge)==1 and len(new_bridge)==1,'Background control component inventory drift')
    require(old_bridge[0]['attrs'].get('android:exported')=='(type 0x12)0xffffffff','Protected bridge export preimage drift')
    require(new_bridge[0]['attrs'].get('android:exported')=='(type 0x12)0x0','Background bridge still allows external applications')
    old_bridge[0]['attrs']['android:exported']='(type 0x12)0x0'
'''
    return text.replace(marker, normalization+marker, 1)
