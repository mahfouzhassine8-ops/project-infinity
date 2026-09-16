#!/usr/bin/env python3
"""Package Background Controls RC2 using the proven RC1 Android-only packager."""
import package_background_resume as package

package.RELEASE = '1.0.9-Cobra-Background-Controls-RC2'
package.VERSION_CODE = 2103137
ACTION = 'com.projectinfinity.kodi.action.OPEN_BACKGROUND_SETTINGS'


def verify_manifest_pair_rc2(original: str, compiled: str):
    old, new = package.manifest_tree(original), package.manifest_tree(compiled)
    for tree in (old, new):
        for key in ('android:versionCode', 'android:versionName'):
            tree['attrs'].pop(key, None)

    permissions = [n for n in new['children'] if n['tag'] == 'uses-permission' and
                   'android.permission.FOREGROUND_SERVICE_SPECIAL_USE' in n['attrs'].get('android:name', '')]
    package.require(len(permissions) == 1, 'Exactly one background service permission required')
    new['children'].remove(permissions[0])

    app = next(n for n in new['children'] if n['tag'] == 'application')
    services = [n for n in app['children'] if n['tag'] == 'service' and
                'InfinityExtendedBackgroundService' in n['attrs'].get('android:name', '')]
    package.require(len(services) == 1, 'Exactly one background service component required')
    service = services[0]
    package.require(service['attrs'].get('android:exported', '').endswith('0x0'),
                    'Background service must not be exported')
    package.require(service['attrs'].get('android:foregroundServiceType', '').endswith('0x40000000'),
                    'Wrong compiled foreground service type')
    app['children'].remove(service)

    activities = [n for n in app['children'] if n['tag'] == 'activity' and
                  'InfinityBackgroundSettingsActivity' in n['attrs'].get('android:name', '')]
    package.require(len(activities) == 1, 'Exactly one background settings activity required')
    activity = activities[0]
    package.require(not activity['attrs'].get('android:exported', '').endswith('0x0'),
                    'Background settings activity must be exported for the Kodi skin action')
    action_hits = []
    for child in activity['children']:
        if child['tag'] != 'intent-filter':
            continue
        for item in child['children']:
            if item['tag'] == 'action' and ACTION in item['attrs'].get('android:name', ''):
                action_hits.append(item)
    package.require(len(action_hits) == 1, 'Compiled OPEN_BACKGROUND_SETTINGS action missing/duplicated')
    app['children'].remove(activity)

    package.require(old == new,
                    'Compiled manifest drift outside version/background service/settings activity')


package.verify_manifest_pair = verify_manifest_pair_rc2

if __name__ == '__main__':
    package.main()
