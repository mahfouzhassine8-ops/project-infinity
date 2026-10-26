"""Correct only the original disposable host clip's frame/keyframe format."""
import hashlib
from pathlib import Path
from types import SimpleNamespace


def prepare(selected,args,report,device):
    if args.case not in ('final-continue','final-actions'):return
    from android17_reference_observation import FIXTURE_SHA
    from android17_candidate_probe import require_disposable
    require_disposable(device)
    if hashlib.sha256(Path(selected.__file__).read_bytes()).hexdigest()!=FIXTURE_SHA:
        raise ValueError('Original selected host generator source differs')
    original=selected.subprocess.run
    target=str(args.out/'final-profile/infinity-final-qa.mp4')
    expected=['ffmpeg','-v','error','-f','lavfi','-i','color=c=gray:s=64x64:r=1','-t','180',
              '-an','-c:v','libx264','-pix_fmt','yuv420p',target]
    def run(command,**kwargs):
        if command!=expected:raise ValueError('Unexpected host fixture generator command')
        revised=list(command);revised[6]='color=c=gray:s=64x64:r=24'
        revised[12:12]=['-g','24','-keyint_min','24','-sc_threshold','0']
        value=original(revised,**kwargs)
        report['generated_clip_format']=dict(duration_seconds=180,fps=24,keyframe_interval=24,
            sha256=hashlib.sha256(Path(target).read_bytes()).hexdigest(),
            actual_generated_test_media=True,APK_changed=False,original_seek_assertions_unchanged=True)
        return value
    # Replace only this imported fixture module's reference, never subprocess
    # globally or any Android/provider implementation.
    selected.subprocess=SimpleNamespace(run=run)
