"""Fail-closed Home-only Fold clock width repair, no other controls changed."""
from __future__ import annotations
import hashlib
import xml.etree.ElementTree as ET

PREIMAGE_SHA256 = "3f774364299b3c535dda0a52b1b304fc65b562f84a8ca6e1a9110ab7c39056f0"
OLD = (b'<param name="timeleft" value="72%" />\n'
       b'          <param name="timetop" value="2" />\n'
       b'          <param name="timewidth" value="26%" />')
NEW = (b'<param name="timeleft" value="64%" />\n'
       b'          <param name="timetop" value="2" />\n'
       b'          <param name="timewidth" value="34%" />')

def transform(original):
    if hashlib.sha256(original).hexdigest() != PREIMAGE_SHA256:
        raise ValueError('Unexpected Home preimage')
    if original.count(OLD) != 1:
        raise ValueError('Missing exact time cluster')
    after = original.replace(OLD, NEW, 1)
    if after.replace(NEW, OLD, 1) != original:
        raise ValueError('Unrelated Home modification')
    root = ET.fromstring(after)
    status = [i for i in root.iter('include') if i.get('content') == 'InfinityHomeStatusCluster']
    if len(status) != 1:
        raise ValueError('Status cluster not unique')
    values = {x.get('name'): x.get('value') for x in status[0]}
    if (values['timeleft'], values['timewidth'], values['timetop'], values['timeheight']) != ('64%', '34%', '2', '64'):
        raise ValueError('Clock geometry mismatch')
    return after
