#!/usr/bin/env python3
"""Bounded Pro-only rendering corrections following native test review."""
from pathlib import Path
root=Path(__file__).resolve().parent
p=root/'ProVisualTest.java';s=p.read_text()
old='frame.setImageBitmap(BitmapFactory.decodeFile(fixture.toString()))'
new='{byte[] bytes=java.nio.file.Files.readAllBytes(fixture.toPath());frame.setImageBitmap(BitmapFactory.decodeByteArray(bytes,0,bytes.length));}'
assert s.count(old)==1
s=s.replace(old+';else',new+'else')
p.write_text(s)
p=root/'CobraProUi.java.in';s=p.read_text()
old='int ink=overlay?Color.WHITE:light?INK:Color.WHITE;float pad=den*2'
new='''int ink=overlay?Color.WHITE:light?INK:Color.WHITE;
      // Edge chevrons have 48dp targets but no solid pill over the programme text.
      if("left".equals(glyph)||"right".equals(glyph)){icon(c,p,glyph,"left".equals(glyph)?0:w-den*24,(h-den*24)/2,den*24,ink);return;}
      float pad=den*2'''
assert s.count(old)==1;s=s.replace(old,new)
old='''if(animate&&was&&motion())info.post(()->{if(token!=animationToken||!info.isAttachedToWindow())return;int[] after=new int[2];info.getLocationOnScreen(after);info.setTranslationX(before[0]-after[0]);info.setTranslationY(before[1]-after[1]);info.animate().translationX(0).translationY(0).setDuration(260).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();});'''
new='''if(animate&&was&&motion()){
          final ViewTreeObserver tree=destination.getViewTreeObserver();
          tree.addOnPreDrawListener(new ViewTreeObserver.OnPreDrawListener(){public boolean onPreDraw(){
            if(tree.isAlive())tree.removeOnPreDrawListener(this);
            if(token==animationToken&&info.isAttachedToWindow()){
              int[] after=new int[2];info.getLocationOnScreen(after);
              info.setTranslationX(before[0]-after[0]);info.setTranslationY(before[1]-after[1]);
              info.animate().translationX(0).translationY(0).setDuration(260).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();
            }return true;
          }});
        }'''
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace('boolean active=primary||isSelected()||isPressed()||isFocused();','boolean active=isEnabled()&&(primary||isSelected()||isPressed()||isFocused());')
p.write_text(s)
print('PASS: Pro fixture decoded from bytes; clean chevrons; metadata uses measured destination for animation')
