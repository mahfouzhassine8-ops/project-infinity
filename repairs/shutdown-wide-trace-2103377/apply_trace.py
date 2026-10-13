"""Extend the preserved targeted tracer on the exact approved native source."""
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
import extend_trace

HERE=Path(__file__).resolve().parent
ACTIVITY='xbmc/platform/android/activity/'
HEADER=ACTIVITY+'InfinityVfsOpenTrace.h'
EXTRA_FILES=['xbmc/interfaces/legacy/LanguageHook.h','xbmc/interfaces/legacy/File.h',
             'xbmc/filesystem/FileCache.cpp','xbmc/interfaces/generic/LanguageInvokerThread.cpp',
             ACTIVITY+'InfinityAndroidCheckpoint.cpp']
GREEN_MAP_SHA='684b77fea120a7efa9fd0c11990f149fdabe3280fbac8f686dd99012dc929700'

def targeted():
    path=HERE.parent/'shutdown-vfs-trace-2103377/apply_trace.py'
    spec=importlib.util.spec_from_file_location('preserved_targeted_vfs',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

BASE_FILES=targeted().FILES
FILES=BASE_FILES+EXTRA_FILES
def sha(data):return hashlib.sha256(data).hexdigest()

def apply(root,expected):
    root=Path(root)
    assert len(expected)==9392
    assert sha(json.dumps(expected,sort_keys=True,separators=(',',':')).encode())==GREEN_MAP_SHA
    for name in FILES:assert sha((root/name).read_bytes())==expected[name],name
    original_logger=(root/(ACTIVITY+'InfinityShutdownTrace.h')).read_text()
    # Run the preserved functioning implementation first. The expansion has one
    # tracer instance, one existing export path and the same shutdown authority.
    original=targeted().apply(root,expected)
    for name in BASE_FILES:
        p=root/name
        p.write_text(extend_trace.metadata(original_logger) if name==ACTIVITY+'InfinityShutdownTrace.h'
                     else extend_trace.extend(name,p.read_text()))
    for name in EXTRA_FILES:
        p=root/name;p.write_text(extend_trace.additional(name,p.read_text()))
    shutil.copyfile(HERE/'InfinityVfsOpenTrace.h',root/HEADER)
    after=dict(original)
    for name in [*FILES,HEADER]:after[name]=sha((root/name).read_bytes())
    return after
