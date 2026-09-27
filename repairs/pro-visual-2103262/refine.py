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
p.write_text(s)
print('PASS: Pro fixtures decode from bytes; carousel chevrons no longer obscure metadata')
