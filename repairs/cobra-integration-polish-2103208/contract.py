"""Immutable parent identity and narrowly authorized 208 source/resource scope."""
from pathlib import Path
import hashlib

PARENT_COMMIT = '872dfe64b6710a478e7fd1b6625d1e03a7f9d1cf'
PARENT_RUN = 35623403102
PARENT_APK = 'de2afee4b5e56ee32cb7332f19ac5086b73ffd5c05c14da91eaa477971777eb2'
PARENT_SOURCE = '82546500a4e3b54a0df69ada48c313a7ac4d164798b7d60323e7aa43992b5c95'
CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
OLD = '1.0.9-Cobra-Feature-Refinement-RC1'
NEW = '1.0.9-Cobra-Integration-Polish-RC1'
VERSION = 2103208
RECIPE_PATH = 'repairs/cobra-integration-polish-2103208'
SOURCE_ROOT = 'tools/android/packaging/xbmc/src/'
GRADLE = 'tools/android/packaging/xbmc/build.gradle.in'
ACTIVITY = SOURCE_ROOT + 'InfinityLiveActivity.java.in'
ALLOWED_JAVA = {SOURCE_ROOT + name + '.java.in' for name in (
    'InfinityLiveActivity', 'CobraPresentationEffects', 'CobraQuickPeekSession',
    'CobraEmblem', 'InfinityExtendedBackgroundService', 'Splash')}

# The existing resource table is immutable. These named PNG payloads alone may
# change for the explicitly approved unified icon. Slots are verified against
# the parent's AAPT resource report; new resources/XML/IDs are not authorized.
ICON_SLOTS = {}
for density in ('ldpi', 'mdpi', 'hdpi', 'xhdpi', 'xxhdpi', 'xxxhdpi'):
    ICON_SLOTS['tools/android/packaging/media/drawable-' + density + '/ic_launcher.png'] = ('drawable/ic_launcher', density)
for density in ('mdpi', 'hdpi', 'xhdpi', 'xxhdpi', 'xxxhdpi'):
    for name in ('ic_launcher', 'ic_launcher_round'):
        ICON_SLOTS['tools/android/packaging/xbmc/res/mipmap-' + density + '/' + name + '.png'] = ('mipmap/' + name, density)
for name in ('infinity_icon_foreground', 'infinity_icon_monochrome',
             'infinity_splash_icon', 'project_infinity_icon'):
    ICON_SLOTS['tools/android/packaging/xbmc/res/drawable-nodpi/' + name + '.png'] = ('drawable/' + name, 'nodpi')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def require(condition, message):
    if not condition:
        raise RuntimeError(message)
