"""Exact requested presentation supersessions on disposable 208 fixtures only.

The complete unmodified 207 fixture inventory runs first on the exact parent.
Keep all original case identities and all unrelated behavioral assertions.
"""
from pathlib import Path
import hashlib
import json

def adapt(folder, output):
    log = []
    def edit(filename, changes, reason):
        path = Path(folder) / filename
        original = path.read_text()
        text = original
        for before, after in changes:
            if text.count(before) != 1:
                raise RuntimeError('208 fixture anchor drift: ' + filename + ': ' + before)
            text = text.replace(before, after, 1)
        if text.count('@Test') != original.count('@Test'):
            raise RuntimeError('208 supersession altered test count')
        path.write_text(text)
        log.append(dict(file=filename, reason=reason,
            before=hashlib.sha256(original.encode()).hexdigest(),
            after=hashlib.sha256(text.encode()).hexdigest(), retained_all_test_identities=True))
    edit('Cobra2103205PresentationEffectsTest.java', [
        ('@Before public void before(){',
         '@Before public void before(){Cobra2103208BrandingTest.installApprovedArtwork();'),
        ('assertEquals(CobraPresentationEffects.PulseState.NORMAL,CobraPresentationEffects.pulseState(true,false,false,false,false,false,false,false));',
         'assertEquals(CobraPresentationEffects.PulseState.NONE,CobraPresentationEffects.pulseState(true,false,false,false,false,false,false,false));'),
        ('if(state==CobraPresentationEffects.PulseState.LIVE?maximum-minimum<25&&maximum>130&&maximum<(canvas==Color.WHITE?250:256):maximum-minimum>15)ink++;',
         'if(maximum-minimum>15)ink++;'),
    ], 'Healthy playback now has no watermark. Every drawable status retains the approved cyan/red brand artwork instead of recoloring LIVE gray; all states still must render visible pixels on light and dark. Manifest-free fixtures explicitly load the exact approved PNG because they intentionally lack the production resource table.')
    edit('Cobra2103205PresentationUiTest.java', [
        ('single();assertEquals(CobraPresentationEffects.PulseState.NORMAL,call("cobraVisualPulseState",player.instance));',
         'single();assertEquals(CobraPresentationEffects.PulseState.NONE,call("cobraVisualPulseState",player.instance));'),
    ], 'User explicitly removed the mark for healthy playback; decoder error, pause, suppression and actual buffering assertions remain intact.')
    edit('Cobra2103207RefinementUiTest.java', [
        ('@Before public void before()throws Exception{f=new Cobra2103201SubtitleTest();f.before();}',
         '@Before public void before()throws Exception{Cobra2103208BrandingTest.installApprovedArtwork();f=new Cobra2103201SubtitleTest();f.before();}'),
        ('assertTrue(opaque>0);assertEquals(0,black);assertEquals(0,Color.alpha(b.getPixel(1,20)));',
         'assertTrue(opaque>0);assertTrue("No black backing/disc area",black<=1);assertTrue("Transparent edge residue",Color.alpha(b.getPixel(1,20))<=1);'),
    ], 'Manifest-free tests install the exact approved PNG used in production. The legacy vector-era case remains a no-black-disc/backing-area guard: one isolated Skia raster pixel and at most alpha-1 edge interpolation are tolerated, while any second black pixel or visible edge opacity still fails; dedicated 208 branding tests continue to require the cyan/red approved mark without a backdrop.')
    edit('CobraVisualRuntimeTest.java', [
        ('try{View mark=(View)CobraNavigationUiTest.construct("CobraBrandMark",a);',
         'try{Cobra2103208BrandingTest.installApprovedArtwork();View mark=(View)CobraNavigationUiTest.construct("CobraBrandMark",a);'),
        ('assertEquals(Color.MAGENTA,b.getPixel(40,40));',
         'assertNotEquals(Color.MAGENTA,b.getPixel(40,40));assertTrue(new Cobra2103208BrandingTest().count(b,false)>50);assertTrue(new Cobra2103208BrandingTest().count(b,true)>=2);assertEquals("badge",CobraVisualRenderer.active.id);'),
    ], 'User explicitly locked the same red-eyed Cobra-Infinity identity everywhere. Only the drawer.badge artwork override is superseded by that fixed identity; the custom theme remains active, cyan and red pixels must render, and every unrelated theme-runtime case and slot remains unchanged.')
    Path(output).write_text(json.dumps(log, indent=2) + '\n')
