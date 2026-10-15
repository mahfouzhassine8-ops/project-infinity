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

namespace InfinityPythonWriteHooks
{
namespace Ledger = InfinityScriptPersistence;
enum Kind
{
  OS_WRITE, OS_WRITEV, OS_PWRITE, OS_PWRITEV, OS_FTRUNCATE, OS_TRUNCATE,
  OS_SENDFILE, OS_COPY, OS_OPEN, OS_RENAME, OS_REPLACE, OS_UNLINK, OS_REMOVE,
  OS_MKDIR, OS_RMDIR, IO_OPEN,
  RAW_WRITE, RAW_TRUNCATE, RAW_CLOSE,
  BUFFER_WRITE, BUFFER_TRUNCATE, BUFFER_FLUSH, BUFFER_CLOSE,
  TEXT_WRITE, TEXT_TRUNCATE, TEXT_FLUSH, TEXT_CLOSE, COUNT
};
struct Spec
{
  PyMethodDef original{};
  PyMethodDef replacement{};
  bool installed{false};
};
inline std::array<Spec, COUNT>& Specs()
{ static auto* specs = new std::array<Spec, COUNT>; return *specs; }
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
    if (kind >= RAW_WRITE)
    {
      // The native descriptor lives on the built-in object, including buffers
      // created by cached _io.open. Keep any pre-existing exception intact.
      PyObject *type = nullptr, *value = nullptr, *trace = nullptr;
      PyErr_Fetch(&type, &value, &trace);
      auto* descriptor = PyObject_CallMethod(self, "fileno", nullptr);
      if (descriptor) { m_paths.push_back(Target(descriptor)); Py_DECREF(descriptor); }
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
    else if (kind == OS_COPY) m_paths = {Target(args.At(1, "dst"))};
    else if (kind == OS_SENDFILE) m_paths = {Target(args.At(0, "out_fd"))};
    else m_paths = {Target(args.At(0, kind == IO_OPEN ? "file" : "path"), args.At(-1, "dir_fd"))};
    const int writer = m_context ? m_context->id : -1;
    m_token = Ledger::BeginProtectedOperation(writer, m_paths, Specs()[kind].original.ml_name);
    m_allowed = m_token != 0;
    if (!m_allowed) { PyErr_SetString(PyExc_PermissionError, "Infinity protected write admission is closed"); return; }
    m_previousOwner = Ledger::protectedWriteOwner;
    Ledger::protectedWriteOwner = writer;
    if (m_context) ++m_context->nativeProtectionDepth[PyThreadState_Get()];
    if (kind == BUFFER_WRITE || kind == BUFFER_TRUNCATE || kind == TEXT_WRITE || kind == TEXT_TRUNCATE)
      Ledger::SetProtectedBuffer(writer, m_key, m_paths, true);
  }
  ~Call()
  {
    if (!m_token) return;
    if (m_context) --m_context->nativeProtectionDepth[PyThreadState_Get()];
    Ledger::protectedWriteOwner = m_previousOwner;
    Ledger::EndProtectedOperation(m_token);
  }
  explicit operator bool() const { return m_allowed; }
  PyObject* Finish(PyObject* result)
  {
    if (result && m_token && (m_kind == BUFFER_FLUSH || m_kind == BUFFER_CLOSE ||
                              m_kind == TEXT_FLUSH || m_kind == TEXT_CLOSE))
      Ledger::SetProtectedBuffer(m_context ? m_context->id : -1, m_key, m_paths, false);
    return result;
  }
private:
  Kind m_kind;
  InfinityPythonPersistence::Context* m_context;
  uint64_t m_token{0};
  bool m_allowed{false};
  int m_previousOwner{-1};
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
template<Kind kind> bool Prepare(PyMethodDef* method)
{
  auto& spec = Specs()[kind];
  if (spec.installed) return method == &spec.replacement ||
      (method->ml_meth == spec.original.ml_meth && method->ml_flags == spec.original.ml_flags);
  spec.original = spec.replacement = *method;
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
inline initproc& RawInitializer() { static initproc original = nullptr; return original; }
inline int RawInitialize(PyObject* self, PyObject* tuple, PyObject* dictionary)
{
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
  if (!posix || !io) { Py_XDECREF(posix); Py_XDECREF(io); return false; }
  bool ok = Function<OS_WRITE>(posix, "write") && Function<OS_OPEN>(posix, "open") &&
      Function<OS_WRITEV>(posix, "writev", true) && Function<OS_PWRITE>(posix, "pwrite", true) &&
      Function<OS_PWRITEV>(posix, "pwritev", true) && Function<OS_FTRUNCATE>(posix, "ftruncate") &&
      Function<OS_TRUNCATE>(posix, "truncate") && Function<OS_SENDFILE>(posix, "sendfile", true) &&
      Function<OS_COPY>(posix, "copy_file_range", true) && Function<OS_RENAME>(posix, "rename") &&
      Function<OS_REPLACE>(posix, "replace") && Function<OS_UNLINK>(posix, "unlink") &&
      Function<OS_REMOVE>(posix, "remove") && Function<OS_MKDIR>(posix, "mkdir") &&
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
  Py_DECREF(posix); Py_DECREF(io);
  if (!ok) Ledger::ProtectionFailure("native_cpython_write_hooks_not_installed");
  return ok;
}
} // namespace InfinityPythonWriteHooks
