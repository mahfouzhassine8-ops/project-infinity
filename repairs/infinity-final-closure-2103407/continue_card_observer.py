"""Read-only extra observations around the retained Continue Playing UI case."""
import json
import math

BEFORE_HOME="                    xbmc.executebuiltin('ActivateWindow(Home)');ui.until(lambda:xbmcgui.getCurrentWindowId()==10000,'Home')"
AFTER_HOME="                    home_card_began=time.monotonic()\n"+BEFORE_HOME
BEFORE_CARD="                    passed('actual-home-one-card-'+media)"
AFTER_CARD='''                    from continue_card_observer import verify_card
                    card_prefix='Container(%d).ListItem.'%rail
                    fields=['Property(Infinity.Selection.Snapshot)','Property(ResumeTime)','Property(StartOffset)',
                            'Property(TotalTime)','Property(Infinity.ResumeHub.Watched)','Season','Episode','Label']
                    observed=ui.rpc('XBMC.GetInfoLabels',{'labels':[card_prefix+field for field in fields]})
                    verify_card(before['items'][key],observed,card_prefix,xbmc.Player().isPlaying())
                    result.setdefault('usable_resume_cards',[]).append(dict(media=media,key=key,
                        observed=observed,home_tab_to_correct_usable_card_ms=(time.monotonic()-home_card_began)*1000,
                        timing_scope='Test Home activation and tab selection to real exact card; not app launch',
                        synthetic_metadata_and_generated_clip=True))
'''+BEFORE_CARD


def verify_card(entry,labels,prefix,playing):
    if playing:raise AssertionError('Home restoration unexpectedly started playback')
    read=lambda name:labels.get(prefix+name,'')
    value=json.loads(read('Property(Infinity.Selection.Snapshot)'))
    if (value.get('key')!=entry['key'] or value.get('identity')!=entry['identity'] or
            value.get('source')!=entry['source'] or value.get('stable_source')!=entry['stable_source']):
        raise AssertionError('Real Home card identity/source differs from committed local state')
    for field,key in [('ResumeTime','position'),('StartOffset','position'),('TotalTime','duration')]:
        actual=float(read('Property('+field+')'))
        if not math.isfinite(actual) or actual!=float(entry[key]):
            raise AssertionError('Real Home card saved playback '+field+' differs')
    if read('Property(Infinity.ResumeHub.Watched)')!='false':
        raise AssertionError('Unfinished fixture card watched indicator differs')
    if entry['media']=='tv':
        if int(read('Season'))!=entry['season'] or int(read('Episode'))!=entry['episode']:
            raise AssertionError('Real Home card season/episode differs')


def instrument(text):
    for old,new in [(BEFORE_HOME,AFTER_HOME),(BEFORE_CARD,AFTER_CARD)]:
        if text.count(old)!=1:raise ValueError('Original Continue observation boundary differs')
        text=text.replace(old,new,1)
    if restore(text).count(BEFORE_CARD)!=1:raise ValueError('Continue observation inverse differs')
    compile(text,'android_selected.py','exec')
    return text


def restore(text):
    return text.replace(AFTER_CARD,BEFORE_CARD,1).replace(AFTER_HOME,BEFORE_HOME,1)
