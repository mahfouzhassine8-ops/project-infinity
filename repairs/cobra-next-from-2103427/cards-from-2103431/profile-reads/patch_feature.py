"""Only replace exact accepted431 adultLocked with its fresh-ID/private-data wrapper."""
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
FEATURE='Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;'
HELPER='Lcom/projectinfinity/kodi/CobraProfileDataReuse;'


def methods(text):
    return {m[1]:m[0]+'\n' for m in re.finditer(r'^\.method ([^\n]+)\n.*?^\.end method',text,re.M|re.S)}


def patch(text):
    budget=json.loads((HERE/'SOURCE-BUDGET.json').read_text())
    assert hashlib.sha256(text.encode()).hexdigest()==budget['feature_class_sha256'],'Exact accepted431 canonical FeatureRuntime source required'
    before=methods(text);signature='public adultLocked()Z'
    assert hashlib.sha256(before[signature].encode()).hexdigest()==budget['selected_method_preimages'][signature]
    replacement=''' .method public adultLocked()Z
    .registers 3

    invoke-virtual {p0}, @FEATURE@->activeProfileId()Ljava/lang/String;
    move-result-object v0
    iget-object v1, p0, @FEATURE@->prefs:Landroid/content/SharedPreferences;
    invoke-static {v0, v1}, @HELPER@->adultLocked(Ljava/lang/String;Landroid/content/SharedPreferences;)Z
    move-result v0
    return v0
.end method
'''.lstrip().replace('@FEATURE@',FEATURE).replace('@HELPER@',HELPER)
    result=text.replace(before[signature],replacement,1)
    after=methods(result)
    assert set(before)==set(after)
    assert [key for key in before if before[key]!=after[key]]==[signature]
    strip=lambda s:re.sub(r'^\.method [^\n]+\n.*?^\.end method','',s,flags=re.M|re.S)
    assert strip(text)==strip(result),'Existing class fields/annotations must remain exact'
    assert hashlib.sha256(after['public profiles()Lorg/json/JSONArray;'].encode()).hexdigest()==budget['unchanged_public_profiles_sha256']
    return result
