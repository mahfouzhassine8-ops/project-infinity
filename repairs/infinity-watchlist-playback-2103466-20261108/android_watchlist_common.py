"""Host-only reuse of retained, selected helpers; never invokes either old main."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import types

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RETAINED = '2f18336ec766cf6e0234ecf7e9727ab4993247ff'
CC = 'script.infinity.commandcenter'
QA = 'script.infinity.finalreleaseqa'
PACKAGE = 'com.projectinfinity.kodi'
HOME = '/sdcard/Android/data/' + PACKAGE + '/files/.kodi'
PROFILE = HOME + '/userdata'
QAROOT = PROFILE + '/addon_data/' + QA


def retained(path):
    return subprocess.check_output(['git', 'show', RETAINED + ':' + path], cwd=ROOT)


def selected_function(path, name, namespace):
    source = retained(path)
    tree = ast.parse(source)
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(nodes) != 1:
        raise RuntimeError('Exact retained function missing: ' + name)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), path, 'exec'), namespace)
    return namespace[name]


def checked_observer(source):
    return selected_function('repairs/infinity-three-corrections-20261108/stage_three_android.py',
                             'checked_observer', {'ast': ast})(source)


def device_class():
    # Supply the unchanged measured OS tutorial helper to the retained Device import.
    # Its historical image self-test/main is not executed.
    import io, os, re, time
    from PIL import Image
    module = types.ModuleType('immersive_prompt')
    module.__dict__.update(io=io, json=json, os=os, re=re, subprocess=subprocess, time=time, Image=Image)
    module.locate = selected_function('repairs/infinity-preview-2103450-fullscreen-display/android-qa/immersive_prompt.py',
                                     'locate', module.__dict__)
    sys.modules['immersive_prompt'] = module
    # Only the retained transport factory executes; neither broad run/main is loaded.
    namespace = dict(subprocess=subprocess, HERE=ROOT / 'repairs/infinity-three-corrections-20261108',
                     ROOT=ROOT, OLD=ROOT / 'repairs/infinity-final-release-462-20261107',
                     PROVIDERS={'plugin.video.pov', 'plugin.video.umbrella'}, QA=QA, QAROOT=QAROOT)
    return selected_function('repairs/infinity-three-corrections-20261108/verify_three_android.py',
                             'transport', namespace)()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def producer_pins():
    tree = ast.parse((HERE / 'overlay' / CC / 'saved_playback.py').read_text())
    return next(ast.literal_eval(node.value) for node in tree.body
                if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'PRODUCERS' for t in node.targets))
