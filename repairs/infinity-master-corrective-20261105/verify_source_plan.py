"""Source inventory only. Never build, sign or mutate an APK/profile."""
import hashlib
import json
from pathlib import Path
import subprocess
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
APK=Path('/tmp/kodi451-signed-baseline/Infinity-2103451-Combined-Original-Signer.apk')
EXPECTED='d77c31c458c4571212022bea7cea1e76c1d415cd5792b780b3c655fba97c6399'
PREFIX='repairs/infinity-kodi-2103453-ui-navigation/'
EDITED={PREFIX+'navigation.py',PREFIX+'overlay/assets/addons/skin.infinity.diggz/resources/lib/infinity_library_navigation.py',PREFIX+'overlay/assets/addons/skin.infinity.diggz/unified/Custom_1198_InfinityNav.xml',PREFIX+'overlay/assets/addons/skin.infinity.diggz/unified/Includes_InfinityMediaLists.xml'}
ALLOW={
 'assets/addons/script.infinity.commandcenter/'+n for n in ['infinity_search.py','media_view.py','service.py']
}|{
 'assets/addons/skin.infinity.diggz/'+n for n in ['resources/lib/infinity_library_navigation.py','unified/Custom_1198_InfinityNav.xml','unified/Includes.xml','unified/Includes_InfinityMediaLists.xml','unified/Includes_InfinityVideoOptions.xml','unified/MyVideoNav.xml','unified/custom_1136_InfinityVideoViews.xml','unified/custom_1137_InfinityVideoViewSettings.xml','unified/custom_1138_InfinityVideoDisableViews.xml']
}


def digest(raw):return hashlib.sha256(raw).hexdigest()


def main():
    with APK.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==EXPECTED
    changed=set(subprocess.check_output(['git','diff','--name-only','1b655a9e'],cwd=ROOT,text=True).splitlines())
    assert changed<=EDITED|{p for p in changed if p.startswith('repairs/infinity-master-corrective-20261105/')},changed-EDITED
    overlay={}
    for directory in [ROOT/PREFIX/'overlay',HERE/'overlay']:
        for p in directory.rglob('*'):
            if p.is_file():
                n=p.relative_to(directory).as_posix()
                assert n not in overlay,n
                overlay[n]=p
    assert set(overlay)==ALLOW,set(overlay)^ALLOW
    with ZipFile(APK) as z:
        names=set(z.namelist())
        rows=[dict(member=n,source=str(p.relative_to(ROOT)),baseline451_sha256=digest(z.read(n)) if n in names else None,candidate_source_sha256=digest(p.read_bytes())) for n,p in sorted(overlay.items())]
        native={n:digest(z.read(n)) for n in sorted(names) if n.startswith('lib/') and n.endswith('.so')}
        dex={n:digest(z.read(n)) for n in sorted(names) if n.endswith('.dex')}
        protected=[n for n in names if n not in overlay and not n.endswith('/')]
    result=dict(status='SOURCE_PLAN_ONLY_NOT_AN_APK_COMPARISON',release_ready=False,APK_built=False,authenticated_modules_ready=False,
                actual_installed_and_accepted_versions='UNVERIFIED',preservation_reference=2103451,baseline_apk_sha256=EXPECTED,
                overlay_members=rows,protected_baseline_existing_members_outside_overlay=len(protected),native_baseline_hashes=native,DEX_baseline_hashes=dex,
                native_payloads_in_overlay=[],signing_and_metadata_exceptions='NOT_ALLOCATED_OR_FINALIZED',
                source_worktree_edits_outside_authorized_scope=[],
                limitations=['Prior source-only UI overlay is reviewed reference input;454/455 are not physically accepted.',
                            'No candidate APK exists; complete postpackaging member/signature/authentication comparisons are NOT RUN.',
                            'No native/DEX input is replaced; test453 engine is not silently substituted.',
                            'No signing authority, workflow, accepted registry, user data or recovery lock was changed.'])
    (HERE/'PLANNED-MEMBERS.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(source_overlay_members=len(rows),protected_baseline_members=len(protected),native_libraries=len(native),DEX_files=len(dex),release_ready=False),indent=2))


if __name__=='__main__':main()
