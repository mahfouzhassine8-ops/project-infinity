"""Exact accepted438 class/method boundary and reuse of the four completed Cards checks."""
import hashlib,json,re,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1]
sys.path.insert(0,str(R/'repairs/cobra-next-from-2103427/cards-from-2103431'))
from projection_patch import methods

def verify(root,out):
    load=lambda p:json.loads(p.read_text())
    digest=lambda b:hashlib.sha256(b).hexdigest()
    before={};after={}
    for prefix,target in [('original-',before),('verify-',after)]:
        for directory in root.glob(prefix+'part-*'):
            for file in directory.rglob('*.smali'):
                raw=file.read_text();name=raw.splitlines()[0].split()[-1]
                assert name not in target;target[name]=raw
    def header(raw):
        raw=re.sub(r'^\.method [^\n]+\n.*?^\.end method\n?','',raw,flags=re.M|re.S)
        return re.sub(r'\n{3,}','\n\n',raw).strip()
    for name in before:assert header(before[name])==header(after[name]),name
    actual={}
    for name in before:
        if before[name]==after[name]:continue
        old_methods,new_methods=methods(before[name]),methods(after[name])
        actual[name]=sorted(k for k in old_methods.keys()|new_methods.keys() if old_methods.get(k)!=new_methods.get(k))
    assert actual==load(H/'METHOD-ALLOWLIST.json')
    assert {name:sorted(methods(after[name])) for name in after.keys()-before.keys()}==load(H/'NEW-CLASS-METHODS.json')
    old=load(H/'evidence/CLASS-HASHES.json')
    reused=[]
    # These are the exact classes exercised by the four checkpoint11a0d820 tests.
    for name in after:
        if name.startswith(('Lcom/projectinfinity/kodi/CobraCards','Lcom/projectinfinity/kodi/InfinityLiveActivity$CobraPlaying','Lcom/projectinfinity/kodi/InfinityLiveActivity$CobraPlayerBinding')):
            assert digest(after[name].encode())==old[name],name
            reused.append(name)
    app='Lcom/projectinfinity/kodi/InfinityLiveActivity;'
    retained=load(H/'RETAINED-CARDS-METHODS.json');current=methods(after[app])
    assert retained['class_sha256']==old[app]
    for signature,pin in retained['method_sha256'].items():assert digest(current[signature].encode())==pin,signature
    protected=['CobraProUi','CobraPresentation','CobraCardsTheme','CobraCardsDrawerViewport','InfinityLiveActivity$27','InfinityLiveActivity$28','InfinityLiveActivity$15']
    for cls in protected:
        name='Lcom/projectinfinity/kodi/'+cls+';';assert before[name]==after[name],name
    for name in before:
        if name.startswith('Lcom/projectinfinity/kodi/CobraProUi$') and not name.endswith('$ChannelRow;'):
            assert before[name]==after[name],name
    holder='Lcom/projectinfinity/kodi/CobraCardsTiles$Holder;'
    for sig in ['resize(I)V','expandedGeometry(Landroid/app/Activity;IIFI)V','rowHeight(Landroid/app/Activity;IF)I','public onClick(Landroid/view/View;)V']:
        assert methods(before[holder])[sig]==methods(after[holder])[sig]
    assert digest((root/'owner-dex/COBRA/part-1.dex').read_bytes())=='70dc429bff4d2df7fe19907100d5df39d5ade973aa2679328b42d567b3d5aee1'
    result=dict(status='PASS_EXACT438_OWNER_AND_CARDS_CHECK_REUSE',changed_methods=actual,
                unchanged_original_classes=sum(before[n]==after[n] for n in before),
                new_classes=sorted(after.keys()-before.keys()),fields_annotations='EXACT_ORIGINAL',
                cards_tested_classes_exact=reused,Pro_controls_adapters_navigation_Sports='BYTE_IDENTICAL',
                Cards_layout_themes_drawer='BYTE_IDENTICAL',second_Cobra_DEX='BYTE_IDENTICAL',
                Infinity='NOT_ACCESSED_BY_OWNER_BUILD;_FINAL_APK_CHECK_REQUIRED',shutdown='UNCHANGED_NOT_TESTED')
    out.mkdir(parents=True,exist_ok=True)
    (out/'OWNER-PRESERVATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'],result['unchanged_original_classes'])
if __name__=='__main__':verify(*(Path(v) for v in sys.argv[1:]))
