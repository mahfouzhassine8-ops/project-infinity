"""Normalize only decoded string-index width and verified method-local label addresses.

Every literal, register, branch target, exception range, switch entry and other opcode
remains compared. Discard only unreachable alignment padding before switch payloads.
"""
import re
METHOD=re.compile(r'^\.method [^\n]*\n[\s\S]*?^\.end method\n',re.M)
LABEL=re.compile(r'^(:[A-Za-z_][\w]*)$')
LEX=re.compile(r'"(?:\\.|[^"\\])*"|(?<![\w$\"\']):[A-Za-z_][\w]*')

def canonical_method(match):
 lines=[line.strip() for line in match[0].splitlines() if line.strip()]
 switches=set()
 for line in lines:
  if re.match(r'(?:sparse|packed)-switch\s',line):switches.update(x[0] for x in LEX.finditer(line) if x[0].startswith(':'))
 kept=[]
 for i,line in enumerate(lines):
  if line=='nop' and i>0 and i+2<len(lines) and lines[i+1] in switches and lines[i+2].startswith(('.sparse-switch','.packed-switch')):
   # Padding has no incoming label and cannot be reached by fall-through.
   if re.match(r'(?:return(?:-\w+)?|throw|goto(?:/\d+)?)(?:\s|$)',kept[-1]):continue
  kept.append(re.sub(r'^const-string/jumbo\s','const-string ',line))
 definitions=[];payload=False
 for line in kept:
  if line.startswith(('.packed-switch','.sparse-switch','.array-data')):payload=True
  elif line.startswith(('.end packed-switch','.end sparse-switch','.end array-data')):payload=False
  elif not payload and LABEL.fullmatch(line):definitions.append(line)
 labels={line:':LABEL_'+str(i) for i,line in enumerate(definitions)}
 assert len(labels)==len(definitions),'Duplicate method label'
 def replacement(m):
  value=m[0]
  if value.startswith('"'):return value
  assert value in labels,'Undefined method branch/data/exception label: '+value
  return labels[value]
 return '\n'.join(LEX.sub(replacement,line) for line in kept)+'\n'

def canonical(text):return METHOD.sub(canonical_method,text)
