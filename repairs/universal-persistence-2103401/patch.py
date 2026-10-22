"""Apply only to the hash-verified, complete 2103401 native source inventory."""
from pathlib import Path
import argparse
import hashlib
import json

HERE = Path(__file__).resolve().parent
BASELINE = json.loads((HERE / 'BASELINE.json').read_text())
BRIDGE = 'xbmc/interfaces/python/InfinityPythonPersistence.h'
OBSERVER = 'xbmc/interfaces/python/InfinityPythonPersistenceSource.h'
LEDGER = 'xbmc/platform/android/activity/InfinityScriptPersistence.h'
WRITES = 'xbmc/platform/android/activity/InfinityProtectedWrites.h'
HOOKS = 'xbmc/interfaces/python/InfinityPythonWriteHooks.h'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def once(raw, old, new):
    if raw.count(old) != 1:
        raise ValueError('Missing or ambiguous exact source anchor: ' + repr(old[:100]))
    return raw.replace(old, new, 1)


def patches(before):
    if set(before) != set(BASELINE['before']):
        raise ValueError('Unexpected native source scope')
    for name, data in before.items():
        if sha(data) != BASELINE['before'][name]:
            raise ValueError('Native source preimage mismatch: ' + name)
    bridge = before[BRIDGE].decode()
    bridge = once(bridge, "    if(target[0]!='/')return {};\n    return target;",
        "    if(target[0]!='/')return {};\n"
        "    return InfinityScriptPersistence::VerifiedDescriptorLink(static_cast<int>(fd),target);")
    bridge = once(bridge, '  PyObject* rawWrite{nullptr};',
        '  PyObject* rawWrite{nullptr};\n  PyObject* vfsType{nullptr};\n  PyObject* vfsWrite{nullptr};')
    anchor = 'inline PyObject* Error(PyObject* self,PyObject* args)'
    bridge = once(bridge, anchor, (HERE / 'vfs_outcome.inc').read_text() + '\n' + anchor)
    bridge = once(bridge,
        '  static PyMethodDef errorMethod={"record_failure",Error,METH_VARARGS,nullptr};',
        '  static PyMethodDef vfsWriteMethod={"checked_vfs_write",CheckedVfsWrite,METH_VARARGS,nullptr};\n'
        '  static PyMethodDef errorMethod={"record_failure",Error,METH_VARARGS,nullptr};')
    bridge = once(bridge,
        '    context->observer=PyObject_CallFunctionObjArgs(klass,error,mutation,vfs,hostProbe,protection,context->admissionError,nullptr);',
        '    CaptureNativeVfsContract(context, vfs);\n'
        '    PyObject* vfsWrite=PyCFunction_NewEx(&vfsWriteMethod,capsule,nullptr);\n'
        '    if(vfsWrite) {\n'
        '      context->observer=PyObject_CallFunctionObjArgs(klass,error,mutation,vfs,hostProbe,protection,context->admissionError,vfsWrite,nullptr);\n'
        '      Py_DECREF(vfsWrite);\n'
        '    }')
    bridge = once(bridge, '  Py_CLEAR(context->rawWrite);Py_CLEAR(context->rawType);',
        '  Py_CLEAR(context->rawWrite);Py_CLEAR(context->rawType);\n'
        '  Py_CLEAR(context->vfsWrite);Py_CLEAR(context->vfsType);')
    bridge = once(bridge,
        'namespace InfinityPythonWriteHooks { inline PyObject* ActualDescriptor(PyObject* object,unsigned depth); }',
        'namespace InfinityPythonWriteHooks { inline PyObject* ActualDescriptor(PyObject* object,unsigned depth); inline bool VerifiedCleanIo(PyObject* object); }')
    bridge = once(bridge, 'struct Context\n{',
        'struct IoContract { PyObject* type{nullptr}; PyObject* methods[4]{}; };\n'
        'struct CleanIoReceipt { PyObject* weak{nullptr}; int fd{-1}; dev_t device{}; ino_t inode{}; mode_t mode{}; int flags{-1}; };\n'
        'struct Context\n{')
    bridge = once(bridge, '  PyObject* admissionError{nullptr};',
        '  PyObject* admissionError{nullptr};\n'
        '  std::vector<IoContract> ioContracts;\n'
        '  std::map<PyObject*,CleanIoReceipt> cleanIo;')
    bridge = once(bridge, '    paths.push_back(path);\n  }\n  Py_DECREF(sequence);',
        '    // A proven clean native handle needs no persistent write lease.\n'
        '    // New writes from callbacks still encounter the normal barrier.\n'
        '    if ((operation=="file.flush" || operation=="file.close" ||\n'
        '         operation=="buffer.flush" || operation=="buffer.close" ||\n'
        '         operation=="raw.flush" || operation=="raw.close") &&\n'
        '        InfinityPythonWriteHooks::VerifiedCleanIo(item))\n'
        '      path=InfinityScriptPersistence::NonPersistentTarget();\n'
        '    paths.push_back(path);\n  }\n  Py_DECREF(sequence);')
    bridge = once(bridge, '  InitializationStage(context,"complete");',
        '  if(!InfinityPythonWriteHooks::CaptureIoContracts(context))return failed();\n'
        '  InitializationStage(context,"complete");')
    bridge = once(bridge, '  Py_CLEAR(context->admissionError);',
        '  for(auto& item:context->cleanIo)Py_XDECREF(item.second.weak);\n'
        '  context->cleanIo.clear();\n'
        '  for(auto& contract:context->ioContracts) {\n'
        '    for(auto* method:contract.methods)Py_XDECREF(method);\n'
        '    Py_XDECREF(contract.type);\n'
        '  }\n'
        '  context->ioContracts.clear();\n'
        '  Py_CLEAR(context->admissionError);')
    observer = before[OBSERVER].decode()
    observer = once(observer,
        'def __init__(self, fail, touch, vfs=None, host_probe=False, protect=None, closed_error=None):',
        'def __init__(self, fail, touch, vfs=None, host_probe=False, protect=None, closed_error=None, native_vfs_write=None):')
    observer = once(observer, '        self.closed_error = closed_error',
        '        self.closed_error = closed_error\n        self.native_vfs_write = native_vfs_write')
    observer = once(observer,
        '                        handle = VFSFile(_original(path, mode), observer, translated)',
        '                        handle = VFSFile(_original(path, mode), observer, translated)\n'
        '                        # A writable VFS open may already truncate/create data.\n'
        '                        # Keep its drain obligation until checked native close.\n'
        '                        observer.buffer(handle, (translated,), True)')
    # The native callback dispatches AND classifies the same real callable. It
    # never accepts a Python claim that a TypeError means no data changed.
    observer = once(observer,
        "    @protected_method('vfs.write')\n    def write(self, value):\n        self.observer.check_live()\n",
        "    @protected_method('vfs.write')\n    def write(self, value):\n        self.observer.check_live()\n"
        '        if self.observer.native_vfs_write is not None:\n'
        '            return self.observer.native_vfs_write(self._infinity_handle, value)\n')
    ledger = once(before[LEDGER].decode(), '  std::set<std::string> paths;\n',
        '  std::set<std::string> paths;\n  std::set<std::string> removedNamespaces;\n')
    ledger = once(ledger, 'struct ProtectedResource\n{',
        'enum class NamespaceEffect { MAY_MUTATE, OBSERVED_CHILDREN };\nstruct ProtectedResource\n{')
    ledger = once(ledger, '  int descriptor{-1};\n};',
        '  int descriptor{-1};\n  NamespaceEffect namespaceEffect{NamespaceEffect::MAY_MUTATE};\n};')
    writes = before[WRITES].decode()
    writes = once(writes, 'bool existingTransaction = false, int descriptor = -1)\n{',
        'bool existingTransaction = false, int descriptor = -1,\n'
        '                                       NamespaceEffect effect = NamespaceEffect::MAY_MUTATE)\n{')
    writes = once(writes, '  resource.descriptor = descriptor;',
        '  resource.descriptor = descriptor;\n  resource.namespaceEffect = effect;')
    writes = once(writes,
        'bool nativeSave = false, bool existingTransaction = false, int descriptor = -1)\n'
        '    : m_token(BeginProtectedOperation(writer, paths, operation, nativeSave, existingTransaction, descriptor)) {}',
        'bool nativeSave = false, bool existingTransaction = false, int descriptor = -1,\n'
        '                     NamespaceEffect effect = NamespaceEffect::MAY_MUTATE)\n'
        '    : m_token(BeginProtectedOperation(writer, paths, operation, nativeSave, existingTransaction, descriptor, effect)) {}')
    writes = once(writes, 'inline std::string DescriptorPath(int fd)',
        (HERE/'descriptor_identity.inc').read_text()+'\ninline std::string DescriptorPath(int fd)')
    writes = once(writes, "  target[size] = '\\0'; return target;",
        "  target[size] = '\\0'; return VerifiedDescriptorLink(fd,target);")
    optional_start = writes.index('  for (const auto& root : p.profiles)\n', writes.index('inline bool OptionalBasePathLocked'))
    optional_end = writes.index('  return false;\n}\ninline bool OptionalPathLocked', optional_start)
    writes = writes[:optional_start] + (
        '  // An add-on identity or private profile folder does not prove that\n'
        '  // databases/history/provider state are recoverable. Only the\n'
        '  // coordinator\'s explicit cache roots may be optional.\n') + writes[optional_end:]
    writes = once(writes,
        '  p.transactions[key] = {-1, {path}, operation};',
        '  // Capture the actual native lease owner, including Python child threads.\n'
        '  p.transactions[key] = {CurrentWriteOwner(), {path}, operation};')
    anchor = 'inline EssentialWriteProof EssentialWritesLocked(State& s)'
    writes = once(writes, anchor,
        'inline std::string ResourceOwnerLocked(const State& s, const ProtectedResource& r)\n'
        '{\n'
        '  std::ostringstream out;\n'
        '  out << ";writer_id=" << r.writer << ";thread=" << r.thread\n'
        '      << ";checkpoint_generation=" << s.protection.generation << ";phase=" << s.protection.phase;\n'
        '  for(const auto& path:r.paths)out << ";target=" << (path.empty()?"<unresolved>":path.substr(0,768));\n'
        '  const auto writer=s.writers.find(r.writer);\n'
        '  if (writer!=s.writers.end()) {\n'
        '    out << ";interpreter=" << writer->second.initialization.interpreterIdentity;\n'
        '    for (const auto& name:writer->second.admissions) out << ";invocation=" << name.first;\n'
        '  }\n'
        '  return out.str();\n'
        '}\n' + anchor)
    writes = once(writes,
        '"active_protected_operation:" + entry.second.operation);',
        '"active_protected_operation:" + entry.second.operation + ";operation_id=" + std::to_string(entry.first) + ResourceOwnerLocked(s,entry.second));')
    writes = once(writes,
        '"unflushed_protected_buffer:" + entry.first);',
        '"unflushed_protected_buffer:" + entry.first + ResourceOwnerLocked(s,entry.second));')
    writes = once(writes,
        '"pending_protected_" + entry.second.operation + ":" + entry.first);',
        '"pending_protected_" + entry.second.operation + ":" + entry.first + ResourceOwnerLocked(s,entry.second));')
    writes = once(writes, '  const auto token = ++p.nextOperation;',
        '  // Coordination barriers retain admission and pending-owner protection.\n'
        '  // Their actual effects are observed by nested native leases and audit\n'
        '  // contracts; the barrier itself cannot invalidate a removed name.\n'
        '  // Unclassified operations still use MAY_MUTATE and fail closed.\n'
        '  if (effect == NamespaceEffect::MAY_MUTATE) {\n'
        '  // Any later admitted operation that overlaps a removed name revokes\n'
        '  // its earlier absence evidence, even when the new operation fails.\n'
        '  if (paths.empty()) p.removedNamespaces.clear();\n'
        '  // mkdir creates an empty directory (or fails without adding descendants);\n'
        '  // rmdir removes an empty directory. Neither can recreate an absent child.\n'
        '  // Exact/ancestor identities are still invalidated below.\n'
        '  bool preservesRemovedDescendants = operation == "rmdir" || operation == "namespace.rmdir" ||\n'
        '      operation == "mkdir" || operation == "namespace.mkdir";\n'
        '  if (operation == "converted_native_write_target") {\n'
        '    const auto parent=p.operations.find(protectedWriteToken);\n'
        '    preservesRemovedDescendants=parent!=p.operations.end() && parent->second.writer==id &&\n'
        '        parent->second.thread==std::this_thread::get_id() &&\n'
        '        (parent->second.operation=="rmdir" || parent->second.operation=="namespace.rmdir" ||\n'
        '         parent->second.operation=="mkdir" || parent->second.operation=="namespace.mkdir");\n'
        '  }\n'
        '  for (const auto& raw : paths) {\n'
        '    if (raw == NonPersistentTarget()) continue;\n'
        '    const auto path = Absolute(raw);\n'
        '    for (auto it=p.removedNamespaces.begin(); it!=p.removedNamespaces.end();)\n'
        '      if (path.empty() || Within(path,*it) || (!preservesRemovedDescendants && Within(*it,path))) it=p.removedNamespaces.erase(it);\n'
        '      else ++it;\n'
        '  }\n'
        '  }\n'
        '  const auto token = ++p.nextOperation;')
    writes = once(writes, 'inline bool SyncProtectedPath(const std::string& path,',
        (HERE/'namespace_outcome.inc').read_text()+'\ninline bool SyncProtectedPath(const std::string& path,')
    writes = once(writes,
        '                              const std::vector<std::string>& profiles)\n{\n  struct stat st{};',
        '                              const std::vector<std::string>& profiles,\n'
        '                              const std::set<std::string>& removed = {})\n{\n  struct stat st{};')
    writes = once(writes,
        'return errno == ENOENT && SyncRemovedInstallerStage(parent, path, profiles);',
        'return errno == ENOENT && (SyncRemovedNamespace(path, removed) ||\n'
        '                               SyncRemovedInstallerStage(parent, path, profiles));')
    writes = once(writes, '  std::vector<std::string> paths, profiles;',
        '  std::vector<std::string> paths, profiles;\n  std::set<std::string> removed;')
    writes = once(writes, '    profiles = p.profiles;',
        '    removed = p.removedNamespaces;\n    profiles = p.profiles;')
    writes = once(writes, '!SyncProtectedPath(canonical, profiles)',
        '!SyncProtectedPath(canonical, profiles, removed)')
    hooks = before[HOOKS].decode()
    hooks = once(hooks,
        'm_paths, Specs()[kind].original.ml_name, false, false, m_descriptor);',
        'm_paths, Specs()[kind].original.ml_name, false, false, m_descriptor,\n'
        '        kind==EXTENSION_CREATE ? Ledger::NamespaceEffect::OBSERVED_CHILDREN : Ledger::NamespaceEffect::MAY_MUTATE);')
    hooks = once(hooks, 'preparing(writer,{},"native_child_contract_preparation");',
        'preparing(writer,{},"native_child_contract_preparation",false,false,-1,\n'
        '      Ledger::NamespaceEffect::OBSERVED_CHILDREN);')
    hooks = once(hooks,
        '    if (result && m_kind == EXTENSION_CREATE && !ProtectNativeModule(result))',
        '    if (result && m_token && !m_paths.empty() &&\n'
        '        (m_kind == OS_RENAME || m_kind == OS_REPLACE || m_kind == OS_REMOVE ||\n'
        '         m_kind == OS_UNLINK || m_kind == OS_RMDIR))\n'
        '      Ledger::RecordRemovedNamespace(m_token,m_paths.front());\n'
        '    if (result && m_kind == EXTENSION_CREATE && !ProtectNativeModule(result))')
    hooks = once(hooks, 'inline bool DescriptorReader(PyObject* io, const char* typeName, unsigned index,',
        (HERE/'clean_io.inc').read_text()+'\ninline bool DescriptorReader(PyObject* io, const char* typeName, unsigned index,')
    hooks = once(hooks,
        'Call(Kind kind, PyObject* self, const Arguments& args) : m_kind(kind), m_context(Context())',
        'Call(Kind kind, PyObject* self, const Arguments& args) : m_kind(kind), m_context(Context()), m_object(self)')
    hooks = once(hooks, '  InfinityPythonPersistence::Context* m_context;',
        '  InfinityPythonPersistence::Context* m_context;\n  PyObject* m_object;')
    hooks = once(hooks, '    const int writer = m_context ? m_context->id : -1;',
        '    if ((kind==BUFFER_FLUSH || kind==BUFFER_CLOSE || kind==TEXT_FLUSH || kind==TEXT_CLOSE) &&\n'
        '        VerifiedCleanIo(self))m_paths={Ledger::NonPersistentTarget()};\n'
        '    const int writer = m_context ? m_context->id : -1;')
    hooks = once(hooks,
        '    if (std::find(m_paths.begin(), m_paths.end(), "") != m_paths.end()) m_paths.clear();',
        '    std::string unresolved;\n'
        '    if (kind>=RAW_WRITE && !Ledger::VerifiedBufferNamespaceTransition(\n'
        '        writer,m_key,m_descriptor,m_paths,unresolved)) {\n'
        '      Ledger::Fail(writer,"unverified_dirty_buffer_namespace",\n'
        '          "operation="+std::string(Specs()[kind].original.ml_name)+";target="+unresolved.substr(0,768));\n'
        '      InfinityPythonPersistence::AdmissionDenied(m_context,"Infinity dirty buffer namespace is unverified");\n'
        '      return;\n'
        '    }\n'
        '    if (std::find(m_paths.begin(), m_paths.end(), "") != m_paths.end()) m_paths.clear();')
    hooks = once(hooks,
        '      Ledger::SetProtectedBuffer(writer, m_key, m_paths, true);',
        '    { ForgetCleanIo(self); Ledger::SetProtectedBuffer(writer, m_key, m_paths, true); }')
    hooks = once(hooks, '    return result;\n  }\nprivate:',
        '    if (result && (m_kind==BUFFER_FLUSH || m_kind==TEXT_FLUSH))RecordCleanIo(m_object);\n'
        '    if (result && (m_kind==BUFFER_CLOSE || m_kind==TEXT_CLOSE || m_kind==RAW_CLOSE))ForgetCleanIo(m_object);\n'
        '    if (result && m_kind==IO_OPEN)RecordCleanIo(result);\n'
        '    return result;\n  }\nprivate:')
    hooks = once(hooks, '  return RawInitializer()(self, tuple, dictionary);',
        '  const int result=RawInitializer()(self, tuple, dictionary);\n'
        '  if(result==0)RecordCleanIo(self);\n'
        '  return result;')
    return {BRIDGE: bridge.encode(), OBSERVER: observer.encode(),
            LEDGER: ledger.encode(), WRITES: writes.encode(), HOOKS: hooks.encode()}


def apply(source, source_map, output):
    expected = json.loads(source_map.read_text())
    if len(expected) != BASELINE['source_count'] or sha(json.dumps(
            expected, sort_keys=True, separators=(',', ':')).encode()) != BASELINE['source_map_sha256']:
        raise ValueError('Complete matching 2103401 source map required')
    for name, pin in expected.items():
        if sha((source / name).read_bytes()) != pin:
            raise ValueError('Source drift: ' + name)
    after = patches({name: (source / name).read_bytes() for name in BASELINE['before']})
    output.mkdir(parents=True, exist_ok=False)
    for name, data in after.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    proof = dict(before=BASELINE['before'], after={n: sha(b) for n, b in after.items()},
        native_source_count=len(expected), other_native_inputs_unchanged=len(expected)-len(after),
        native_source_only=True, signed_apk_created=False, android_validated=False,
        physical_fold_verified=False, final_lock=False)
    (output / 'SOURCE-DELTA.json').write_text(json.dumps(proof, indent=2) + '\n')
    return proof


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--source-map', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(apply(args.source, args.source_map, args.output), indent=2))
