"""Save resumable source/evidence only; never label an unbuilt APK as a candidate."""
import hashlib,json,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];WORK=ROOT.parent;HERE=Path(__file__).resolve().parent
evidence=ROOT/'audit282/local';evidence.mkdir(parents=True,exist_ok=True)
for test in ('test_native.py','test_observer.py'):
    result=subprocess.run(['python3',str(HERE/test),'-v'],cwd=ROOT,capture_output=True,text=True)
    (evidence/(test+'.log')).write_text(result.stdout+result.stderr);assert result.returncode==0
old=WORK/'android-parent/shell-kodi';new=ROOT/'shell-kodi'
before={str(p.relative_to(old)):p for p in old.rglob('*') if p.is_file()}
after={str(p.relative_to(new)):p for p in new.rglob('*') if p.is_file()}
modified=[n for n in before if before[n].read_bytes()!=after[n].read_bytes()]
added=sorted(after.keys()-before.keys())
assert sorted(modified)==sorted(['cmake/scripts/android/Install.cmake','tools/android/packaging/xbmc/build.gradle.in','tools/android/packaging/xbmc/src/Main.java.in'])
assert added==['tools/android/packaging/xbmc/src/InfinityKodiAmbientGate.java.in']
assert not before.keys()-after.keys()
report={'status':'LOCAL SOURCE CHECKPOINT — ANDROID BUILD BLOCKED PENDING GITHUB PUSH APPROVAL','apk_parent':2103281,'apk_parent_sha256':'4c119343d623be5c15233e7b1ed7fa82e3d1f92c3a5ec56f7d3f85b0707cbfe5','skin_parent':'1.0.5.173','skin_parent_sha256':'e70cbcc974dbb646c4061432ce458d513911108aad943cddcc663dc7b937b98e','parent_lock_commit':'bf9e70d68f696fae156c9f33dedf1224c37d7137','planned_apk_version':2103282,'planned_skin_version':'1.0.5.175','local_tests_passed':{'native_rendering':14,'observer_lifecycle_simulated_kodi':16,'inherited_experience':46},'android_modified_files':modified,'android_added_files':added,'unchanged_android_source_files':len(before)-len(modified),'android_compilation':False,'permanent_signing':False,'update_over_install':False,'actual_kodi_rendering_tested':False,'physical_fold_verified':False,'locked':False,'github_branch_push':'blocked; not retried','candidate_branch':'candidate-infinity-native-video-ambient-from-2103281','repository':'mahfouzhassine8-ops/project-infinity','next_action':'Obtain explicit approval to push this candidate branch and run existing permanent-signing CI; do not alter locked parent.'}
(evidence/'CHECKPOINT.json').write_text(json.dumps(report,indent=2)+'\n')
note='''INFINITY LIVE VIDEO AMBIENT — LOCAL CHECKPOINT, NOT AN INSTALLABLE RELEASE

The user explicitly authorized 2103281 as Android parent. Locked .173 remains
the skin source. .174 was only reference; .172 was not used as the source.

76 local tests pass: 14 native directional-rendering checks, 16 observer lifecycle
tests with simulated Kodi APIs, 46 inherited Infinity Experience tests. All old
skin control trees/actions are preserved. 1,366 skin files are byte-identical.
No actual Kodi rendering or physical Fold acceptance has happened.

GitHub push was stopped by workspace safety review because explicit approval to
send the newly created source/workflow to this repository is required. No push
was retried. No Android compilation/signing/CI/update test happened. There is no
new signed APK, no completed release, and no new lock.

To resume: authorize pushing candidate-infinity-native-video-ambient-from-2103281
to mahfouzhassine8-ops/project-infinity and running its candidate workflow with
the existing configured permanent-signing identity. Keep lock/main unchanged.

Architecture: one presentation-only native kernel observes Kodi RenderCapture;
skin-owned RAM-backed light textures are placed on existing Home glass and dock
below text/icons. Off/Subtle and all player/provider actions remain unchanged.
No second decoder/player or new add-on is introduced. Native Kodi/Cobra source
is not modified. Original Cobra field arithmetic is adapted at the rendering
boundary (edge sampling, 56/44 smoothing, saturation, premultiplied blur).

Still required: compile/sign; inherited Android/Cobra regression and protected
render comparison; update-over-install; actual Kodi RAM texture loading;
comparison with accepted Cobra on the real Fold; viewport/crop correctness;
all real window/fold/fullscreen lifecycles; long-run performance; user acceptance.
Dynamic list-item materials are not individually injected; static Home/nav glass
and playback dock are the current integration targets and need visual review.
Do not label sampler success or the synthetic image as a product/device pass.

No secrets, user accounts, credentials, or provider data are included.
Parent APK and .173 ZIP remain unchanged and available as rollback references.
'''
(evidence/'READ-FIRST.txt').write_text(note)
dest=WORK/'Infinity-2103281-Ambient-LOCAL-CHECKPOINT.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    z.write(evidence/'READ-FIRST.txt','READ-FIRST.txt')
    for p in HERE.iterdir():
        if p.is_file():z.write(p,'source/'+p.name)
    z.write(ROOT/'.github/workflows/infinity-native-ambient-2103282.yml','source/infinity-native-ambient-2103282.yml')
    for p in (ROOT/'audit282').rglob('*'):
        if p.is_file():z.write(p,'evidence/'+str(p.relative_to(ROOT/'audit282')))
    for p in ('skin-preservation.json',):z.write(WORK/'candidate'/p,'evidence/'+p)
    for n in modified+added:z.write(after[n],'android-forward/'+n)
    z.write(WORK/'evidence281/reconstructed-2103281-shell.tar.gz','parent/reconstructed-2103281-shell.tar.gz')
    # Delta only, not a standalone skin ZIP that might be installed without APK.
    with zipfile.ZipFile(WORK/'candidate/Infinity-Mobile-1.0.5.175-Native-Video-Ambient-RC1.zip') as skin:
        changes=json.loads((WORK/'candidate/skin-preservation.json').read_text())
        for n in changes['modified_files']+changes['added_files']:z.writestr('skin-forward-delta/'+n,skin.read(n))
print(json.dumps({'checkpoint':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'bytes':dest.stat().st_size,'local_tests':76,'unmodified_android_source_files':report['unchanged_android_source_files']},indent=2))
