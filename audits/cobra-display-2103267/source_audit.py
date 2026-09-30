#!/usr/bin/env python3
from pathlib import Path
import argparse,json,re,hashlib
p=argparse.ArgumentParser();p.add_argument('--activity',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
s=a.activity.read_text()
def req(v,m):
    if not v: raise RuntimeError(m)
def modes(pattern):
    m=re.search(pattern,s,re.S);req(m,'menu array not found');out=[]
    for raw in m.group(1).split(','):
        raw=raw.strip()
        out.append(12 if raw=='CobraFoldAspectPolicy.FIT_MODE' else 13 if raw=='CobraFoldAspectPolicy.FILL_MODE' else int(raw))
    return out
channel=modes(r'private void cobraShowChannelAspect\(Channel channel\).*?final int\[] modes=\{([^}]*)\};')
player=modes(r'private void showCobraAspectPicker\(\).*?final int\[] modes=\{([^}]*)\};')
default=modes(r'cobraOpenSheet\("Default fullscreen aspect".*?final int\[] modes=\{([^}]*)\};')
labels=['Fold Fit','Fold Fill','Inherit default','Best Fit','Crop / Fill','16:9','4:3','Wide 1.10x','Wide 1.25x','Wide 1.40x','Short + Wide','Zoom 1.25x','Zoom 1.50x','Zoom 2.00x','Custom Width / Height']
expected=[12,13,-1,0,1,2,3,4,5,6,7,8,9,10,11]
req(channel==expected,'Channel Display menu is not the complete locked 15-choice order: '+repr(channel))
req(player==[12,13,0,1,2,3,4,5,6,7,8,9,10,11],'Non-live Display menu incomplete: '+repr(player))
for n in labels:
    req(n in s,'Missing Display label '+n)
req('mPrefs.edit().putInt(COBRA_ASPECT_MODE,selected).apply();applyCobraAspectTransform()' in s,'Non-live selection does not immediately apply')
req('p.aspect=selected;if(cobraSavePreferences(channel,key,p,false))' in s,'Channel selection does not persist/apply through channel preference owner')
req('matrix.setScale(scale[0],scale[1],texture.getWidth()/2f,texture.getHeight()/2f);texture.setTransform(matrix);' in s,'Display transform is not replaced from a fresh centered matrix')
req('mInPictureInPicture?0:mode' in s,'PiP Best Fit safety path missing')
req('binding.layoutListener=' in s and 'cobraFitBinding(binding)' in s,'Layout/fold reflow callback missing')
result={
  'activity_sha256':hashlib.sha256(a.activity.read_bytes()).hexdigest(),
  'channel_display_count':len(channel),'channel_display_modes':channel,'channel_display_labels':labels,
  'non_live_display_count':len(player),'non_live_display_modes':player,
  'related_default_fullscreen_picker_modes':default,
  'related_default_fullscreen_picker_missing_custom_mode_11':11 not in default,
  'channel_display_complete':True,'fresh_matrix_each_apply':True,'pip_best_fit_safety':True,'layout_reflow_hook':True,
  'physical_device_verified':False,
  'note':'The video-toolbar Channel Display itself contains all 15 choices. A separate Playback Defaults picker omits Custom mode 11; this is recorded as a related settings inconsistency, not a failure of the toolbar menu.'
}
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
