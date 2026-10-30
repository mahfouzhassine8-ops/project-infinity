"""Cards-only hooks on accepted431 native widgets; preserve all native actions.

The layout helper mutates only the existing Cards model arrays. Shared styling
is restored before native restyling, then reapplied only for active Cards.
"""
import hashlib
import json
from pathlib import Path
import re

from projection_patch import methods, replace_body

HERE = Path(__file__).resolve().parent
APP = 'Lcom/projectinfinity/kodi/InfinityLiveActivity;'
CARD = 'Lcom/projectinfinity/kodi/InfinityLiveActivity$CobraPosterChannelCard;'
LAYOUT = 'Lcom/projectinfinity/kodi/CobraCardsLayout;'
TILES = 'Lcom/projectinfinity/kodi/CobraCardsTiles;'


def _verify(name, source):
    budget = json.loads((HERE/'CARDS-SOURCE-BUDGET.json').read_text())[name]
    original = methods(source)
    for signature, pin in budget['selected_preimages'].items():
        assert hashlib.sha256(original[signature].encode()).hexdigest() == pin, signature
    return budget, original


def _finish(source, original, changes):
    result = source
    for signature, revised in changes.items():
        result = result.replace(original[signature], revised, 1)
    after = methods(result)
    assert set(original) == set(after)
    assert {s for s in original if original[s] != after[s]} == set(changes)
    strip = lambda s: re.sub(r'^\.method [^\n]+\n.*?^\.end method', '', s, flags=re.M|re.S)
    assert strip(source) == strip(result), 'Class metadata/fields/annotations stay exact'
    return result


def patch_activity(source):
    budget, before = _verify('Activity', source)
    changes = {}
    for signature in budget['selected_preimages']:
        old = before[signature]
        revised = old
        if 'cobraLayoutGuide(' in signature:
            anchor = '    :cond_3\n    iget-object v0, v6, '+APP+'->mCobraGuideStyle:Ljava/lang/String;'
            assert old.count(anchor) == 1
            revised = old.replace(anchor, '    :cond_3\n'+
                '    iget-object v0, v6, '+APP+'->mCobraModeLayout:Lcom/projectinfinity/kodi/InfinityLiveActivity$CobraModeLayout;\n'+
                '    invoke-static {v6, v0}, '+LAYOUT+'->layout(Landroid/app/Activity;Ljava/lang/Object;)V\n'+
                anchor.split('\n', 1)[1], 1)
        elif 'cobraShowGuideShell(' in signature:
            # Preserve the original Stage/aliveness eligibility checks. Restore
            # Cards ownership before the destination mode writes Stage padding.
            anchor='    :cond_0\n    iget-boolean v0, p0, '+APP+'->mCobraProActive:Z'
            assert old.count(anchor)==1
            revised=old.replace(anchor,'    :cond_0\n'+
                '    invoke-static/range {p0 .. p0}, '+LAYOUT+'->beforeShell(Landroid/app/Activity;)V\n\n'+
                anchor.split('\n',1)[1],1)
        elif 'cobraAmbientSurface(' in signature:
            anchor='    .registers 14\n'
            assert old.count(anchor)==1 and ':cobra_cards_original_ambient' not in old
            revised=old.replace(anchor,anchor+'\n'+
                '    invoke-static/range {p0 .. p5}, '+LAYOUT+'->ambientSurface(Landroid/app/Activity;Landroid/view/View;IIIZ)Z\n'+
                '    move-result v0\n'+
                '    if-eqz v0, :cobra_cards_original_ambient\n'+
                '    return-void\n'+
                '    :cobra_cards_original_ambient\n',1)
        else:
            if 'cobraRestyleGuide(' in signature:
                anchor = '    .registers 12\n'
                assert old.count(anchor) == 1
                revised = revised.replace(anchor, anchor+'\n    invoke-static/range {p0 .. p0}, '+LAYOUT+'->beforeShell(Landroid/app/Activity;)V\n', 1)
            if 'cobraRefreshModeDetails(' in signature:
                api = 'refreshDetails(Landroid/app/Activity;)Z'
            elif 'cobraRefreshVisualEffects(' in signature:
                api = 'refreshPreview(Landroid/app/Activity;)V'
            else:
                api = 'afterRender(Landroid/app/Activity;)V'
            assert revised.count('    return-void') >= 1
            revised = revised.replace('    return-void',
                '    invoke-static/range {p0 .. p0}, '+LAYOUT+'->'+api+'\n\n    return-void')
        assert revised != old
        changes[signature] = revised
    return _finish(source, before, changes)


def patch_card(source):
    budget, before = _verify('Card', source)
    changes = {}
    for signature in budget['selected_preimages']:
        old = before[signature]
        if 'constructor <init>(' in signature:
            assert old.count('    return-void') == 1
            revised = old.replace('    return-void',
                '    move-object/from16 v0, p0\n'+
                '    move-object/from16 v1, p1\n'+
                '    invoke-static {v1, v0}, '+TILES+'->created(Landroid/app/Activity;Landroid/widget/LinearLayout;)V\n\n    return-void', 1)
        elif signature.startswith('bind('):
            revised = replace_body(old, 4,
                '    iget-object v0, p0, '+CARD+'->this$0:'+APP+'\n'+
                '    invoke-static {v0, p0, p1, p2}, '+TILES+'->bind(Landroid/app/Activity;Landroid/widget/LinearLayout;Ljava/lang/Object;I)V\n'+
                '    return-void')
        elif signature == 'refreshPlaying()V':
            revised = replace_body(old, 2,
                '    iget-object v0, p0, '+CARD+'->this$0:'+APP+'\n'+
                '    invoke-static {v0, p0}, '+TILES+'->refresh(Landroid/app/Activity;Landroid/widget/LinearLayout;)V\n'+
                '    return-void')
        else:
            raise AssertionError(signature)
        changes[signature] = revised
    return _finish(source, before, changes)
