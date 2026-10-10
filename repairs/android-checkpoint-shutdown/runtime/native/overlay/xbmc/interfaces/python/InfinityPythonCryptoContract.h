#pragma once
// Exact signed-APK crypto binaries: arithmetic/memory only, no durable I/O.
// See CRYPTO-2103362-AUDIT.json. No library-name prefix exemptions.
#include <dlfcn.h>
#include <openssl/evp.h>
#include <set>
namespace InfinityPythonPersistence {
struct CryptoImage {const char* name;const char* digest;const char* symbols;};
inline const std::vector<CryptoImage>& CryptoImages() {
 static const std::vector<CryptoImage> images={
  {"libCryptodome_Cipher__Salsa20.so","a6b27534731b443931a50bc081fe89c9bfa3644c0810b26062a79ad11fe66173","|Salsa20_8_core|Salsa20_stream_destroy|Salsa20_stream_encrypt|Salsa20_stream_init|"},
  {"libCryptodome_Cipher__chacha20.so","573bc77521e4c75cda9818b686987af221e9c1738268d88f97218c2c0206148f","|chacha20_destroy|chacha20_encrypt|chacha20_init|chacha20_seek|hchacha20|"},
  {"libCryptodome_Cipher__raw_aes.so","49dccf26bf84844090778e0d5980ede18f2fdb99c7f28ed57807d50413473aaf","|AES_start_operation|AES_stop_operation|"},
  {"libCryptodome_Cipher__raw_cbc.so","069a680c2643c5a05a77a20cb043070e550d344a268e767ea38b36c2cfd04848","|CBC_decrypt|CBC_encrypt|CBC_start_operation|CBC_stop_operation|"},
  {"libCryptodome_Cipher__raw_cfb.so","fb3ab550f9a22f5a043678786f40eb52cffbd306485fe38be17a8ed1c6214f0b","|CFB_decrypt|CFB_encrypt|CFB_start_operation|CFB_stop_operation|"},
  {"libCryptodome_Cipher__raw_ctr.so","a08cf702e9341789861d259dd30c4bd3dae3629fabf9de24eb6553681fb1e448","|CTR_decrypt|CTR_encrypt|CTR_start_operation|CTR_stop_operation|"},
  {"libCryptodome_Cipher__raw_ecb.so","5dcc7bddf9cf7db3b3605a90b390cea3ae6afbda1ddd9209fbabdef21a54f811","|ECB_decrypt|ECB_encrypt|ECB_start_operation|ECB_stop_operation|"},
  {"libCryptodome_Cipher__raw_ocb.so","966cd086b785d05ce397d733fee8a46e710ff22ece6a6dbda146b69f7a602a1d","|OCB_decrypt|OCB_digest|OCB_encrypt|OCB_start_operation|OCB_stop_operation|OCB_transcrypt|OCB_update|"},
  {"libCryptodome_Cipher__raw_ofb.so","77de679c6932e4ff59db0c58300d7b750fedd0e38d12e9f668988afa5a630869","|OFB_decrypt|OFB_encrypt|OFB_start_operation|OFB_stop_operation|"},
  {"libCryptodome_Hash__BLAKE2s.so","ae590e31568b2706725f7006b583dc593d4c4e6b438f2e56aa01825c1e16c1c2","|blake2s_copy|blake2s_destroy|blake2s_digest|blake2s_init|blake2s_update|"},
  {"libCryptodome_Hash__MD5.so","5ba9f38a40d6f920cb5a2835c4150adaa9f975ba585cc0d086d4b0288144907c","|MD5_copy|MD5_destroy|MD5_digest|MD5_init|MD5_pbkdf2_hmac_assist|MD5_update|"},
  {"libCryptodome_Hash__SHA1.so","61e8ba022e1ecb79fc8b64a4e60ec67acde9c3b1486c2f839f662e9a6fcd3392","|SHA1_copy|SHA1_destroy|SHA1_digest|SHA1_init|SHA1_pbkdf2_hmac_assist|SHA1_update|"},
  {"libCryptodome_Hash__SHA256.so","77aea79e5c4db591467e12b6bffe0fd4c237af3e764404b9db02506d722af434","|SHA256_copy|SHA256_destroy|SHA256_digest|SHA256_init|SHA256_pbkdf2_hmac_assist|SHA256_update|"},
  {"libCryptodome_Hash__ghash_portable.so","37acc302aff53118835c1b262a159c7d4b6cdb2705b7dc098b8eee4984c29010","|ghash_destroy_portable|ghash_expand_portable|ghash_portable|"},
  {"libCryptodome_Hash__poly1305.so","7716c738b5ab8f3548087d78a77232051b78831061ac04797986dda93f5fdd73","|poly1305_destroy|poly1305_digest|poly1305_init|poly1305_update|"},
  {"libCryptodome_Protocol__scrypt.so","c695b6a659cf06f9ea03705616663a84ea4a380eefe67d5130dad7198ce1137a","|scryptROMix|"},
  {"libCryptodome_Util__cpuid_c.so","d7a81665ef377989555c89ddc8c3d3b8cce13dfa0255bc6b228964847d11e40d","|have_aes_ni|have_clmul|"},
  {"libCryptodome_Util__strxor.so","c368ec648f91889d2d4032b401c0ac83cb530dd103291453b572a4b7395540eb","|strxor|strxor_c|"},
 };return images;
}
inline bool ApprovedCryptoImage(const std::string& path,const std::string& symbol={}) {
 const char* root=std::getenv("KODI_ANDROID_LIBS");
 if(!root || root[0]!='/' || path.empty() || path[0]!='/')return false;
 const auto slash=path.rfind('/');
 const auto name=path.substr(slash+1);
 const CryptoImage* image=nullptr;
 for(const auto& candidate:CryptoImages())if(name==candidate.name){image=&candidate;break;}
 if(!image || (!symbol.empty() && std::string(image->symbols).find("|"+symbol+"|")==std::string::npos))return false;
 char canonicalRoot[PATH_MAX]{},canonicalPath[PATH_MAX]{};
 if(!::realpath(root,canonicalRoot) || !::realpath(path.c_str(),canonicalPath) ||
    path!=std::string(canonicalRoot)+"/"+name || path!=canonicalPath)return false;
 struct stat before{},after{};
 if(::lstat(path.c_str(),&before)!=0 || !S_ISREG(before.st_mode))return false;
 const int fd=::open(path.c_str(),O_RDONLY|O_CLOEXEC|O_NOFOLLOW);
 if(fd<0)return false;
 std::string bytes;char buffer[8192];bool ok=true;
 for(;;){const auto got=::read(fd,buffer,sizeof(buffer));if(got<0 && errno==EINTR)continue;
  if(got<0 || bytes.size()>4*1024*1024){ok=false;break;}if(got==0)break;bytes.append(buffer,static_cast<std::size_t>(got));}
 ok=ok && ::fstat(fd,&after)==0 && before.st_dev==after.st_dev && before.st_ino==after.st_ino;
 if(::close(fd)!=0)ok=false;
 unsigned char digest[EVP_MAX_MD_SIZE]{};unsigned size=0;
 if(!ok || EVP_Digest(bytes.data(),bytes.size(),digest,&size,EVP_sha256(),nullptr)!=1 || size!=32)return false;
 static constexpr char hex[]="0123456789abcdef";std::string encoded;
 for(unsigned i=0;i<size;++i){encoded+=hex[digest[i]>>4];encoded+=hex[digest[i]&15];}
 return encoded==image->digest;
}
inline bool ApprovedNativeLookup(const char* event,PyObject* args) {
 const auto count=PyTuple_Check(args)?PyTuple_GET_SIZE(args):0;
 if(std::strcmp(event,"ctypes.dlopen")==0) {
  // dlopen(NULL) references the already-running process; loads no new image.
  if(count==1 && PyTuple_GET_ITEM(args,0)==Py_None)return true;
  return count==1 && ApprovedCryptoImage(Path(PyTuple_GET_ITEM(args,0)));
 }
 if(count!=2 || !PyUnicode_Check(PyTuple_GET_ITEM(args,1)))return false;
 const char* symbol=PyUnicode_AsUTF8(PyTuple_GET_ITEM(args,1));if(!symbol)return false;
 PyObject* first=PyTuple_GET_ITEM(args,0);
 PyObject* handle=std::strcmp(event,"ctypes.dlsym/handle")==0?first:PyObject_GetAttrString(first,"_handle");
 if(handle==first)Py_INCREF(handle);
 void* pointer=handle && PyLong_Check(handle)?PyLong_AsVoidPtr(handle):nullptr;Py_XDECREF(handle);
 if(!pointer || PyErr_Occurred()){PyErr_Clear();return false;}
 void* address=::dlsym(pointer,symbol);Dl_info info{};
 return address && ::dladdr(address,&info)!=0 && info.dli_fname && ApprovedCryptoImage(info.dli_fname,symbol);
}
} // namespace InfinityPythonPersistence
