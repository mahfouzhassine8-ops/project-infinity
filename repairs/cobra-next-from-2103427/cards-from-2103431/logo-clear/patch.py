"""Add only the Cards recycled-image unbind API to the accepted431 coordinator."""
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent

METHOD = r'''
.method public static clear(Landroid/app/Activity;Landroid/widget/ImageView;)V
    .registers 5

    if-eqz p1, :cards_clear_done
    sget-object v0, Lcom/projectinfinity/kodi/CobraLogoRequests;->OWNERS:Ljava/util/WeakHashMap;
    invoke-virtual {v0, p0}, Ljava/util/WeakHashMap;->get(Ljava/lang/Object;)Ljava/lang/Object;
    move-result-object v0
    check-cast v0, Ljava/lang/ref/WeakReference;
    if-eqz v0, :cards_clear_image
    invoke-virtual {v0}, Ljava/lang/ref/WeakReference;->get()Ljava/lang/Object;
    move-result-object v0
    check-cast v0, Lcom/projectinfinity/kodi/CobraLogoRequests;
    if-eqz v0, :cards_clear_image
    iget-object v1, v0, Lcom/projectinfinity/kodi/CobraLogoRequests;->waiting:Ljava/util/WeakHashMap;
    invoke-virtual {v1, p1}, Ljava/util/WeakHashMap;->remove(Ljava/lang/Object;)Ljava/lang/Object;
    iget-object v1, v0, Lcom/projectinfinity/kodi/CobraLogoRequests;->bindings:Ljava/util/WeakHashMap;
    invoke-virtual {v1, p1}, Ljava/util/WeakHashMap;->remove(Ljava/lang/Object;)Ljava/lang/Object;
    move-result-object v1
    check-cast v1, Lcom/projectinfinity/kodi/CobraLogoRequests$Binding;
    if-eqz v1, :cards_clear_image
    const-string v2, ""
    iput-object v2, v1, Lcom/projectinfinity/kodi/CobraLogoRequests$Binding;->url:Ljava/lang/String;
    invoke-virtual {p1, v1}, Landroid/view/View;->removeOnAttachStateChangeListener(Landroid/view/View$OnAttachStateChangeListener;)V
    :cards_clear_image
    const/4 v0, 0x0
    invoke-virtual {p1, v0}, Landroid/widget/ImageView;->setImageDrawable(Landroid/graphics/drawable/Drawable;)V
    :cards_clear_done
    return-void
.end method
'''


def methods(source):
    return {m[1]:m[0]+'\n' for m in re.finditer(r'^\.method ([^\n]+)\n.*?^\.end method', source, re.M|re.S)}


def patch(source):
    budget=json.loads((HERE/'SOURCE-BUDGET.json').read_text())
    assert hashlib.sha256(source.encode()).hexdigest()==budget['baseline_class_sha256']
    before=methods(source)
    result=source+'\n'+METHOD.lstrip()
    after=methods(result)
    assert set(after)-set(before)=={budget['new_method']}
    assert all(after[k]==v for k,v in before.items())
    return result
