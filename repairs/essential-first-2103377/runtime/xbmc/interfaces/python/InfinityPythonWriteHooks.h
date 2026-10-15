/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once
// Included after Context/Path definitions, with the GIL held at installation.
// These native entry points also cover function/method aliases cached BEFORE
// the Python observer was installed. Rebinding os.write alone cannot do that.
#if PY_MAJOR_VERSION != 3 || PY_MINOR_VERSION != 11
#error "Infinity native write hooks require the pinned CPython 3.11 ABI"
#endif
#include <array>
#include <cstring>
#include <vector>
#include <sys/file.h>

namespace InfinityPythonWriteHooks
{
namespace Ledger = InfinityScriptPersistence;
enum Kind
{
  OS_WRITE, OS_WRITEV, OS_PWRITE, OS_PWRITEV, OS_FTRUNCATE, OS_TRUNCATE,
  OS_SENDFILE, OS_COPY, OS_OPEN, OS_RENAME, OS_REPLACE, OS_UNLINK, OS_REMOVE,
  OS_MKDIR, OS_RMDIR, OS_MKFIFO, OS_MKNOD, OS_FALLOCATE, OS_SPLICE,
  OS_CLOSE, OS_CLOSERANGE, OS_DUP, OS_DUP2, FILE_FLOCK, IO_OPEN, EXTENSION_CREATE, PIL_DESCRIPTOR_WRITE, PIL_PATH_WRITE,
  RAW_WRITE, RAW_TRUNCATE, RAW_CLOSE,
  BUFFER_WRITE, BUFFER_TRUNCATE, BUFFER_FLUSH, BUFFER_CLOSE,
  TEXT_WRITE, TEXT_TRUNCATE, TEXT_FLUSH, TEXT_CLOSE, FORK_EXEC, COUNT
};
struct Spec
{
  PyMethodDef original{};
  PyMethodDef replacement{};
  bool installed{false};
};
inline std::array<Spec, COUNT>& Specs()
{ static auto* specs = new std::array<Spec, COUNT>; return *specs; }
inline bool ProtectNativeModule(PyObject* module);
inline InfinityPythonPersistence::Context* Context();
inline std::array<PyCFunction, 3>& DescriptorReaders()
{ static std::array<PyCFunction, 3> readers{}; return readers; }
inline std::array<PyTypeObject*, 6>& IOTypes()
{ static std::array<PyTypeObject*, 6> types{}; return types; }
inline bool RememberIOTypes(PyObject* io)
{
  const char* names[]{"FileIO","BufferedWriter","BufferedRandom","BufferedReader","TextIOWrapper","BytesIO"};
  for (unsigned i = 0; i < 6; ++i)
  {
    auto* object = PyObject_GetAttrString(io,names[i]);
    if (!object || !PyType_Check(object)) { Py_XDECREF(object); return false; }
    auto* type = reinterpret_cast<PyTypeObject*>(object);
    if (!IOTypes()[i]) IOTypes()[i] = type; // Retain the actual pinned native type.
    else { Py_DECREF(object); if (IOTypes()[i] != type) return false; }
  }
  return true;
}
inline PyObject* NativeField(PyObject* object, PyTypeObject* type, const char* name)
{
  auto* descriptor = PyObject_GetAttrString(reinterpret_cast<PyObject*>(type),name);
  if (!descriptor) return nullptr;
  PyObject* result = nullptr;
  if ((Py_IS_TYPE(descriptor,&PyGetSetDescr_Type) || Py_IS_TYPE(descriptor,&PyMemberDescr_Type)) &&
      Py_TYPE(descriptor)->tp_descr_get)
    result = Py_TYPE(descriptor)->tp_descr_get(descriptor,object,reinterpret_cast<PyObject*>(Py_TYPE(object)));
  Py_DECREF(descriptor); return result;
}
inline PyObject* ActualDescriptor(PyObject* object, unsigned depth = 0)
{
  if (depth > 4) return nullptr;
  if (Py_IS_TYPE(object,IOTypes()[5])) return PyUnicode_FromString(":nonpersistent:");
  if (PyObject_TypeCheck(object,IOTypes()[0]))
  {
    if (depth)
    {
      auto* actual = PyObject_GetAttrString(reinterpret_cast<PyObject*>(Py_TYPE(object)),"write");
      auto* builtin = PyObject_GetAttrString(reinterpret_cast<PyObject*>(IOTypes()[0]),"write");
      auto* context = Context();
      bool direct = actual && builtin && (actual == builtin ||
          (context && reinterpret_cast<PyObject*>(Py_TYPE(object)) == context->rawType && actual == context->rawWrite));
      Py_XDECREF(actual); Py_XDECREF(builtin);
      direct = direct && Py_TYPE(object)->tp_getattro == IOTypes()[0]->tp_getattro;
      if (direct && Py_TYPE(object)->tp_dictoffset)
      {
        auto* dictionary = PyObject_GenericGetDict(object,nullptr);
        direct = dictionary && !PyDict_GetItemString(dictionary,"write");
        Py_XDECREF(dictionary);
      }
      if (!direct) return nullptr; // An arbitrary Python raw writer has unknown effects.
    }
    return DescriptorReaders()[0](object,nullptr);
  }
  for (unsigned i = 1; i <= 4; ++i)
    if (PyObject_TypeCheck(object,IOTypes()[i]))
    {
      auto* next = NativeField(object,IOTypes()[i],i == 4 ? "buffer" : "raw");
      if (!next) return nullptr;
      auto* result = ActualDescriptor(next,depth+1);
      Py_DECREF(next); return result;
    }
  return nullptr;
}
inline bool DescriptorReader(PyObject* io, const char* typeName, unsigned index)
{
  auto* type = PyObject_GetAttrString(io, typeName);
  auto* member = type ? PyObject_GetAttrString(type, "fileno") : nullptr;
  bool ok = member && Py_IS_TYPE(member, &PyMethodDescr_Type);
  if (ok)
  {
    auto* method = reinterpret_cast<PyMethodDescrObject*>(member)->d_method;
    ok = method->ml_flags == METH_NOARGS;
    if (ok) DescriptorReaders()[index] = method->ml_meth;
  }
  Py_XDECREF(member); Py_XDECREF(type); return ok;
}
inline InfinityPythonPersistence::Context* Context()
{
  auto* thread = PyThreadState_Get();
  const auto found = InfinityPythonPersistence::Contexts().find(thread->interp);
  return found == InfinityPythonPersistence::Contexts().end() ? nullptr : found->second;
}
struct Arguments
{
  PyObject* const* values;
  Py_ssize_t count;
  PyObject* keywords;
  PyObject* dictionary;
  PyObject* At(Py_ssize_t position, const char* name = nullptr) const
  {
    if (position >= 0 && position < count) return values[position];
    if (!name) return nullptr;
    if (dictionary) return PyDict_GetItemString(dictionary, name);
    if (keywords)
      for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(keywords); ++i)
        if (PyUnicode_CompareWithASCIIString(PyTuple_GET_ITEM(keywords, i), name) == 0)
          return values[count + i];
    return nullptr;
  }
};
inline std::string Target(PyObject* object, PyObject* directory = nullptr)
{
  if (!object) return {};
  if (PyLong_Check(object))
  {
    const long fd = PyLong_AsLong(object);
    if (PyErr_Occurred()) { PyErr_Clear(); return {}; }
    return Ledger::DescriptorPath(static_cast<int>(fd));
  }
  // Do not call an arbitrary __fspath__ twice. The actual converted target is
  // supplied by the native audit event inside this operation's live lease.
  if (!PyUnicode_Check(object) && !PyBytes_Check(object)) return {};
  return InfinityPythonPersistence::PathAt(object, directory);
}
inline bool WritesOpen(Kind kind, const Arguments& args)
{
  if (kind == OS_OPEN)
  {
    auto* value = args.At(1, "flags");
    if (!value || !PyLong_Check(value)) return true;
    const long flags = PyLong_AsLong(value);
    if (PyErr_Occurred()) { PyErr_Clear(); return true; }
    return flags & (O_WRONLY | O_RDWR | O_CREAT | O_TRUNC | O_APPEND);
  }
  if (kind == IO_OPEN)
  {
    auto* mode = args.At(1, "mode");
    if (!mode) return false;
    if (!PyUnicode_Check(mode)) return true;
    const char* text = PyUnicode_AsUTF8(mode);
    return text && std::strpbrk(text, "wax+");
  }
  return true;
}
class Call
{
public:
  Call(Kind kind, PyObject* self, const Arguments& args) : m_kind(kind), m_context(Context())
  {
    if (!WritesOpen(kind, args)) { m_allowed = true; return; }
    if (kind == EXTENSION_CREATE)
      m_paths.clear(); // Covers the complete native import and hook installation.
    else if (kind >= RAW_WRITE)
    {
      // The native descriptor lives on the built-in object, including buffers
      // created by cached _io.open. Keep any pre-existing exception intact.
      PyObject *type = nullptr, *value = nullptr, *trace = nullptr;
      PyErr_Fetch(&type, &value, &trace);
      // Invoke the actual built-in descriptor reader. A subclass's fileno()
      // override must not classify a protected FileIO handle as private cache.
      auto* descriptor = ActualDescriptor(self);
      if (descriptor) { m_paths.push_back(Target(descriptor)); if (PyLong_Check(descriptor)) m_descriptor = static_cast<int>(PyLong_AsLong(descriptor)); Py_DECREF(descriptor); }
      else
      {
        PyErr_Clear();
        auto* closed = PyObject_GetAttrString(self, "closed");
        const bool alreadyClosed = closed && PyObject_IsTrue(closed) == 1;
        Py_XDECREF(closed); PyErr_Clear();
        if (alreadyClosed)
        { PyErr_Restore(type, value, trace); m_allowed = true; return; }
        m_paths.push_back(""); // A failed fileno is uncertainty, never a waiver.
      }
      PyErr_Restore(type, value, trace);
      m_key = "native-buffer:" + std::to_string(reinterpret_cast<uintptr_t>(self));
    }
    else if (kind == OS_RENAME || kind == OS_REPLACE)
      m_paths = {Target(args.At(0, "src"), args.At(-1, "src_dir_fd")),
                 Target(args.At(1, "dst"), args.At(-1, "dst_dir_fd"))};
    else if (kind == OS_DUP2)
    {
      auto destination = Target(args.At(1, "fd2"));
      // dup2 may legally allocate a currently unused descriptor number.
      if (destination.empty() && args.At(1,"fd2") && PyLong_Check(args.At(1,"fd2"))) destination = ":nonpersistent:";
      m_paths = {Target(args.At(0, "fd")), destination};
    }
    else
    {
      auto* target = args.At(kind == OS_COPY || kind == OS_SPLICE ? 1 : 0,
          kind == IO_OPEN ? "file" : kind == OS_COPY || kind == OS_SPLICE ? "dst" : kind == OS_SENDFILE ? "out_fd" : "path");
      m_paths = {Target(target, args.At(-1, "dir_fd"))};
      if (target && PyLong_Check(target)) m_descriptor = static_cast<int>(PyLong_AsLong(target));
    }
    const int writer = m_context ? m_context->id : -1;
    // Unbuffered close changes descriptor identity, not file contents. Do not
    // invent dirty files merely because a read-only module file was closed.
    if (kind == OS_CLOSE || kind == OS_CLOSERANGE || kind == RAW_CLOSE) m_paths = {":nonpersistent:"};
    if (kind == FILE_FLOCK)
    {
      auto* value = args.At(1,"operation");
      if (value && PyLong_Check(value)) m_lockOperation = static_cast<int>(PyLong_AsLong(value));
      if (m_lockOperation & LOCK_UN) m_paths = {":nonpersistent:"};
    }
    if (std::find(m_paths.begin(), m_paths.end(), "") != m_paths.end()) m_paths.clear();
    m_token = Ledger::BeginProtectedOperation(writer, m_paths, Specs()[kind].original.ml_name, false, false, m_descriptor);
    m_allowed = m_token != 0;
    if (!m_allowed) { InfinityPythonPersistence::AdmissionDenied(m_context, "Infinity protected write admission is closed"); return; }
    m_previousOwner = Ledger::protectedWriteOwner;
    Ledger::protectedWriteOwner = writer;
    m_previousToken = Ledger::protectedWriteToken;
    Ledger::protectedWriteToken = m_token;
    if (m_context) ++m_context->nativeProtectionDepth[PyThreadState_Get()];
    if (m_context && kind == EXTENSION_CREATE) ++m_context->nativeExtensionDepth[PyThreadState_Get()];
    if (kind == OS_CLOSE || kind == RAW_CLOSE) Ledger::InvalidateDescriptor(m_descriptor, m_token);
    if (kind == OS_CLOSERANGE)
    {
      auto* first = args.At(0,"fd_low"); auto* last = args.At(1,"fd_high");
      if (first && last && PyLong_Check(first) && PyLong_Check(last))
        Ledger::InvalidateDescriptorRange(static_cast<int>(PyLong_AsLong(first)),static_cast<int>(PyLong_AsLong(last)));
      else Ledger::InvalidateDescriptorRange(0,INT_MAX);
    }
    if (kind == OS_DUP2)
    {
      auto* target = args.At(1,"fd2");
      if (target && PyLong_Check(target)) Ledger::InvalidateDescriptor(static_cast<int>(PyLong_AsLong(target)));
    }
    if (kind == BUFFER_WRITE || kind == BUFFER_TRUNCATE || kind == TEXT_WRITE || kind == TEXT_TRUNCATE)
      Ledger::SetProtectedBuffer(writer, m_key, m_paths, true);
  }
  ~Call()
  {
    if (!m_token) return;
    if (m_context) --m_context->nativeProtectionDepth[PyThreadState_Get()];
    if (m_context && m_kind == EXTENSION_CREATE) --m_context->nativeExtensionDepth[PyThreadState_Get()];
    Ledger::protectedWriteOwner = m_previousOwner;
    Ledger::protectedWriteToken = m_previousToken;
    Ledger::EndProtectedOperation(m_token);
  }
  explicit operator bool() const { return m_allowed; }
  PyObject* Finish(PyObject* result)
  {
    if (m_token && m_kind == IO_OPEN && m_paths.empty() && result)
    {
      // _io.open may delegate its converted argument to FileIO's nested
      // initializer. Resolve the returned native handle while the enclosing
      // unknown-target lease still prevents sealing. Do not call __fspath__
      // again or trust an overridable Python fileno().
      auto* descriptor = ActualDescriptor(result);
      if (descriptor)
      { Ledger::RecordProtectedResult(m_token,Target(descriptor)); Py_DECREF(descriptor); }
      else
      { PyErr_Clear(); Ledger::ProtectionFailure("completed_native_write_target_unconfirmed"); }
    }
    // PathLike arguments may be resolved by a native audit event. Calls such
    // as write(custom_index_object, ...) have no converted-target audit event;
    // never drop that uncertainty merely because the operation returned.
    if (m_token && m_kind != EXTENSION_CREATE && m_paths.empty())
      Ledger::RequireProtectedIdentity(m_token);
    if (result && m_kind == FILE_FLOCK)
    {
      if (m_descriptor < 0 || m_paths.empty())
        Ledger::ProtectionFailure("unresolved_native_file_lock_identity");
      else Ledger::SetProtectedTransaction("flock:"+std::to_string(m_descriptor), m_paths.front(),
          (m_lockOperation & LOCK_EX) && !(m_lockOperation & LOCK_UN), "file_lock_transaction");
    }
    if (result && (m_kind == OS_RENAME || m_kind == OS_REPLACE || m_kind == OS_DUP2) && m_paths.size() == 2)
      Ledger::RememberAlias(m_paths[0], m_paths[1]);
    if (result && m_kind == EXTENSION_CREATE && !ProtectNativeModule(result))
    {
      Ledger::ProtectionFailure("bundled_native_encoder_write_adapter_missing");
      Py_DECREF(result);
      if (!PyErr_Occurred()) PyErr_SetString(PyExc_RuntimeError,"Infinity native encoder protection installation failed");
      return nullptr;
    }
    if (result && m_token && (m_kind == BUFFER_FLUSH || m_kind == BUFFER_CLOSE ||
                              m_kind == TEXT_FLUSH || m_kind == TEXT_CLOSE))
      Ledger::SetProtectedBuffer(m_context ? m_context->id : -1, m_key, m_paths, false);
    return result;
  }
private:
  Kind m_kind;
  InfinityPythonPersistence::Context* m_context;
  uint64_t m_token{0};
  uint64_t m_previousToken{0};
  bool m_allowed{false};
  int m_previousOwner{-1};
  int m_descriptor{-1};
  int m_lockOperation{0};
  std::vector<std::string> m_paths;
  std::string m_key;
};
template<Kind kind> PyObject* Fast(PyObject* self, PyObject* const* values, Py_ssize_t count)
{
  Call call(kind, self, {values, count, nullptr, nullptr}); if (!call) return nullptr;
  return call.Finish(reinterpret_cast<_PyCFunctionFast>(reinterpret_cast<void(*)(void)>(Specs()[kind].original.ml_meth))(self, values, count));
}
template<Kind kind> PyObject* FastKeywords(PyObject* self, PyObject* const* values, Py_ssize_t count, PyObject* names)
{
  Call call(kind, self, {values, count, names, nullptr}); if (!call) return nullptr;
  return call.Finish(reinterpret_cast<_PyCFunctionFastWithKeywords>(reinterpret_cast<void(*)(void)>(Specs()[kind].original.ml_meth))(self, values, count, names));
}
template<Kind kind> PyObject* Single(PyObject* self, PyObject* value)
{
  PyObject* values[]{value};
  Call call(kind, self, {values, value ? 1 : 0, nullptr, nullptr}); if (!call) return nullptr;
  return call.Finish(Specs()[kind].original.ml_meth(self, value));
}
template<Kind kind> PyObject* VarArgs(PyObject* self, PyObject* tuple)
{
  const auto count = PyTuple_GET_SIZE(tuple);
  std::vector<PyObject*> values;
  for (Py_ssize_t i = 0; i < count; ++i) values.push_back(PyTuple_GET_ITEM(tuple, i));
  Call call(kind, self, {values.data(), count, nullptr, nullptr}); if (!call) return nullptr;
  return call.Finish(Specs()[kind].original.ml_meth(self, tuple));
}
template<Kind kind> PyObject* Keywords(PyObject* self, PyObject* tuple, PyObject* keywords)
{
  const auto count = PyTuple_GET_SIZE(tuple);
  std::vector<PyObject*> values;
  for (Py_ssize_t i = 0; i < count; ++i) values.push_back(PyTuple_GET_ITEM(tuple, i));
  Call call(kind, self, {values.data(), count, nullptr, keywords}); if (!call) return nullptr;
  return call.Finish(reinterpret_cast<PyCFunctionWithKeywords>(reinterpret_cast<void(*)(void)>(Specs()[kind].original.ml_meth))(self, tuple, keywords));
}
inline PyObject* ForkExec(PyObject* self, PyObject* tuple)
{
  auto* context = Context();
  const int writer = context ? context->id : -1;
  if (!context || !context->readonlyChildren[PyThreadState_Get()])
  {
    Ledger::Fail(writer, "unobserved_native_child_process");
    if (Ledger::RejectOpaqueMutation("native_child_process"))
    { InfinityPythonPersistence::AdmissionDenied(context,"Unverified child process during checkpoint"); return nullptr; }
  }
  std::vector<uint64_t> operations;
  // Pinned CPython 3.11 fork_exec ABI: c2pwrite and errwrite are the actual
  // converted stdout/stderr descriptors, after any provider fileno() calls.
  for (const auto& item : {std::make_pair(9,1), std::make_pair(11,2)})
  {
    int descriptor = -1;
    if (PyTuple_Check(tuple) && PyTuple_GET_SIZE(tuple) == 23)
    {
      auto* value = PyTuple_GET_ITEM(tuple,item.first);
      if (PyLong_Check(value))
      {
        const long fd = PyLong_AsLong(value);
        if (!PyErr_Occurred() && fd >= -1 && fd <= INT_MAX)
          descriptor = fd < 0 ? item.second : static_cast<int>(fd);
        else PyErr_Clear();
      }
    }
    const auto path = descriptor < 0 ? std::string{} : Ledger::DescriptorPath(descriptor);
    const auto token = Ledger::BeginProtectedOperation(writer,
        path.empty() ? std::vector<std::string>{} : std::vector<std::string>{path},
        "native_child_output_preparing",false,false,descriptor);
    if (!token)
    {
      for (const auto active : operations) Ledger::EndProtectedOperation(active);
      InfinityPythonPersistence::AdmissionDenied(context,"Child output crosses protected write barrier");
      return nullptr;
    }
    operations.push_back(token);
  }
  auto* result = Specs()[FORK_EXEC].original.ml_meth(self,tuple);
  if (result && PyLong_Check(result))
  {
    const long pid = PyLong_AsLong(result);
    if (!PyErr_Occurred() && pid > 0 && pid <= INT_MAX)
    {
      for (const auto active : operations) Ledger::BindProtectedChild(active,static_cast<int>(pid));
      return result;
    }
    PyErr_Clear();
    Ledger::ProtectionFailure("native_child_pid_unconfirmed");
  }
  for (const auto active : operations) Ledger::EndProtectedOperation(active);
  return result;
}
template<Kind kind> bool Prepare(PyMethodDef* method)
{
  auto& spec = Specs()[kind];
  if (spec.installed) return method == &spec.replacement ||
      (method->ml_meth == spec.original.ml_meth && method->ml_flags == spec.original.ml_flags);
  spec.original = spec.replacement = *method;
  if constexpr (kind == FORK_EXEC)
  {
    if (method->ml_flags != METH_VARARGS) return false;
    spec.replacement.ml_meth = ForkExec; spec.installed = true; return true;
  }
  switch (method->ml_flags)
  {
    case METH_FASTCALL: spec.replacement.ml_meth = _PyCFunction_CAST(Fast<kind>); break;
    case METH_FASTCALL | METH_KEYWORDS: spec.replacement.ml_meth = _PyCFunction_CAST(FastKeywords<kind>); break;
    case METH_O: case METH_NOARGS: spec.replacement.ml_meth = Single<kind>; break;
    case METH_VARARGS: spec.replacement.ml_meth = VarArgs<kind>; break;
    case METH_VARARGS | METH_KEYWORDS: spec.replacement.ml_meth = _PyCFunction_CAST(Keywords<kind>); break;
    default: Ledger::ProtectionFailure("unsupported_cpython_write_calling_convention"); return false;
  }
  spec.installed = true; return true;
}
template<Kind kind> bool Function(PyObject* module, const char* name, bool optional = false)
{
  PyObject* object = PyObject_GetAttrString(module, name);
  if (!object)
  {
    if (optional && PyErr_ExceptionMatches(PyExc_AttributeError)) { PyErr_Clear(); return true; }
    return false;
  }
  bool ok = PyCFunction_Check(object);
  if (ok)
  {
    auto* function = reinterpret_cast<PyCFunctionObject*>(object);
    ok = Prepare<kind>(function->m_ml);
    if (ok) function->m_ml = &Specs()[kind].replacement;
  }
  Py_DECREF(object); return ok;
}
template<Kind kind> bool Method(PyObject* module, const char* typeName, const char* name)
{
  PyObject* object = PyObject_GetAttrString(module, typeName);
  if (!object) return false;
  auto* type = reinterpret_cast<PyTypeObject*>(object);
  PyObject* member = PyDict_GetItemString(type->tp_dict, name);
  const bool found = member && Py_IS_TYPE(member, &PyMethodDescr_Type);
  bool ok = found;
  if (ok)
  {
    auto* descriptor = reinterpret_cast<PyMethodDescrObject*>(member);
    ok = Prepare<kind>(descriptor->d_method);
    if (ok) { descriptor->d_method = &Specs()[kind].replacement; PyType_Modified(type); }
  }
  Py_DECREF(object); return ok;
}
template<Kind kind> bool NativeTypeMethod(PyObject* object, const char* name)
{
  auto* type = Py_TYPE(object);
  auto* member = PyDict_GetItemString(type->tp_dict, name);
  if (!member || !Py_IS_TYPE(member, &PyMethodDescr_Type)) return false;
  auto* descriptor = reinterpret_cast<PyMethodDescrObject*>(member);
  if (!Prepare<kind>(descriptor->d_method)) return false;
  descriptor->d_method = &Specs()[kind].replacement;
  PyType_Modified(type); return true;
}
inline bool ProtectNativeModule(PyObject* module)
{
  if (!PyModule_Check(module)) return true;
  const auto* name = PyModule_GetName(module);
  if (!name) return false;
  if (std::strcmp(name,"PIL._imaging") && std::strcmp(name,"_imaging")) return true;
  // Match the locked dependency's ABI and disabled native TIFF/JPEG2000 paths.
  auto* dictionary = PyModule_GetDict(module);
  auto* version = PyDict_GetItemString(dictionary,"PILLOW_VERSION");
  if (!version || !PyUnicode_Check(version) || PyUnicode_CompareWithASCIIString(version,"8.4.0") ||
      PyDict_GetItemString(dictionary,"libtiff_encoder") || PyDict_GetItemString(dictionary,"jpeg2k_encoder"))
    return false;
  auto* encoder = PyObject_CallMethod(module,"raw_encoder","ss","RGB","RGB");
  if (!encoder) return false;
  const bool encoded = NativeTypeMethod<PIL_DESCRIPTOR_WRITE>(encoder,"encode_to_file");
  Py_DECREF(encoder);
  if (!encoded) return false;
  auto* image = PyObject_CallMethod(module,"new","s(ii)","RGB",1,1);
  if (!image) return false;
  const bool saved = NativeTypeMethod<PIL_PATH_WRITE>(image,"save_ppm");
  Py_DECREF(image); return saved;
}
inline initproc& RawInitializer() { static initproc original = nullptr; return original; }
inline int RawInitialize(PyObject* self, PyObject* tuple, PyObject* dictionary)
{
  // Reinitializing an existing FileIO closes its old fd without calling close.
  // Invalidate any concurrent operation using that descriptor before reuse.
  PyObject *errorType=nullptr,*errorValue=nullptr,*errorTrace=nullptr;
  PyErr_Fetch(&errorType,&errorValue,&errorTrace);
  auto* old = DescriptorReaders()[0](self,nullptr);
  if (old) { Ledger::InvalidateDescriptor(static_cast<int>(PyLong_AsLong(old))); Py_DECREF(old); }
  else PyErr_Clear(); // The native constructor is also called on new/closed objects.
  PyErr_Restore(errorType,errorValue,errorTrace);
  std::vector<PyObject*> values;
  for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(tuple); ++i) values.push_back(PyTuple_GET_ITEM(tuple, i));
  Call call(IO_OPEN, self, {values.data(), static_cast<Py_ssize_t>(values.size()), nullptr, dictionary});
  if (!call) return -1;
  return RawInitializer()(self, tuple, dictionary);
}
inline bool Initializer(PyObject* io)
{
  auto* object = PyObject_GetAttrString(io, "FileIO");
  if (!object) return false;
  auto* type = reinterpret_cast<PyTypeObject*>(object);
  auto* member = PyDict_GetItemString(type->tp_dict, "__init__");
  bool ok = member && Py_IS_TYPE(member, &PyWrapperDescr_Type);
  if (ok && type->tp_init != RawInitialize)
  {
    auto* descriptor = reinterpret_cast<PyWrapperDescrObject*>(member);
    if (RawInitializer() && RawInitializer() != type->tp_init) ok = false;
    else
    {
      RawInitializer() = type->tp_init;
      type->tp_init = RawInitialize;
      descriptor->d_wrapped = reinterpret_cast<void*>(RawInitialize);
      PyType_Modified(type);
    }
  }
  Py_DECREF(object); return ok;
}
inline bool Install()
{
  auto* posix = PyImport_ImportModule("posix");
  auto* io = PyImport_ImportModule("_io");
  auto* imports = PyImport_ImportModule("_imp");
  auto* locks = PyImport_ImportModule("fcntl");
  auto* children = PyImport_ImportModule("_posixsubprocess");
  if (!posix || !io || !imports || !locks || !children) { Py_XDECREF(posix); Py_XDECREF(io); Py_XDECREF(imports); Py_XDECREF(locks); Py_XDECREF(children); return false; }
  bool ok = RememberIOTypes(io) && DescriptorReader(io, "FileIO", 0) && DescriptorReader(io, "BufferedWriter", 1) &&
      DescriptorReader(io, "TextIOWrapper", 2) &&
      Function<EXTENSION_CREATE>(imports,"create_dynamic") &&
      Function<OS_WRITE>(posix, "write") && Function<OS_OPEN>(posix, "open") &&
      Function<OS_WRITEV>(posix, "writev", true) && Function<OS_PWRITE>(posix, "pwrite", true) &&
      Function<OS_PWRITEV>(posix, "pwritev", true) && Function<OS_FTRUNCATE>(posix, "ftruncate") &&
      Function<OS_TRUNCATE>(posix, "truncate") && Function<OS_SENDFILE>(posix, "sendfile", true) &&
      Function<OS_COPY>(posix, "copy_file_range", true) && Function<OS_RENAME>(posix, "rename") &&
      Function<OS_REPLACE>(posix, "replace") && Function<OS_UNLINK>(posix, "unlink") &&
      Function<OS_REMOVE>(posix, "remove") && Function<OS_MKDIR>(posix, "mkdir") &&
      Function<OS_MKFIFO>(posix,"mkfifo",true) && Function<OS_MKNOD>(posix,"mknod",true) &&
      Function<OS_FALLOCATE>(posix,"posix_fallocate",true) && Function<OS_SPLICE>(posix,"splice",true) &&
      Function<FILE_FLOCK>(locks,"flock") &&
      Function<FORK_EXEC>(children,"fork_exec") &&
      Function<OS_CLOSE>(posix, "close") && Function<OS_DUP>(posix, "dup") && Function<OS_DUP2>(posix, "dup2") &&
      Function<OS_CLOSERANGE>(posix,"closerange") &&
      Function<OS_RMDIR>(posix, "rmdir") && Function<IO_OPEN>(io, "open") &&
      Method<RAW_WRITE>(io, "FileIO", "write") && Method<RAW_TRUNCATE>(io, "FileIO", "truncate") &&
      Method<RAW_CLOSE>(io, "FileIO", "close") &&
      Method<BUFFER_WRITE>(io, "BufferedWriter", "write") &&
      Method<BUFFER_WRITE>(io, "BufferedRandom", "write") &&
      Method<BUFFER_TRUNCATE>(io, "BufferedWriter", "truncate") &&
      Method<BUFFER_TRUNCATE>(io, "BufferedRandom", "truncate") &&
      Method<BUFFER_FLUSH>(io, "BufferedWriter", "flush") &&
      Method<BUFFER_FLUSH>(io, "BufferedRandom", "flush") &&
      Method<BUFFER_CLOSE>(io, "BufferedWriter", "close") &&
      Method<BUFFER_CLOSE>(io, "BufferedRandom", "close") &&
      Method<TEXT_WRITE>(io, "TextIOWrapper", "write") &&
      Method<TEXT_TRUNCATE>(io, "TextIOWrapper", "truncate") &&
      Method<TEXT_FLUSH>(io, "TextIOWrapper", "flush") &&
      Method<TEXT_CLOSE>(io, "TextIOWrapper", "close") && Initializer(io);
  Py_DECREF(posix); Py_DECREF(io); Py_DECREF(imports); Py_DECREF(locks); Py_DECREF(children);
  if (!ok) Ledger::ProtectionFailure("native_cpython_write_hooks_not_installed");
  return ok;
}
} // namespace InfinityPythonWriteHooks
