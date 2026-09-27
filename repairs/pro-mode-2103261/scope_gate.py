#!/usr/bin/env python3
import argparse,hashlib,json,re
from pathlib import Path
def sha_text(s):return hashlib.sha256(s.encode()).hexdigest()
def method(text,name):
    m=re.search(r'(?m)^  private(?: static| final| synchronized|\s+)*[^\n]*\b'+re.escape(name)+r'\s*\(',text)
    if not m: raise AssertionError('missing method '+name)
    start=m.start();brace=text.find('{',m.end()-1);assert brace>=0
    depth=0;i=brace;quote=None;escape=False;line=False;block=False
    while i<len(text):
      c=text[i];n=text[i+1] if i+1<len(text) else ''
      if line:
        if c=='\n':line=False
      elif block:
        if c=='*' and n=='/':block=False;i+=1
      elif quote:
        if escape:escape=False
        elif c=='\\':escape=True
        elif c==quote:quote=None
      else:
        if c=='/' and n=='/':line=True;i+=1
        elif c=='/' and n=='*':block=True;i+=1
        elif c in "'\"":quote=c
        elif c=='{':depth+=1
        elif c=='}':
          depth-=1
          if depth==0:return text[start:i+1]
      i+=1
    raise AssertionError('unterminated '+name)
def main():
  ap=argparse.ArgumentParser();ap.add_argument('--before',type=Path,required=True);ap.add_argument('--after',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
  old=a.before.read_text();new=a.after.read_text()
  protected=['cobraRenderGridMode','cobraRenderCompactMode','cobraRenderCardsMode','cobraPreviewPanel','startCobraPreview','cobraStartDirectPreview','cobraStartLocalTimeshiftPreview','promoteCobraPreviewToFullscreen','closeFullscreenToCobraView','openPlayerOverlay','startSinglePlayer','releaseMulti','showMovies','showSeries','showCobraHealthCenter']
  hashes={}
  for name in protected:
    x=method(old,name);y=method(new,name);assert x==y,'protected method changed: '+name;hashes[name]=sha_text(x)
  old_focus=method(old,'cobraRenderFocusMode');new_focus=method(new,'cobraRenderFocusMode')
  assert new_focus.replace('    cobraEnterProMode(channels);\n','',1)==old_focus,'Focus lower renderer changed beyond Pro entry hook'
  assert old.count('new ExoPlayer')==new.count('new ExoPlayer'),'new player owner introduced'
  assert old.count('buildPlayer(')==new.count('buildPlayer('),'player construction sites changed'
  assert 'String[] values = {"grid", "compact", "cards", "focus"};' in new
  assert 'static final String[] MODES={"mobile","grid","compact","cards","focus"};' in new
  assert 'String[] labels = {"TV Grid", "Compact", "Cards", "Pro"};' in new
  assert 'COBRA_PRO_MAX_SLOTS=6' in new
  assert all(x in new for x in ['COBRA_PRO_RESTING','COBRA_PRO_PREVIEW','COBRA_PRO_WATCHING','cobra_pro_source','cobra_pro_preview','cobra_pro_unmute','FROM FAVORITES','RECENTLY WATCHED','CONTINUE WATCHING'])
  p=method(new,'cobraProPreview');u=method(new,'cobraProUnmute')
  assert 'mCobraPreviewPlayer' in p and 'mCobraPreviewPlayer' in u and 'new ExoPlayer' not in p+u
  assert 'cobraUserUnmute(player)' in u and 'cobraSetProState(COBRA_PRO_WATCHING,true)' in u
  assert 'promoteCobraPreviewToFullscreen' not in p+u,'Preview/unmute must not auto-fullscreen'
  install=method(new,'cobraInstallProHeroOverlay');assert 'setOnTouchListener' in install and 'cobraProStep(dx<0?1:-1)' in install
  assert 'mCobraPreviewHost.addView(overlay' in install and 'cobra_pro_hero_overlay' in install and 'GridView' not in install and 'RecyclerView' not in install
  adjust=method(new,'cobraAdjustProLayout');assert 'COBRA_PRO_WATCHING' in adjust and 'layout.details' in adjust
  key_pattern=r'(?:getString|putString)\(\"(cobra_[a-z0-9_]+)\"'
  old_keys=set(re.findall(key_pattern,old));new_keys=set(re.findall(key_pattern,new));added=sorted(new_keys-old_keys)
  assert added==['cobra_pro_hero_channel','cobra_pro_hero_source'],added
  report={'protected_methods_byte_identical':protected,'protected_method_sha256':hashes,'focus_lower_renderer_byte_identical_after_entry_hook':True,'new_exoplayer_sites':0,'build_player_sites_unchanged':True,'internal_focus_key_preserved':True,'pro_slot_cap':6,'new_preferences':added,'source_swipe_inside_preview_host':True,'fullscreen_path_unchanged':True}
  a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
