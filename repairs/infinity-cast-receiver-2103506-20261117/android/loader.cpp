#include <jni.h>
#include <dlfcn.h>
#include <sstream>
extern "C" JNIEXPORT jstring JNICALL Java_com_projectinfinity_castqa_ReceiverHardwareProbe_engineCapabilities(JNIEnv* e,jclass){
 static void* engine=dlopen("libkodi.so",RTLD_NOW|RTLD_LOCAL);
 using Find=const void*(*)(const char*);
 auto encoder=engine?reinterpret_cast<Find>(dlsym(engine,"avcodec_find_encoder_by_name")):nullptr;
 auto decoder=engine?reinterpret_cast<Find>(dlsym(engine,"avcodec_find_decoder_by_name")):nullptr;
 auto has=[](Find f,const char* name){return f && f(name)?"true":"false";};
 std::ostringstream o;o<<"{\"engine_loaded\":"<<(engine?"true":"false")<<",\"aac_encoder\":"<<has(encoder,"aac")<<",\"h264_mediacodec_encoder\":"<<has(encoder,"h264_mediacodec")<<",\"hevc_mediacodec_encoder\":"<<has(encoder,"hevc_mediacodec")<<",\"hevc_mediacodec_decoder\":"<<has(decoder,"hevc_mediacodec")<<",\"software_hevc_decoder\":"<<has(decoder,"hevc")<<"}";
 return e->NewStringUTF(o.str().c_str());
}
