"""Reuse frozen synthetic resume data before a fresh API37 test app launches.

This is test setup, never a runtime writer or a user-profile migration. The
stress driver's nonempty-state and post-run preservation assertions stay intact.
"""
import hashlib
import json
import subprocess
from pathlib import Path

from android17_reference_observation import OLD, FIXTURE_SHA
from android17_stress import COUNTS

PACKAGE = 'com.projectinfinity.kodi'
PROFILE = '/sdcard/Android/data/' + PACKAGE + '/files/.kodi/userdata'
START = '    def row(key,kind,ids,updated,episode=-1):'
END = "    target=profile/'addon_data/script.infinity.commandcenter/continue-watching.json';"


def retained_state(raw):
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA:
        raise ValueError('Exact frozen final-eight fixture required')
    text = raw.decode()
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError('Frozen fixture boundaries changed')
    clip = [line for line in text.splitlines(True) if line.startswith('    clip=')]
    if len(clip) != 1:
        raise ValueError('Frozen synthetic clip identity changed')
    body = text[text.index(START):text.index(END)]
    scope = {}
    exec(compile('def fixture_state():\n' + clip[0] + body + '    return data\n',
                 'retained-final-eight-fixture', 'exec'), scope)
    return scope['fixture_state']()


def seed(device, args, report, expected):
    if (args.case != 'final-search-all-enter' or expected.get('post_feature') != COUNTS or
            not expected.get('candidate_apk_sha256') or
            report.get('apk_sha256') != expected.get('candidate_apk_sha256')):
        raise ValueError('Only the exact selected candidate Search stress may be seeded')
    if (device.PACKAGE != PACKAGE or device.PROFILE != PROFILE or
            device.shell('getprop', 'ro.kernel.qemu').strip() != '1' or
            device.shell('getprop', 'ro.build.version.sdk').strip() != '37'):
        raise ValueError('Fixture refuses physical or non-API37 devices')
    receipt = json.loads((args.out / 'INSTALL-OVER-EVIDENCE.json').read_text())
    if (receipt.get('candidate_sha256') != expected['candidate_apk_sha256'] or
            receipt.get('baseline_launched') is not False or
            receipt.get('test_sentinel_preserved') is not True or
            receipt.get('uninstall_or_data_clear') is not False):
        raise ValueError('Fresh install-over admission missing')
    if device.shell('pidof', PACKAGE, check=False).strip() or device.running_engine():
        raise ValueError('Refuse fixture writes after app launch')
    target = PROFILE + '/addon_data/script.infinity.commandcenter/continue-watching.json'
    # Checked shell exit status rejects existing files, broken links, and
    # transport errors; no empty/read-error value is treated as absence.
    device.shell('test', '!', '-e', target)
    device.shell('test', '!', '-L', target)
    clip_target=PROFILE+'/infinity-final-qa.mp4'
    device.shell('test','!','-e',clip_target);device.shell('test','!','-L',clip_target)
    raw = (OLD / 'tracking/final-eight/android_selected.py').read_bytes()
    state = retained_state(raw)
    poster=None
    if expected.get('measure_cached_poster') is True:
        import cached_poster_observer
        poster=cached_poster_observer.stage(device,args,state)
    local = args.out / 'prelaunch-stress-tracking-fixture.json'
    with local.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(state, sort_keys=True) + '\n')
    device.shell('mkdir', '-p', str(Path(target).parent))
    device.adb('push', local, target)
    if device.shell('cat', target) != local.read_text():
        raise RuntimeError('Prelaunch fixture readback differs')
    clip=args.out/'prelaunch-resume-fixture.mp4'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=gray:s=64x64:r=1','-t','180',
                    '-an','-c:v','libx264','-pix_fmt','yuv420p',str(clip)],check=True)
    clip_sha=hashlib.sha256(clip.read_bytes()).hexdigest()
    device.adb('push',clip,clip_target)
    returned=device.adb('shell','cat',clip_target,binary=True)
    if not isinstance(returned,bytes) or hashlib.sha256(returned).hexdigest()!=clip_sha:
        raise RuntimeError('Actual declared resume clip readback differs')
    evidence = dict(source_sha256=FIXTURE_SHA,
                    fixture_sha256=hashlib.sha256(local.read_bytes()).hexdigest(),
                    phase='before first app launch', synthetic_records=len(state['items']),
                    actual_user_data=False, runtime_writer_authority_added=False,
                    existing_profile_replaced=False, readback_matches=True)
    evidence.update(declared_resume_clip_exists=True,declared_resume_clip_sha256=clip_sha,
                    generated_clip_seconds=180,actual_movie_content=False)
    if poster:evidence['actual_cached_poster']=poster
    (args.out / 'STRESS-FIXTURE-SEED.json').write_text(json.dumps(evidence, indent=2) + '\n')
    report['prelaunch_stress_fixture'] = evidence
