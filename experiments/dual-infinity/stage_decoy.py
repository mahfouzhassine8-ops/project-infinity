#!/usr/bin/env python3
"""Stage the G0 Android identity probe; no native build or installable APK merge.

The output is a compile-only Android donor. The verified original JNI class
namespace stays intact; installation ID/components/providers/paths are explicit.
The parent engine/skin/add-on/Health/Cobra payload is never rewritten here.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys
import xml.etree.ElementTree as ET

from source_gate import compiled_manifest, inspect

HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[1]
NAMESPACE = 'com.projectinfinity.kodi'
INSTALL_ID = 'com.projectinfinity.kodi.dualtest'
ANDROID = '{http://schemas.android.com/apk/res/android}'
ET.register_namespace('android', ANDROID[1:-1])


def require(condition, message):
    if not condition:
        raise ValueError(message)


def once(text, old, new):
    require(text.count(old) == 1, 'Unreviewed shell preimage: ' + old[:100])
    return text.replace(old, new, 1)


def manifest(text):
    root = ET.fromstring(text)
    require(ANDROID + 'sharedUserId' not in root.attrib, 'Shared UID is not a safe decoy')
    # AGP 8 owns namespace/applicationId through Gradle, not a source-manifest
    # package attribute. Component classes below are explicitly qualified.
    root.attrib.pop('package', None)
    root.set(ANDROID + 'versionCode', '1')
    root.set(ANDROID + 'versionName', '0.1.0-G0-Identity-Probe')
    app = root.find('application')
    require(app is not None, 'Missing application')
    app.set(ANDROID + 'name', NAMESPACE + '.InfinityDecoyApplication')
    app.set(ANDROID + 'label', 'Infinity Experimental')
    app.set(ANDROID + 'allowBackup', 'false')
    app.set(ANDROID + 'debuggable', 'false')
    # The G0 probe uses app-managed data and content grants, not all-files access.
    excluded = {'android.permission.MANAGE_EXTERNAL_STORAGE',
                'android.permission.WRITE_EXTERNAL_STORAGE',
                'android.permission.RECEIVE_BOOT_COMPLETED'}
    for permission in list(root.findall('uses-permission')):
        if permission.get(ANDROID + 'name') in excluded:
            root.remove(permission)
    for component in list(app):
        if component.tag not in ('activity', 'service', 'receiver', 'provider'):
            continue
        name = component.get(ANDROID + 'name', '')
        if name.startswith('.'):
            name = NAMESPACE + name
        require(name.startswith(NAMESPACE + '.'), 'Unknown component namespace')
        component.set(ANDROID + 'name', name)
        component.set(ANDROID + 'exported', 'false')
        affinity = component.get(ANDROID + 'taskAffinity')
        if affinity:
            require(affinity.startswith(NAMESPACE + '.'), 'Unexpected task affinity')
            component.set(ANDROID + 'taskAffinity', INSTALL_ID + affinity[len(NAMESPACE):])
        authority = component.get(ANDROID + 'authorities')
        if authority:
            require(authority.startswith(NAMESPACE + '.'), 'Unexpected provider authority')
            component.set(ANDROID + 'authorities', INSTALL_ID + authority[len(NAMESPACE):])
        # These components are preserved as compiled classes but never activated
        # for this phone-only Kodi identity probe. Their source stays byte-identical.
        if any(token in name for token in ('InfinityLive', 'Cobra', '.channels.Sync')):
            component.set(ANDROID + 'enabled', 'false')
        for intent_filter in list(component.findall('intent-filter')):
            categories = {x.get(ANDROID + 'name') for x in intent_filter.findall('category')}
            if categories & {'android.intent.category.LAUNCHER',
                             'android.intent.category.LEANBACK_LAUNCHER'}:
                component.remove(intent_filter)
    launcher = ET.SubElement(app, 'activity', {
        ANDROID + 'name': NAMESPACE + '.InfinityDecoyLauncher',
        ANDROID + 'exported': 'true', ANDROID + 'theme': '@style/AppTheme'})
    intent = ET.SubElement(launcher, 'intent-filter')
    ET.SubElement(intent, 'action', {ANDROID + 'name': 'android.intent.action.MAIN'})
    ET.SubElement(intent, 'category', {ANDROID + 'name': 'android.intent.category.LAUNCHER'})
    return ET.tostring(root, encoding='unicode')


def validate_manifest(text, compiled=False):
    root = ET.fromstring(text)
    if compiled:
        require(root.get('package') == INSTALL_ID, 'Wrong compiled installation identity')
    else:
        require(root.get('package') in (None, NAMESPACE), 'Wrong source namespace identity')
    require(ANDROID + 'sharedUserId' not in root.attrib, 'Shared UID prohibited')
    app = root.find('application')
    require(app.get(ANDROID + 'name') == NAMESPACE + '.InfinityDecoyApplication',
            'Owned startup application missing')
    mains = []
    for component in app:
        if component.tag not in ('activity', 'service', 'receiver', 'provider'):
            continue
        name = component.get(ANDROID + 'name', '')
        require(name.startswith(NAMESPACE + '.'), 'JNI class namespace changed')
        if component.get(ANDROID + 'exported') == 'true':
            require(name == NAMESPACE + '.InfinityDecoyLauncher', 'Unexpected exported endpoint')
        authority = component.get(ANDROID + 'authorities')
        if authority:
            require(authority.startswith(INSTALL_ID + '.'), 'Production provider collision')
        affinity = component.get(ANDROID + 'taskAffinity')
        if affinity:
            require(affinity.startswith(INSTALL_ID + '.'), 'Production task collision')
        if name == NAMESPACE + '.Main':
            require(component.get(ANDROID + 'process') == ':kodi', 'Primary native process moved')
            mains.append(component)
    require(len(mains) == 1, 'G0 probe must declare exactly one native engine')
    forbidden = {'android.permission.MANAGE_EXTERNAL_STORAGE',
                 'android.permission.WRITE_EXTERNAL_STORAGE', 'android.permission.RECEIVE_BOOT_COMPLETED'}
    require(not any(p.get(ANDROID + 'name') in forbidden for p in root.findall('uses-permission')),
            'Shared external/boot access is not enabled in G0')


def java_transform(name, text):
    if name == 'Main.java.in':
        anchor = '  @Override\n  public void onCreate(Bundle savedInstanceState)'
        additions = '''  @Override public void startActivity(android.content.Intent request) {
    super.startActivity(InfinityDecoyIdentity.ownIntent(this, request));
  }
  @Override public void startActivity(android.content.Intent request, android.os.Bundle options) {
    super.startActivity(InfinityDecoyIdentity.ownIntent(this, request), options);
  }
  @Override public void startActivityForResult(android.content.Intent request, int code) {
    super.startActivityForResult(InfinityDecoyIdentity.ownIntent(this, request), code);
  }
  @Override public void startActivityForResult(android.content.Intent request, int code, android.os.Bundle options) {
    super.startActivityForResult(InfinityDecoyIdentity.ownIntent(this, request), code, options);
  }

'''
        return once(text, anchor, additions + anchor)
    if name == 'XBMCProperties.java.in':
        return once(text, '  public static void initializeProperties()\n  {',
                    '  public static void initializeProperties()\n  {\n'
                    '    // Decoy Application configured owned paths before any provider/native load.\n'
                    '    if (InfinityDecoyIdentity.INSTALL_ID.equals(BuildConfig.APPLICATION_ID)) {\n'
                    '      if (!"yes".equals(System.getProperty("xbmc.proploaded", "")))\n'
                    '        throw new IllegalStateException("Owned decoy paths not prepared");\n'
                    '      return;\n    }')
    if name == 'content/XBMCContentProvider.java.in':
        return once(text, 'AUTHORITY_ROOT = "@APP_PACKAGE@";',
                    'AUTHORITY_ROOT = "' + INSTALL_ID + '";')
    if name == 'XBMCSearchableActivity.java.in':
        return once(text, 'content://@APP_PACKAGE@.media/search/',
                    'content://' + INSTALL_ID + '.media/search/')
    if name == 'InfinityCloseNativeLease.java.in':
        # Component classes retain their namespace; installation IDs are distinct.
        text = once(text, 'name.equals(getPackageName()+".channels.SyncChannelJobService")',
                    'name.equals(@APP_PACKAGE@.channels.SyncChannelJobService.class.getName())')
        return once(text, 'name.equals(getPackageName()+".channels.SyncProgramsJobService")',
                    'name.equals(@APP_PACKAGE@.channels.SyncProgramsJobService.class.getName())')
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    expected, parent = compiled_manifest('android')
    require(not inspect(expected, args.source), 'Not the complete verified 2103368 Android source')
    require(hashlib.sha256(args.base.read_bytes()).hexdigest() == parent['parent_apk_sha256'],
            'Wrong protected 2103368 APK input')
    require(not args.build.exists(), 'Fresh Android staging directory required')
    sys.path.insert(0, str(REPOSITORY / 'repairs/mobile-regressions-2103304'))
    from packaging_checks import configured, resource_ids
    sdk = Path(os.environ['ANDROID_HOME'])
    tools = sdk / 'build-tools/34.0.0'
    args.output.mkdir(parents=True, exist_ok=True)
    ids = resource_ids(tools / 'aapt2', args.base, args.output / 'parent-resources.txt')
    packaging = args.source / 'tools/android/packaging'
    args.build.mkdir(parents=True)
    for name in ('build.gradle', 'settings.gradle', 'gradle.properties', 'gradlew'):
        shutil.copyfile(packaging / name, args.build / name)
    shutil.copytree(packaging / 'gradle', args.build / 'gradle')
    (args.build / 'gradlew').chmod(0o755)
    app = args.build / 'xbmc'; app.mkdir()
    values = {'APP_PACKAGE': NAMESPACE, 'APP_NAME': 'Kodi', 'APP_NAME_LC': 'kodi',
              'APP_VERSION': '0.1.0-G0-Identity-Probe', 'APP_VERSION_CODE_ANDROID': '1',
              'TARGET_MINSDK': '28', 'TARGET_SDK': '35', 'NDKROOT': str(sdk / 'ndk/unused')}
    manifest_text = manifest(configured(packaging / 'xbmc/AndroidManifest.xml.in', values))
    validate_manifest(manifest_text)
    (app / 'AndroidManifest.xml').write_text(manifest_text)
    gradle = configured(packaging / 'xbmc/build.gradle.in', values)
    gradle = once(gradle, 'applicationId "' + NAMESPACE + '"', 'applicationId "' + INSTALL_ID + '"')
    gradle = once(gradle, 'versionCode 2103302', 'versionCode 1')
    gradle = once(gradle, 'versionName "1.0.9-Chooser-Weather-Snapshot-RC1"',
                  'versionName "0.1.0-G0-Identity-Probe"')
    gradle += '''
android { buildFeatures { buildConfig true }
  testOptions { unitTests.includeAndroidResources = true; unitTests.all { maxHeapSize = "2g" } }
}
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1' }
'''
    gradle += '\nandroid.aaptOptions.additionalParameters "--stable-ids", rootProject.file("stable-ids.txt").absolutePath\n'
    (app / 'build.gradle').write_text(gradle)
    (args.build / 'stable-ids.txt').write_text(''.join(
        INSTALL_ID + ':' + name + ' = ' + rid + '\n' for name, rid in sorted(ids.items())))
    (args.build / 'local.properties').write_text('sdk.dir=' + str(sdk) + '\n')
    delta = {}
    namespace_root = app / 'java' / NAMESPACE.replace('.', '/')
    for origin in (packaging / 'xbmc/src').rglob('*.java.in'):
        name = origin.relative_to(packaging / 'xbmc/src').as_posix()
        original = origin.read_text()
        transformed = java_transform(name, original)
        target = namespace_root / name[:-3]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(transformed.replace('@APP_PACKAGE@', NAMESPACE).replace('@APP_NAME@', 'Kodi')
                          .replace('@APP_NAME_LC@', 'kodi'))
        if transformed != original:
            delta[name] = {'before': hashlib.sha256(original.encode()).hexdigest(),
                           'transformed_template': hashlib.sha256(transformed.encode()).hexdigest()}
    for origin in (HERE / 'android').glob('*.java.in'):
        (namespace_root / origin.name[:-3]).write_text(origin.read_text())
    shutil.copytree(packaging / 'xbmc/res', app / 'res')
    for name, folder in (('strings.xml', 'values'), ('colors.xml', 'values'), ('searchable.xml', 'xml')):
        target = app / 'res' / folder / name
        target.parent.mkdir(parents=True, exist_ok=True)
        content = configured(packaging / 'xbmc' / (name + '.in'), values)
        if name == 'searchable.xml':
            content = content.replace(NAMESPACE + '.media', INSTALL_ID + '.media')
        target.write_text(content)
    copies = {'drawable/applaunch_screen.png': args.source / 'media/applaunch_screen.png',
              'drawable-xxxhdpi/applaunch_screen.png': args.source / 'media/applaunch_screen.png',
              'drawable/ic_recommendation_80dp.png': args.source / 'media/icon80x80.png',
              'drawable-xhdpi/banner.png': packaging / 'media/drawable-xhdpi/banner.png'}
    for density in ('ldpi', 'mdpi', 'hdpi', 'xhdpi', 'xxhdpi', 'xxxhdpi'):
        name = 'drawable-' + density + '/ic_launcher.png'; copies[name] = packaging / 'media' / name
    for name, origin in copies.items():
        target = app / 'res' / name; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origin, target)
    tests = app / 'src/test/java' / NAMESPACE.replace('.', '/')
    tests.mkdir(parents=True)
    shutil.copyfile(HERE / 'android/DecoyIdentityTest.java', tests / 'DecoyIdentityTest.java')
    receipt = {'schema': 1, 'compiled_parent_commit': parent['compiled_parent_commit'],
               'application_id': INSTALL_ID, 'jni_class_namespace': NAMESPACE,
               'android_source_inputs_verified': len(expected), 'android_template_changes': delta,
               'second_engine_enabled': False, 'native_recompiled': False,
               'native_merged': False, 'installable_decoy_created': False,
               'installation_safety_verified': False, 'device_pass': False}
    (args.output / 'DECOY-STAGING.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('G0 compile-only donor staged; verified namespace retained; installation identity separated')


if __name__ == '__main__':
    main()
