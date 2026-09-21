"""Remove the exact repeated fullscreen aspect route; retain its existing button."""

def transform(source):
    old='    rows.addView(cobraSheetRow("aspect","Aspect / Display",cobraAspectLabel(mAspectMode),false,true,()->showCobraAspectPicker()));\n'
    if source.count(old)!=1:
        raise RuntimeError('Expected exactly one duplicate Options aspect row')
    if 'if(action==1)showCobraAspectPicker()' not in source:
        raise RuntimeError('Existing dedicated Aspect button missing')
    return source.replace(old,'',1)
