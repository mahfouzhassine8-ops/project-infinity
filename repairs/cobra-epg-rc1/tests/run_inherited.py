#!/usr/bin/env python3
"""Rerun unchanged inherited assertions against the repaired production helpers."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,subprocess,sys
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT.parent))
from apply_epg_repair import span,digest

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--repository',type=Path,required=True);p.add_argument('--mode-harness',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    text=a.source.read_text();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    original=a.repository/'tests/cobra_2103153/test_refinement.py'
    spec=importlib.util.spec_from_file_location('inherited_refinement',original);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.verify(text)
    parts=[]
    for name,kind in [(n,'class') for n in ('CobraGuideMath','CobraLayoutMath','CobraTileStore','CobraEpgData','GuideProgram')]+[(n,'method') for n in ('parseXmlTvTime','cobraBoundedId','cobraParseGuide','cobraEpgHasCoverage')]:
        x,y=span(text,name,kind);parts.append(text[x:y])
    java='''import java.io.*;import java.util.*;import java.text.*;import java.util.regex.*;import java.nio.charset.StandardCharsets;import org.xmlpull.v1.*;import android.util.Xml;
public class CobraRefinementHarness {private boolean mCobraAsyncDestroyed=false;
'''+ '\n'.join(parts)+'\n'+module.HARNESS+'\n}\n'
    files={'CobraRefinementHarness.java':java,'org/xmlpull/v1/XmlPullParser.java':module.XML_INTERFACE,'org/xmlpull/v1/XmlPullParserException.java':'package org.xmlpull.v1; public class XmlPullParserException extends Exception { public XmlPullParserException(String text){super(text);} }','android/util/Xml.java':module.XML_ADAPTER}
    for name,content in files.items():f=out/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(content)
    subprocess.run(['javac','-encoding','UTF-8','-d',str(out)]+[str(out/n) for n in files],check=True)
    first=subprocess.run(['java','-Xmx768m','-cp',str(out),'CobraRefinementHarness'],check=True,capture_output=True,text=True)
    # Keep the actual inherited mode assertion body, replacing only its production class with the exact current class.
    mode=a.mode_harness.read_text();x,y=span(mode,'CobraModeLayout','class');s,e=span(text,'CobraModeLayout','class')
    if mode[x:y]!=text[s:e]:raise AssertionError('EPG repair changed the inherited layout policy')
    (out/'CobraModesHarness.java').write_text(mode)
    subprocess.run(['javac','-encoding','UTF-8','-d',str(out),str(out/'CobraModesHarness.java')],check=True)
    second=subprocess.run(['java','-cp',str(out),'CobraModesHarness'],check=True,capture_output=True,text=True)
    result={'source_sha256':digest(text),'inherited_assertions_sha256':digest(module.HARNESS),'mode_harness_sha256':digest(mode),'stdout':first.stdout+second.stdout,'device_verified':False}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');(out/'output.txt').write_text(result['stdout']);print(result['stdout'])
if __name__=='__main__':main()
