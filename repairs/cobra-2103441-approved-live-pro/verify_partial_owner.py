"""Bound the partial Cards owner against actual accepted438 canonical definitions.

This is not the final combined APK/signature gate or a Pro acceptance check.
"""
import json,re,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1]
sys.path.insert(0,str(R/'repairs/cobra-next-from-2103427/cards-from-2103431'))
from projection_patch import methods

def verify(root,preview,out):
    load=lambda p:json.loads(p.read_text())
    meta=load(root/'OWNER-BUILD.json');before={};after={}
    for prefix,target in [('original-',before),('verify-',after)]:
        for directory in root.glob(prefix+'part-*'):
            for file in directory.rglob('*.smali'):
                raw=file.read_text();name=raw.splitlines()[0].split()[-1]
                assert name not in target;target[name]=raw
    def header(raw):
        raw=re.sub(r'^\.method [^\n]+\n.*?^\.end method\n?','',raw,flags=re.M|re.S)
        return re.sub(r'\n{3,}','\n\n',raw).strip()
    for name in before:assert header(before[name])==header(after[name]),name
    holder='Lcom/projectinfinity/kodi/CobraCardsTiles$Holder;'
    for method in ['resize(I)V','expandedGeometry(Landroid/app/Activity;IIFI)V','rowHeight(Landroid/app/Activity;IF)I','public onClick(Landroid/view/View;)V']:
        assert methods(before[holder])[method]==methods(after[holder])[method],method
    frozen=['CobraProUi','CobraCardsTheme','CobraCardsDrawerViewport','InfinityLiveActivity$CobraPlayingDot','InfinityLiveActivity$CobraPlayingIndicatorPolicy','InfinityLiveActivity$CobraPlayerBinding']
    for cls in frozen:
        name='Lcom/projectinfinity/kodi/'+cls+';';assert before[name]==after[name],name
    app='Lcom/projectinfinity/kodi/InfinityLiveActivity;'
    tap='synthetic lambda$cobraPreviewPanel$71$com-projectinfinity-kodi-InfinityLiveActivity(Landroid/view/View;)V'
    assert methods(preview.read_text())[tap]==methods(after[app])[tap]
    report={
      'status':'PASS_CARDS_PARTIAL_OWNER_PRESERVATION','baseline':'actual signed2103438',
      'rejected441':'not_used_as_baseline','unchanged_classes':meta['unchanged'],
      'changed_methods':load(root/'METHOD-DELTA.json'),
      'new_class':'CobraCardsTiles$LivePlayback; weak-reference bridge to unchanged native effect',
      'original_class_fields_annotations':'IDENTICAL',
      'cards_geometry_menu_methods':'BYTE_IDENTICAL_TO438',
      'native_playing_effect_policy_binding':'BYTE_IDENTICAL_TO438',
      'working_preview_tap':'BYTE_IDENTICAL_TO440',
      'frozen_classes_checked':frozen,
      'Pro':'ORIGINAL438_IN_PARTIAL_OWNER; APPROVED_INNER_IMPLEMENTATION_PENDING_IMAGE',
      'Infinity':'NO_SOURCE_OR_COMPONENT_CHANGE; FINAL_APK_NOT_BUILT',
      'shutdown':'UNCHANGED_NOT_TESTED','final_signed_APK_preservation':'NOT_RUN_NO_CANDIDATE'}
    out.mkdir(exist_ok=True,parents=True)
    (out/'PARTIAL-OWNER-PRESERVATION.json').write_text(json.dumps(report,indent=2)+'\n')
    for name in ['OWNER-BUILD.json','METHOD-DELTA.json','CLASS-HASHES.json']:(out/name).write_bytes((root/name).read_bytes())
    print(report['status'])

if __name__=='__main__':verify(*(Path(value) for value in sys.argv[1:]))
