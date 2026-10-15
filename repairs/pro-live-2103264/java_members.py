import re

def span(text,name):
    m=re.search(r'(?m)^  private[^\n]*\b'+re.escape(name)+r'\s*\(',text)
    assert m,'Missing Java member '+name
    start=m.start();i=text.find('{',m.end());depth=0;mode='';escape=False
    while i<len(text):
        c=text[i];pair=text[i:i+2]
        if mode=='line':
            if c=='\n':mode=''
        elif mode=='block':
            if pair=='*/':mode='';i+=1
        elif mode:
            if escape:escape=False
            elif c=='\\':escape=True
            elif c==mode:mode=''
        elif pair=='//':mode='line';i+=1
        elif pair=='/*':mode='block';i+=1
        elif c in '\"\'':mode=c
        elif c=='{':depth+=1
        elif c=='}':
            depth-=1
            if depth==0:return start,i+1
        i+=1
    raise AssertionError('Unterminated '+name)

def member(text,name):
    a,b=span(text,name);return text[a:b]
