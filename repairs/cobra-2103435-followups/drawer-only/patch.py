"""Exact signed435 native coordinate-read delta; no other native method edit."""
import hashlib
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
CARDS=HERE.parents[1]/'cobra-next-from-2103427/cards-from-2103431'
sys.path.insert(0,str(CARDS))
from projection_patch import methods

SIGNATURE='private cobraLayoutGuide()V'
NATIVE_PREIMAGE='1631bfaf16a463f317a238982187eb92b7c9e7a8caa1de3cf6ddc63f4f1498aa'
PHYSICAL='physicalLayout(Landroid/app/Activity;Ljava/lang/Object;)V'
PHYSICAL_PREIMAGE='6080d81ed05360d034ea19b4d91613d9d9b706b7d09a3a6cad2ebe76e90e620f'

def patch(source,expected=NATIVE_PREIMAGE):
    old=methods(source)[SIGNATURE]
    assert hashlib.sha256(old.encode()).hexdigest()==expected,'Exact signed435 layout preimage required'
    call='    invoke-virtual {v4, v3}, Landroid/widget/FrameLayout;->getLocationInWindow([I)V'
    replacement='    invoke-static {v6, v4, v3}, Lcom/projectinfinity/kodi/CobraCardsDrawerViewport;->location(Landroid/app/Activity;Landroid/view/View;[I)V'
    assert old.count(call)==1
    revised=source.replace(old,old.replace(call,replacement),1)
    before,after=methods(source),methods(revised)
    assert before.keys()==after.keys()
    assert [k for k in before if before[k]!=after[k]]==[SIGNATURE]
    return revised

def physical(source):
    old=methods(source)[PHYSICAL]
    assert hashlib.sha256(old.encode()).hexdigest()==PHYSICAL_PREIMAGE
    call='    invoke-virtual {v5, v2}, Landroid/view/View;->getLocationInWindow([I)V'
    # v7 is dead here; its next original use assigns the left inset. Keep the
    # existing register count and every original geometry instruction intact.
    replacement='    move-object/from16 v7, p1\n\n    invoke-static {v7, v5, v2}, Lcom/projectinfinity/kodi/CobraCardsDrawerViewport;->location(Landroid/app/Activity;Landroid/view/View;[I)V'
    assert old.count(call)==1
    revised=source.replace(old,old.replace(call,replacement),1)
    before,after=methods(source),methods(revised)
    assert before.keys()==after.keys()
    assert [k for k in before if before[k]!=after[k]]==[PHYSICAL]
    return revised
