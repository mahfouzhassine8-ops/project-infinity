"""Require an actual correct usable saved card, beyond an empty Home/RPC."""
import json
import time
import android_stress_script as dispatch
from continue_card_observer import verify_card


def observe(device,records,media,out=None):
    if media not in ('movie','tv'):raise ValueError('Unknown exact saved-card category')
    key=('b' if media=='movie' else 'd')*64
    expected=records.get('items',{}).get(key)
    if not isinstance(expected,dict) or expected.get('media')!=media:
        raise ValueError('Original nonempty saved movie/episode fixture required')
    rail=8830 if media=='movie' else 8831
    prefix='Container(%d).ListItem.'%rail
    fields=['Property(Infinity.Selection.Snapshot)','PercentPlayed',
            'Property(Infinity.ResumeHub.Watched)','Season','Episode','Label']
    count='Container(%d).NumItems'%rail
    began=time.monotonic()
    dispatch.launch(device,'home-resume-'+media)
    def ready():
        try:dispatch.verify_dispatch(device)
        except ValueError:return None
        visibility='Control.IsVisible(%d)'%rail
        flags=device.rpc('XBMC.GetInfoBooleans',{'booleans':[visibility]})
        if flags.get(visibility) is not True:return None
        labels=device.rpc('XBMC.GetInfoLabels',{'labels':[count]+[prefix+f for f in fields]})
        if labels.get(count)!='1':return None
        raw=labels.get(prefix+fields[0],'')
        if not raw:return None
        capsule=json.loads(raw)
        if capsule.get('key')!=key:return None
        return labels
    labels=device.until(ready,20)
    visible_ms=(time.monotonic()-began)*1000
    poster=None
    if expected.get('poster')=='special://profile/infinity-qa-poster.png':
        if out is None:raise ValueError('Actual poster output required')
        import cached_poster_observer
        poster=cached_poster_observer.observe(device,out,began,began+20)
    usable_ms=poster['first_observed_poster_capture_ms'] if poster is not None else visible_ms
    from resume_native_rpc import read
    rows=read(device,media,began+20)['files']
    if len(rows)!=1:raise AssertionError('Native directory differs from exact single visible saved card')
    verify_card(expected,labels,prefix,bool(device.rpc('Player.GetActivePlayers')),rows[0].get('resume'))
    return dict(media=media,key=key,exact_usable_card=True,observed=labels,
                observation_began_monotonic=began,
                native_directory_resume=rows[0].get('resume'),tab_select_to_card_visible_ms=visible_ms,
                tab_select_to_usable_card_ms=usable_ms,
                exact_native_proof_finished_ms=(time.monotonic()-began)*1000,
                verification_scope='Visible native resume percent plus exact directory native resume; reserved GUI properties are not readouts',
                generated_metadata_and_declared_clip=True,poster_paint_verified=poster is not None,
                actual_cached_poster=poster)
