#pragma once
// Internal presentation classifier. No provider execution, settings mutation,
// persistence exemption, or unknown-dialog suppression is authorized here.
// Include Python.h first in the Python-enabled native translation unit.
#include <frameobject.h>
#include <openssl/evp.h>
#include <cerrno>
#include <cstring>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>
#include <string>

namespace
{
namespace InfinityPromotionalDialog
{
enum class Surface { QrWindow, OkDialog };
struct Ref
{
  PyObject* value{nullptr};
  explicit Ref(PyObject* object=nullptr):value(object){}
  ~Ref(){Py_XDECREF(value);}
  Ref(const Ref&)=delete;Ref& operator=(const Ref&)=delete;
};
struct ErrorState
{
  PyObject *type{nullptr},*value{nullptr},*trace{nullptr};
  int nativeError{errno};
  ErrorState(){PyErr_Fetch(&type,&value,&trace);}
  ~ErrorState(){PyErr_Clear();PyErr_Restore(type,value,trace);errno=nativeError;}
};
struct Reentry
{
  bool& active;
  explicit Reentry(bool& flag):active(flag){active=true;}
  ~Reentry(){active=false;}
};
struct FileDescriptor
{
  int value{-1};
  explicit FileDescriptor(int fd):value(fd){}
  ~FileDescriptor(){if(value>=0)::close(value);}
  bool Close(){const int fd=value;value=-1;return ::close(fd)==0;}
  FileDescriptor(const FileDescriptor&)=delete;
  FileDescriptor& operator=(const FileDescriptor&)=delete;
};
struct NativeIoScope
{
  PyThreadState* state{PyEval_SaveThread()};
  ~NativeIoScope(){PyEval_RestoreThread(state);}
  NativeIoScope()=default;
  NativeIoScope(const NativeIoScope&)=delete;
  NativeIoScope& operator=(const NativeIoScope&)=delete;
};
static bool Text(PyObject* object,std::string& text)
{
  if(!object || !PyUnicode_CheckExact(object) || PyUnicode_GetLength(object)>4096)return false;
  Py_ssize_t length=0;
  const char* bytes=PyUnicode_AsUTF8AndSize(object,&length);
  if(!bytes || length<=0 || length>16384 || std::memchr(bytes,0,length))return false;
  text.assign(bytes,static_cast<std::size_t>(length));return true;
}
static bool Source(const std::string& path,const char* leaf,const char* digest,std::string& source)
{
  const std::string suffix=std::string("/script.module.slyguy/resources/modules/slyguy/")+leaf;
  if(path.empty() || path.front()!='/' || path.size()<=suffix.size() ||
      path.compare(path.size()-suffix.size(),suffix.size(),suffix)!=0)return false;
  const int fd=::open(path.c_str(),O_RDONLY|O_CLOEXEC|O_NOFOLLOW|O_NONBLOCK);
  if(fd<0)return false;
  FileDescriptor descriptor(fd);
  struct stat before{},after{};
  bool valid=::fstat(fd,&before)==0 && S_ISREG(before.st_mode) && before.st_size>0 && before.st_size<=1024*1024;
  char buffer[8192];
  while(valid && source.size()<=static_cast<std::size_t>(before.st_size)) {
    const auto count=::read(fd,buffer,sizeof(buffer));
    if(count<0 && errno==EINTR)continue;
    if(count<0){valid=false;break;}
    if(count==0)break;
    source.append(buffer,static_cast<std::size_t>(count));
  }
  valid=valid && source.size()==static_cast<std::size_t>(before.st_size) &&
      ::fstat(fd,&after)==0 && before.st_dev==after.st_dev && before.st_ino==after.st_ino &&
      before.st_size==after.st_size && before.st_mtim.tv_sec==after.st_mtim.tv_sec &&
      before.st_mtim.tv_nsec==after.st_mtim.tv_nsec && source.find('\0')==std::string::npos;
  if(!descriptor.Close())valid=false;
  if(!valid)return false;
  unsigned char hash[EVP_MAX_MD_SIZE]{};unsigned size=0;
  if(EVP_Digest(source.data(),source.size(),hash,&size,EVP_sha256(),nullptr)!=1 || size!=32)return false;
  static const char hex[]="0123456789abcdef";std::string encoded;
  for(unsigned i=0;i<size;++i){encoded+=hex[hash[i]>>4];encoded+=hex[hash[i]&15];}
  return encoded==digest;
}
static PyCodeObject* FindCode(PyCodeObject* code,const char* qualname,unsigned depth=0)
{
  if(depth>8 || !PyCode_Check(code))return nullptr;
  if(PyUnicode_CompareWithASCIIString(code->co_qualname,qualname)==0)return code;
  if(!PyTuple_CheckExact(code->co_consts))return nullptr;
  const auto count=PyTuple_GET_SIZE(code->co_consts);
  if(count>4096)return nullptr;
  for(Py_ssize_t i=0;i<count;++i) {
    auto* item=PyTuple_GET_ITEM(code->co_consts,i);
    if(PyCode_Check(item)) {
      auto* found=FindCode(reinterpret_cast<PyCodeObject*>(item),qualname,depth+1);
      if(found)return found;
    }
  }
  return nullptr;
}
struct Budget
{
  std::size_t bytes{256*1024};unsigned nodes{4096};
  bool Take(std::size_t count)
  {if(count>bytes)return false;bytes-=count;return true;}
};
static bool SameValue(PyObject*,PyObject*,Budget&,unsigned);
static bool CompareCode(PyCodeObject* actual,PyCodeObject* expected,Budget& budget,unsigned depth)
{
  // Pinned CPython 3.11 layout. Compare execution content, not marshal's
  // reference/interning representation or mutable specialization caches.
  if(actual->co_argcount!=expected->co_argcount ||
      actual->co_posonlyargcount!=expected->co_posonlyargcount ||
      actual->co_kwonlyargcount!=expected->co_kwonlyargcount ||
      actual->co_stacksize!=expected->co_stacksize ||
      actual->co_flags!=expected->co_flags ||
      actual->co_firstlineno!=expected->co_firstlineno ||
      actual->co_nlocalsplus!=expected->co_nlocalsplus ||
      actual->co_nlocals!=expected->co_nlocals ||
      actual->co_nplaincellvars!=expected->co_nplaincellvars ||
      actual->co_ncellvars!=expected->co_ncellvars ||
      actual->co_nfreevars!=expected->co_nfreevars)return false;
  Ref left(PyCode_GetCode(actual)),right(PyCode_GetCode(expected));
  PyObject* a[]={left.value,actual->co_consts,actual->co_names,actual->co_exceptiontable,
      actual->co_localsplusnames,actual->co_localspluskinds,actual->co_filename,
      actual->co_name,actual->co_qualname,actual->co_linetable};
  PyObject* b[]={right.value,expected->co_consts,expected->co_names,expected->co_exceptiontable,
      expected->co_localsplusnames,expected->co_localspluskinds,expected->co_filename,
      expected->co_name,expected->co_qualname,expected->co_linetable};
  for(unsigned i=0;i<sizeof(a)/sizeof(*a);++i)
    if(!SameValue(a[i],b[i],budget,depth+1))return false;
  return true;
}
static bool SameValue(PyObject* a,PyObject* b,Budget& budget,unsigned depth)
{
  if(!a || !b || Py_TYPE(a)!=Py_TYPE(b) || depth>16 || budget.nodes==0)return false;
  --budget.nodes;
  if(a==Py_None || PyBool_Check(a))return a==b;
  if(PyCode_Check(a))return CompareCode(reinterpret_cast<PyCodeObject*>(a),reinterpret_cast<PyCodeObject*>(b),budget,depth);
  if(PyTuple_CheckExact(a)) {
    const auto size=PyTuple_GET_SIZE(a);
    if(size!=PyTuple_GET_SIZE(b) || size>static_cast<Py_ssize_t>(budget.nodes))return false;
    for(Py_ssize_t i=0;i<size;++i)
      if(!SameValue(PyTuple_GET_ITEM(a,i),PyTuple_GET_ITEM(b,i),budget,depth+1))return false;
    return true;
  }
  if(PyBytes_CheckExact(a)) {
    const auto size=PyBytes_GET_SIZE(a);
    return size==PyBytes_GET_SIZE(b) && budget.Take(size) &&
        std::memcmp(PyBytes_AS_STRING(a),PyBytes_AS_STRING(b),static_cast<std::size_t>(size))==0;
  }
  if(PyUnicode_CheckExact(a)) {
    const auto size=PyUnicode_GET_LENGTH(a);
    return size==PyUnicode_GET_LENGTH(b) && size<=static_cast<Py_ssize_t>(budget.bytes/4) &&
        budget.Take(static_cast<std::size_t>(size)*4) && PyUnicode_Compare(a,b)==0;
  }
  if(PyLong_CheckExact(a)) {
    const auto size=Py_SIZE(a);
    if(size!=Py_SIZE(b) || size>4096 || size< -4096)return false;
    const auto bytes=static_cast<std::size_t>(size<0?-size:size)*sizeof(digit);
    return budget.Take(bytes) && std::memcmp(reinterpret_cast<PyLongObject*>(a)->ob_digit,
        reinterpret_cast<PyLongObject*>(b)->ob_digit,bytes)==0;
  }
  if(PyFloat_CheckExact(a)) {
    const double x=PyFloat_AS_DOUBLE(a),y=PyFloat_AS_DOUBLE(b);
    return budget.Take(sizeof(x)) && std::memcmp(&x,&y,sizeof(x))==0;
  }
  if(PyComplex_CheckExact(a)) {
    const auto x=reinterpret_cast<PyComplexObject*>(a)->cval;
    const auto y=reinterpret_cast<PyComplexObject*>(b)->cval;
    return budget.Take(sizeof(double)*2) && std::memcmp(&x.real,&y.real,sizeof(double))==0 &&
        std::memcmp(&x.imag,&y.imag,sizeof(double))==0;
  }
  // No rich comparison, getters, user equality, or unsupported constant types.
  return false;
}
static bool SameCode(PyCodeObject* actual,PyCodeObject* expected)
{
  Budget budget;
  return SameValue(reinterpret_cast<PyObject*>(actual),reinterpret_cast<PyObject*>(expected),budget,0) && !PyErr_Occurred();
}
static bool Matches(PyCodeObject* actual,PyCodeObject* module,const char* qualname)
{return PyUnicode_CompareWithASCIIString(actual->co_qualname,qualname)==0 && SameCode(actual,FindCode(module,qualname));}

static bool Capture(Surface surface) noexcept
{
  // These call sites already belong to Python's binding/GIL contract. This
  // sanity check never acquires a GIL or guesses another interpreter's state.
  auto* thread=_PyThreadState_UncheckedGet();
  if(!thread || thread->thread_id!=PyThread_get_thread_ident())return false;
  static thread_local bool classifying=false;
  if(classifying)return false; // compile audit callbacks may reenter UI
  Reentry reentry(classifying);ErrorState error;
  try {
    Ref first(reinterpret_cast<PyObject*>(PyThreadState_GetFrame(thread)));
    if(!first.value)return false;
    auto* dialogFrame=reinterpret_cast<PyFrameObject*>(first.value);
    if(PyFrame_GetLineNumber(dialogFrame)!=(surface==Surface::QrWindow?193:195))return false;
    Ref firstCode(reinterpret_cast<PyObject*>(PyFrame_GetCode(dialogFrame)));
    if(!firstCode.value)return false;
    auto* dialogCode=reinterpret_cast<PyCodeObject*>(firstCode.value);
    if(PyUnicode_CompareWithASCIIString(dialogCode->co_qualname,"ok")!=0)return false;
    Ref second(reinterpret_cast<PyObject*>(PyFrame_GetBack(dialogFrame)));
    if(!second.value)return false;
    auto* supportFrame=reinterpret_cast<PyFrameObject*>(second.value);
    if(PyFrame_GetLineNumber(supportFrame)!=982)return false;
    Ref secondCode(reinterpret_cast<PyObject*>(PyFrame_GetCode(supportFrame)));
    if(!secondCode.value)return false;
    auto* supportCode=reinterpret_cast<PyCodeObject*>(secondCode.value);
    if(PyUnicode_CompareWithASCIIString(supportCode->co_qualname,"process_support")!=0)return false;
    Ref third(reinterpret_cast<PyObject*>(PyFrame_GetBack(supportFrame)));
    if(!third.value)return false;
    auto* ownerFrame=reinterpret_cast<PyFrameObject*>(third.value);
    const int ownerLine=PyFrame_GetLineNumber(ownerFrame);
    const char* ownerName=ownerLine==913?"Folder.display":ownerLine==757?"Item.play":nullptr;
    if(!ownerName)return false;
    Ref thirdCode(reinterpret_cast<PyObject*>(PyFrame_GetCode(ownerFrame)));
    if(!thirdCode.value)return false;
    auto* ownerCode=reinterpret_cast<PyCodeObject*>(thirdCode.value);
    std::string dialogPath,pluginPath,ownerPath;
    if(!Text(dialogCode->co_filename,dialogPath) || !Text(supportCode->co_filename,pluginPath) ||
        !Text(ownerCode->co_filename,ownerPath) || ownerPath!=pluginPath)return false;
    const auto dialogSlash=dialogPath.rfind('/'),pluginSlash=pluginPath.rfind('/');
    if(dialogPath.substr(0,dialogSlash)!=pluginPath.substr(0,pluginSlash))return false;
    std::string dialogSource,pluginSource;
    bool verifiedSources=false;
    {
      // Regular files on Android FUSE can block despite O_NONBLOCK. Only
      // native I/O and hashing run without the GIL. Owned Python references
      // remain outside this scope and are released after this same state is
      // restored, including on native allocation or file-operation errors.
      NativeIoScope nativeIo;
      verifiedSources=Source(dialogPath,"dialog.py","ab3e19bd94f3575ba0a2b3ec957bfa69f1fe4a439d3f2a21cd4cc2e45cb56e97",dialogSource) &&
          Source(pluginPath,"plugin.py","f197feaf23a5115e3d593a2cb7586b70706cd93701e107feb2c859be593f3ad0",pluginSource);
    }
    if(!verifiedSources)return false;
    Ref dialogModule(Py_CompileStringExFlags(dialogSource.c_str(),dialogPath.c_str(),Py_file_input,nullptr,-1));
    Ref pluginModule(Py_CompileStringExFlags(pluginSource.c_str(),pluginPath.c_str(),Py_file_input,nullptr,-1));
    return dialogModule.value && pluginModule.value &&
        Matches(dialogCode,reinterpret_cast<PyCodeObject*>(dialogModule.value),"ok") &&
        Matches(supportCode,reinterpret_cast<PyCodeObject*>(pluginModule.value),"process_support") &&
        Matches(ownerCode,reinterpret_cast<PyCodeObject*>(pluginModule.value),ownerName);
  } catch(...) {return false;}
}
} // namespace InfinityPromotionalDialog
} // anonymous namespace: no new native ABI
