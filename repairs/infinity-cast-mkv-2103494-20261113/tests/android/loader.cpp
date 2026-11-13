// CI-only loader: reuse the original engine's FFmpeg without starting Kodi or JNI lifecycle.
#include <jni.h>
#include <dlfcn.h>
extern "C" JNIEXPORT jboolean JNICALL Java_com_projectinfinity_kodi_InfinityCastProbeActivity_loadExistingEngine(JNIEnv*,jclass){
 static void* engine=dlopen("libkodi.so",RTLD_NOW|RTLD_LOCAL);return engine?JNI_TRUE:JNI_FALSE;
}
