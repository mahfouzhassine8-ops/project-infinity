// Called only inside the existing Infinity interpreter observer. Do not patch
// Kodi's shared argument converter, VFS implementation or provider modules.
inline PyObject* CheckedVfsWrite(PyObject* self, PyObject* args)
{
  auto* context = Capsule(self);
  PyObject *handle = nullptr, *value = nullptr;
  if (!context || !PyArg_ParseTuple(args, "OO", &handle, &value)) return nullptr;
  const auto found = Contexts().find(PyThreadState_Get()->interp);
  if (found == Contexts().end() || found->second != context)
  {
    PyErr_SetString(PyExc_RuntimeError, "VFS observer interpreter ownership mismatch");
    return nullptr;
  }

  // Capture and invoke the same callable. Only the original static Kodi File
  // type and its original C method can establish the conversion contract.
  // A Python override, subclass, replacement or unknown extension gets no proof.
  PyObject* method = PyObject_GetAttrString(handle, "write");
  bool nativeMethod = method && context->vfsType && context->vfsWrite &&
      Py_TYPE(handle) == reinterpret_cast<PyTypeObject*>(context->vfsType) &&
      PyCFunction_Check(method) && PyCFunction_GetSelf(method) == handle;
  if (nativeMethod)
  {
    const auto* definition = reinterpret_cast<PyMethodDescrObject*>(context->vfsWrite)->d_method;
    nativeMethod = PyCFunction_GetFunction(method) == definition->ml_meth &&
        PyCFunction_GetFlags(method) == definition->ml_flags;
  }
  const bool invalidBuffer = !PyUnicode_Check(value) && !PyBytes_Check(value) &&
      !PyByteArray_Check(value);

  uint64_t operation = 0, generation = 0;
  std::string target;
  {
    auto& state = InfinityScriptPersistence::Get();
    std::lock_guard<std::mutex> lock(state.mutex);
    for (const auto& item : state.protection.operations)
    {
      const auto& lease = item.second;
      if (lease.writer != context->id || lease.thread != std::this_thread::get_id() ||
          lease.operation != "vfs.write") continue;
      // Nested/ambiguous leases never establish no-mutation proof.
      if (operation) { operation = 0; target.clear(); break; }
      operation = item.first;
      if (lease.paths.size() == 1) target = lease.paths.front();
    }
    generation = state.protection.generation;
  }
  PyObject* result = method ? PyObject_CallFunctionObjArgs(method, value, nullptr) : nullptr;
  Py_XDECREF(method);
  if (result == Py_True) return result;

  // Preserve exactly the original result, pending exception and errno. Neither
  // a rejection nor a failed/partial write is a successful save receipt.
  const int savedErrno = errno;
  PyObject *type = nullptr, *error = nullptr, *trace = nullptr;
  PyErr_Fetch(&type, &error, &trace);
  const bool rejected = !result && type == PyExc_TypeError && nativeMethod &&
      invalidBuffer && operation != 0;
  const char* reason = result ? "vfs_write_failed" : "vfs_write_exception";
  const std::string detail = "value_type=" + std::string(Py_TYPE(value)->tp_name).substr(0, 80) +
      ";exception=" + (type && PyType_Check(type) ?
          std::string(reinterpret_cast<PyTypeObject*>(type)->tp_name).substr(0, 80) : "<none>") +
      ";operation_id=" + std::to_string(operation) +
      ";checkpoint_generation=" + std::to_string(generation) +
      ";effect=" + (rejected ? "argument_rejected_before_native_write" : "unverified");
  bool recorded = false;
  if (rejected)
  {
    auto& state = InfinityScriptPersistence::Get();
    std::lock_guard<std::mutex> lock(state.mutex);
    const auto live = state.protection.operations.find(operation);
    const auto writer = state.writers.find(context->id);
    if (live != state.protection.operations.end() && writer != state.writers.end() &&
        live->second.writer == context->id && live->second.thread == std::this_thread::get_id() &&
        live->second.operation == "vfs.write" && state.protection.generation == generation)
    {
      // Direct native evidence; this reason is NOT added to the generic
      // AdvisoryFailureReason allowlist. Python cannot assert this proof.
      std::string name;
      for (const auto& admission : writer->second.admissions)
      { if (!name.empty()) name += ","; name += admission.first; }
      InfinityScriptPersistence::AddBlockerLocked(state, context->id, name,
          reason, detail, false);
      recorded = true;
    }
  }
  if (!recorded)
  {
    const auto verified = InfinityScriptPersistence::VerifiedVfsWriteFailureTarget(
        context->id, "vfs.write", target);
    InfinityScriptPersistence::Fail(context->id, reason, detail, verified);
  }
  PyErr_Restore(type, error, trace);
  errno = savedErrno;
  return result;
}

inline void CaptureNativeVfsContract(Context* context, PyObject* vfs)
{
  if (!vfs || vfs == Py_None) return;
  PyObject* type = PyObject_GetAttrString(vfs, "File");
  if (!type) { PyErr_Clear(); return; }
  if (PyType_Check(type) &&
      !(reinterpret_cast<PyTypeObject*>(type)->tp_flags & Py_TPFLAGS_HEAPTYPE) &&
      std::strcmp(reinterpret_cast<PyTypeObject*>(type)->tp_name, "xbmcvfs.File") == 0)
  {
    PyObject* method = PyObject_GetAttrString(type, "write");
    if (method && Py_TYPE(method) == &PyMethodDescr_Type &&
        PyDescr_TYPE(method) == reinterpret_cast<PyTypeObject*>(type))
    { context->vfsType = type; context->vfsWrite = method; return; }
    Py_XDECREF(method);
    PyErr_Clear();
  }
  Py_DECREF(type);
}
