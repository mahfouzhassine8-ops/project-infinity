// Positive, interpreter-owned evidence from a successful native open/flush.
// A clean close/flush is admitted as NONPERSISTENT: it confers no permission
// for a callback to write new payload through an enclosing drain lease.
inline const char* const* IoMethodNames()
{
  static const char* names[]{"write","flush","close","truncate"}; return names;
}
inline bool CaptureIoContracts(InfinityPythonPersistence::Context* context)
{
  auto* io=PyImport_ImportModule("_io"); if(!io)return false;
  bool ok=true;
  for(const auto* name:{"FileIO","BufferedWriter","BufferedRandom","TextIOWrapper"})
  {
    InfinityPythonPersistence::IoContract contract;
    contract.type=PyObject_GetAttrString(io,name);
    if(!contract.type || !PyType_Check(contract.type))ok=false;
    for(unsigned i=0;i<4 && ok;++i)
    { contract.methods[i]=PyObject_GetAttrString(contract.type,IoMethodNames()[i]);if(!contract.methods[i])ok=false; }
    context->ioContracts.push_back(contract);
    if(!ok)break;
  }
  Py_DECREF(io); return ok;
}
inline bool TrustedIoObject(PyObject* object)
{
  auto* type=Py_TYPE(object); bool known=false;
  for(auto* native:IOTypes())if(type==native)known=true;
  auto* context=Context();
  if(!known && context)
    for(const auto& contract:context->ioContracts)
      if(reinterpret_cast<PyObject*>(type)==contract.type)
      {
        known=true;
        for(unsigned i=0;i<4;++i)
        {
          auto* method=PyObject_GetAttrString(contract.type,IoMethodNames()[i]);
          if(!method || method!=contract.methods[i])known=false;
          Py_XDECREF(method);
        }
      }
  if(!known)return false;
  if(type->tp_dictoffset)
  {
    auto* dictionary=PyObject_GenericGetDict(object,nullptr);if(!dictionary)return false;
    for(const auto* name:{"write","flush","close","truncate","fileno","writable","raw","buffer"})
      if(PyDict_GetItemString(dictionary,name))known=false;
    Py_DECREF(dictionary);
  }
  return known;
}
inline bool IoIdentity(PyObject* object,InfinityPythonPersistence::CleanIoReceipt& receipt)
{
  auto* descriptor=ActualDescriptor(object);
  if(!descriptor)return false;
  const long value=PyLong_Check(descriptor)?PyLong_AsLong(descriptor):-1;
  Py_DECREF(descriptor);
  if(PyErr_Occurred() || value<0 || value>INT_MAX)return false;
  struct stat st{};
  const int fd=static_cast<int>(value),flags=::fcntl(fd,F_GETFL);
  if(flags<0 || ::fstat(fd,&st)!=0)return false;
  receipt.fd=fd;receipt.device=st.st_dev;receipt.inode=st.st_ino;
  receipt.mode=st.st_mode;receipt.flags=flags;return true;
}
inline void ForgetCleanIo(PyObject* object)
{
  auto* context=Context();if(!context)return;
  const auto found=context->cleanIo.find(object);
  if(found!=context->cleanIo.end())
  {Py_XDECREF(found->second.weak);context->cleanIo.erase(found);}
}
inline void RecordCleanIo(PyObject* object)
{
  auto* context=Context();if(!context || !object)return;
  const int savedErrno=errno;PyObject *type=nullptr,*error=nullptr,*trace=nullptr;
  PyErr_Fetch(&type,&error,&trace);
  InfinityPythonPersistence::CleanIoReceipt receipt;
  if(TrustedIoObject(object) && IoIdentity(object,receipt))
  {
    receipt.weak=PyWeakref_NewRef(object,nullptr);
    if(receipt.weak)
    {
      ForgetCleanIo(object);
      if(context->cleanIo.size()>=65536)
      {
        for(auto it=context->cleanIo.begin();it!=context->cleanIo.end();)
          if(PyWeakref_GetObject(it->second.weak)==Py_None)
          {Py_DECREF(it->second.weak);it=context->cleanIo.erase(it);}else ++it;
      }
      if(context->cleanIo.size()<65536)context->cleanIo.emplace(object,receipt);
      else {Py_DECREF(receipt.weak);Ledger::Fail(context->id,"native_clean_io_inventory_exhausted");}
    }
  }
  PyErr_Clear();PyErr_Restore(type,error,trace);errno=savedErrno;
}
inline bool CleanIoTree(PyObject* object,bool& proof,unsigned depth=0)
{
  if(depth>4 || !TrustedIoObject(object))return false;
  auto* context=Context();if(!context)return false;
  InfinityPythonPersistence::CleanIoReceipt current;
  if(!IoIdentity(object,current))return false;
  const auto key=std::to_string(context->id)+":";
  const auto address=std::to_string(reinterpret_cast<uintptr_t>(object));
  {
    auto& state=Ledger::Get();std::lock_guard<std::mutex> lock(state.mutex);
    if(state.protection.buffers.count(key+address) ||
       state.protection.buffers.count(key+"native-buffer:"+address))return false;
  }
  const auto found=context->cleanIo.find(object);
  if(found!=context->cleanIo.end())
  {
    const auto& prior=found->second;
    if(PyWeakref_GetObject(prior.weak)!=object || prior.fd!=current.fd ||
       prior.device!=current.device || prior.inode!=current.inode ||
       prior.mode!=current.mode || prior.flags!=current.flags)return false;
    proof=true;
  }
  if(PyObject_TypeCheck(object,IOTypes()[0]))return true;
  for(unsigned i=1;i<=4;++i)
    if(PyObject_TypeCheck(object,IOTypes()[i]))
    {
      auto* next=NativeField(object,IOTypes()[i],i==4?"buffer":"raw");
      if(!next)return false;
      const bool clean=CleanIoTree(next,proof,depth+1);Py_DECREF(next);return clean;
    }
  return false;
}
inline bool VerifiedCleanIo(PyObject* object)
{
  const int savedErrno=errno;PyObject *type=nullptr,*error=nullptr,*trace=nullptr;
  PyErr_Fetch(&type,&error,&trace);bool proof=false;
  const bool clean=CleanIoTree(object,proof) && proof;
  PyErr_Clear();PyErr_Restore(type,error,trace);errno=savedErrno;return clean;
}
