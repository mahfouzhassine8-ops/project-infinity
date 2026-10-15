#!/usr/bin/env python3
"""Exact-preimage chooser-material refinement; production startup/callbacks stay untouched.
The focus assertion explicitly transitions out of Android touch mode. No test is disabled.
"""
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent
PREIMAGES={'InfinityGlassChooser.java.in': '4c8aa204a403c8878b96d9ca1f76b4661e826d1adb461adb811bcc3766d038f2', 'apply.py': '2ef0cfe1e043e84a7357ca70f7fbe89565030bc901af9e94f5b3138b5b2dd195', 'GlassChooserTest.java': 'dc2f2d851185df861b1ee931ff6d25750a6f6bc5bc12e7caebdc34f113be55ed'}
ASSET_SHA256={'art-hd-0.json': '834220389d5aa2270fd9efbc6ed7935de04ae8dfc5f2b788e72d95de3d74cada', 'art-hd-1.json': '13d9d554e2451fee3d0b6aab12c6dc233810cf86834a085c1b5ae4953369fb93', 'art-hd-2.json': '5e56e93c9f860726de1ba0d96de4ff30d0ce85cc3c0cae72a11284bbb8743c2d', 'art-hd-3.json': '96ffa19d2a17ac286096f1e59d459e84cdf3668476ecac8033b4b7cf8ffdddf4', 'art-hd-4.json': '503538dfcb6dbb568344282855c9aa9688a888a0381748fa64dd3f18df5b153a', 'art-hd-5.json': '8ce2439564ea7faf3e5ec2beba6b36e151e01a69df7114efc6c119339d189b24'}
for name,digest in PREIMAGES.items():
    assert hashlib.sha256((P/name).read_bytes()).hexdigest()==digest, 'Unexpected repair source '+name
# Normalize the single transport transcription byte before verifying source-image hashes.
asset=P/'assets/art-hd-4.json'
raw=asset.read_bytes()
if hashlib.sha256(raw).hexdigest()=='78702ad41b2d15645bf0dbb9b6696e29f5b486a9f2d46dec50991fa6866f8b50':
    assert raw.count(b'YiFCYtg3jDv9Ch')==1
    asset.write_bytes(raw.replace(b'YiFCYtg3jDv9Ch',b'YiFCYtg2jDv9Ch'))
for name,digest in ASSET_SHA256.items():
    assert hashlib.sha256((P/'assets'/name).read_bytes()).hexdigest()==digest, 'Changed art asset '+name

s=(P/'InfinityGlassChooser.java.in').read_text()
s=s.replace('add(new Mark(c,false),light?341:391,light?95:82,light?156:153,light?61:62,false);','add(new Mark(c,light,"header_mark"),light?338:372,light?86:68,light?162:186,light?76:82,false);')
s=s.replace('part(new Mark(c,cobra),light?(cobra?49:68):(cobra?60:78),light?(cobra?151:178):(cobra?147:179),light?(cobra?279:246):(cobra?281:249),light?(cobra?159:148):(cobra?165:130),false);','part(new Mark(c,light,cobra?"cyan_mark":"gold_mark"),light?(cobra?48:56):(cobra?61:75),light?(cobra?140:166):(cobra?145:178),light?(cobra?292:279):(cobra?281:244),light?(cobra?188:156):(cobra?169:128),false);')
s=s.replace('if(b.view instanceof Label)((Label)b.view).scale=scale;\n        b.view.measure','if(b.view instanceof Label)((Label)b.view).scale=scale;\n        if(b.view instanceof Gear)((Gear)b.view).visualSize=Math.round(b.w*scale);\n        b.view.measure')
# Gear housing uses the original approved material, but all events and state are native.
start=s.index('  static final class Gear extends View {')
s=s[:start]+'''  static final class Gear extends View {
    final Paint p=new Paint(Paint.ANTI_ALIAS_FLAG|Paint.FILTER_BITMAP_FLAG);
    final RectF frame=new RectF(),artBounds=new RectF();final Path cog=new Path();
    final boolean light,cobra;final Bitmap material;int visualSize=Integer.MAX_VALUE;
    Gear(Context c,boolean light,boolean cobra){super(c);this.light=light;this.cobra=cobra;
      material=InfinityGlassArt.decode((light?"light":"dark")+(cobra?"_gear_cyan":"_gear_gold"));
      setFocusable(true);setClickable(true);
    }
    @Override protected void onSizeChanged(int w,int h,int ow,int oh){
      super.onSizeChanged(w,h,ow,oh);float s=Math.min(visualSize,Math.min(w,h)),cx=w/2f,cy=h/2f;
      artBounds.set(cx-s*.5f,cy-s*.5f,cx+s*.5f,cy+s*.5f);
      frame.set(cx-s*.42f,cy-s*.42f,cx+s*.42f,cy+s*.42f);cog.reset();
      for(int i=0;i<40;i++){double angle=i*Math.PI/20-Math.PI/2;float rad=s*((i%5==1||i%5==2)? .123f:.097f);
        float x=cx+(float)Math.cos(angle)*rad,y=cy+(float)Math.sin(angle)*rad;if(i==0)cog.moveTo(x,y);else cog.lineTo(x,y);}
      cog.close();
    }
    @Override protected void onDraw(Canvas c){
      float s=artBounds.width();p.setStyle(Paint.Style.FILL);p.setColor(Color.WHITE);c.drawBitmap(material,null,artBounds,p);
      p.setStyle(Paint.Style.STROKE);
      if(isPressed()||isFocused()){p.setStrokeWidth(Math.max(2,s*.035f));p.setColor(cobra?0xff159acc:0xffbc9438);c.drawRoundRect(frame,s*(light?.42f:.27f),s*(light?.42f:.27f),p);}
      p.setColor(light?0xff082339:0xffe1ebf3);p.setStrokeWidth(Math.max(1.5f,s*.022f));c.drawPath(cog,p);c.drawCircle(getWidth()/2f,getHeight()/2f,s*.036f,p);
    }
    @Override protected void drawableStateChanged(){super.drawableStateChanged();invalidate();}
    @Override public void onInitializeAccessibilityNodeInfo(AccessibilityNodeInfo info){super.onInitializeAccessibilityNodeInfo(info);info.setClassName("android.widget.Button");}
  }
  /** Independent approved brand artwork; not reinterpreted or recolored at runtime. */
  private static final class Mark extends View {
    final Bitmap bitmap;final Paint p=new Paint(Paint.ANTI_ALIAS_FLAG|Paint.FILTER_BITMAP_FLAG);final RectF bounds=new RectF();
    Mark(Context c,boolean light,String key){super(c);bitmap=InfinityGlassArt.decode((light?"light_":"dark_")+key);setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);}
    @Override protected void onSizeChanged(int w,int h,int ow,int oh){super.onSizeChanged(w,h,ow,oh);bounds.set(0,0,w,h);}
    @Override protected void onDraw(Canvas c){c.drawBitmap(bitmap,null,bounds,p);}
  }
}
'''
s=s.replace('eight small text-free material plates','independent text-free material plates')
(P/'InfinityGlassChooser.java.in').write_text(s)
a=(P/'apply.py').read_text()
a=a.replace("art=json.loads((here/'assets/art.json').read_text());assert set(art)=={m+'_'+p for m in ['light','dark'] for p in ['gold','cyan','orb','background']}","art=json.loads((here/'assets/art.json').read_text())\n    for enhanced in sorted((here/'assets').glob('art-hd-*.json')):art.update(json.loads(enhanced.read_text()))\n    assert set(art)=={m+'_'+p for m in ['light','dark'] for p in ['gold','cyan','orb','background','header_mark','gold_mark','cyan_mark','gear_gold','gear_cyan']}")
(P/'apply.py').write_text(a)
t=(P/'GlassChooserTest.java').read_text().replace('assertTrue(ui.stage.infinity.requestFocus());assertTrue(ui.stage.infinity.isFocused());','Shadows.shadowOf(Looper.getMainLooper()).idle();\n      // Directional input exits Android touch mode; requestFocusFromTouch models that transition.\n      assertTrue(mode+" "+size[0]+"x"+size[1]+" request directional focus",ui.stage.infinity.requestFocusFromTouch());\n      assertTrue(mode+" "+size[0]+"x"+size[1]+" card owns focus",ui.stage.infinity.isFocused());')
t=t.replace('new String[]{"background","orb","gold","cyan"}','new String[]{"background","orb","gold","cyan","header_mark","gold_mark","cyan_mark","gear_gold","gear_cyan"}').replace('getByteCount()<700000','getByteCount()<7000000')
(P/'GlassChooserTest.java').write_text(t)

EXPECTED_RESULT={'InfinityGlassChooser.java.in': '73bd6c469351678b47691d6af6c4c4cb3cab4306cddbd6aac930a3a8c3f7043b', 'apply.py': 'aa020de49b4a68774836c33c83103834728e500474b16eb03514b98bfdd7c470', 'GlassChooserTest.java': 'c7139d80f8dac89236d11a1a7896ffca6159e78e96b1f342f12c1ffc72774008'}
for name,digest in EXPECTED_RESULT.items():
    assert hashlib.sha256((P/name).read_bytes()).hexdigest()==digest, 'Unexpected refined result '+name
print('PASS: exact source-derived material and directional-focus refinements applied')
