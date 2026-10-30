"""Front Cards Player settings host only; preserve native callbacks/menu body."""
from hashlib import sha256
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
SIGNATURE='private cobraOpenSheet(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)Landroid/widget/LinearLayout;'

def patch(source):
    pattern=re.compile(r'^\.method ([^\n]+)\n.*?^\.end method',re.M|re.S)
    methods={m[1]:m[0]+'\n' for m in pattern.finditer(source)}
    old=methods[SIGNATURE]
    budget=json.loads((HERE/'SOURCE-BUDGET.json').read_text())
    assert sha256(old.encode()).hexdigest()==budget['preimage_sha256']
    anchor='    .line 7654\n    iget-object v2, v7, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mMultiOverlay:Landroid/widget/FrameLayout;'
    assert old.count(anchor)==1
    added=('    .line 7654\n'
           '    invoke-static {v7, v8}, Lcom/projectinfinity/kodi/CobraCardsLayout;->frontPlayerSheetHost(Landroid/app/Activity;Ljava/lang/String;)Landroid/widget/FrameLayout;\n'
           '    move-result-object v2\n'
           '    if-nez v2, :goto_2\n'
           '    iget-object v2, v7, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mMultiOverlay:Landroid/widget/FrameLayout;')
    new=old.replace(anchor,added,1)
    assert new.replace(added,anchor,1)==old
    result=source.replace(old,new,1)
    after={m[1]:m[0]+'\n' for m in pattern.finditer(result)}
    assert set(after)==set(methods) and {k for k in methods if methods[k]!=after[k]}=={SIGNATURE}
    assert pattern.sub('',source)==pattern.sub('',result)
    return result
