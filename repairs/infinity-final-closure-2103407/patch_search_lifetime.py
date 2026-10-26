"""Repair the proven Search consumer/worker ownership race from exact signed407."""
import ast
import hashlib
from pathlib import Path
import sys

BASELINE_SHA = "bb6e8791ca7644ca9d370b5871d69ded71790557069b56535e920baa6cf50531"
REPLACEMENT = "def _leased_directory(path,home,progress=None):\n    \"\"\"Keep the original native lease and the actual RPC worker's capacity.\n\n    A failing consumer callback must not release capacity while native work\n    remains alive. Only its real RPC worker retires an admission after start;\n    this invoker retains ownership of its request/cancel/result token cleanup.\n    \"\"\"\n    admission = _native_search_admission() if path.startswith('plugin://plugin.video.') else False\n    if admission is None:\n        return 'busy', {'error': {'message': 'A previous Infinity Search is still active'}}\n    worker=None\n    keys=[]\n    cancel_sent=False\n    try:\n        token=uuid.uuid4().hex\n        keys=['Infinity.Search.'+part+token for part in ('Request.','Cancel.','Result.')]\n        output=[]\n        def request():\n            try:\n                try:output.append(rpc('Files.GetDirectory',dict(directory=path+'|infinity_search='+token,media='video',\n                                    properties=PROPERTIES,limits={'start':0,'end':MAX_RESULTS})))\n                except (ValueError,RuntimeError):output.append({'error':{'message':'provider_failed'}})\n            finally:\n                # The worker owns capacity even if its submitting interpreter's\n                # GUI callback, cancellation check or token cleanup raises.\n                if admission:\n                    admission.close()\n        worker=threading.Thread(target=request,name='InfinitySearchResult')\n        monitor=xbmc.Monitor()\n        home.setProperty(keys[0],hashlib.sha256(path.encode('utf-8')).hexdigest())\n        worker.start()\n        while worker.is_alive():\n            if not cancel_sent and (monitor.abortRequested() or (progress is not None and progress.iscanceled())):\n                home.setProperty(keys[1],'1')\n                cancel_sent=True\n            worker.join(.05)\n        status=home.getProperty(keys[2])\n        return status,output[0] if output else {'error':{}}\n    finally:\n        try:\n            if worker is not None and worker.ident is not None and worker.is_alive():\n                # On exceptional consumer exit, request native cancellation once\n                # and retain this original worker until it actually retires.\n                # Never force-kill a provider or clear its live request token.\n                if not cancel_sent:\n                    try:\n                        home.setProperty(keys[1],'1')\n                    except Exception:\n                        pass  # The existing native lease still owns retirement.\n                worker.join()\n            cleanup_error=None\n            for key in keys:\n                try:\n                    home.clearProperty(key)\n                except Exception as error:\n                    if cleanup_error is None:\n                        cleanup_error=error\n            if cleanup_error is not None:\n                raise cleanup_error\n        finally:\n            # No worker was launched: this invoker still owns the descriptor.\n            # A started worker closes it itself, including exceptional RPC exit.\n            if admission and (worker is None or worker.ident is None):\n                admission.close()\n"

def patch(raw):
    if hashlib.sha256(raw).hexdigest() != BASELINE_SHA:
        raise ValueError("Exact signed407 Search source required")
    text = raw.decode("utf-8")
    tree = ast.parse(text)
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_leased_directory"]
    if len(nodes) != 1:
        raise ValueError("Expected one reviewed native Search consumer")
    node = nodes[0]
    lines = text.splitlines(keepends=True)
    before = "".join(lines[node.lineno-1:node.end_lineno])
    result = "".join(lines[:node.lineno-1]) + REPLACEMENT + "".join(lines[node.end_lineno:])
    if result.replace(REPLACEMENT, before, 1) != text:
        raise ValueError("Unrelated Search bytes changed")
    compile(result, "infinity_search.py", "exec")
    return result.encode("utf-8")

if __name__ == "__main__":
    source, output = map(Path, sys.argv[1:])
    if output.exists():
        raise ValueError("Refuse to replace an existing staged candidate")
    candidate = patch(source.read_bytes())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(candidate)
    print("STAGED_SEARCH_SHA256", hashlib.sha256(candidate).hexdigest())
