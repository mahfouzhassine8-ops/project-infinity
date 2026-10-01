// SPDX-License-Identifier: GPL-2.0-or-later
// Presentation-only adaptation of locked Cobra 2103281's lightPixel,
// 56/44 premultiplied smoothing, four-edge Watch palette and radius-4 blur.
// x-ambient design: Copyright (c) 2026 mmnga, MIT (notice shipped alongside).
// No player, decoder, Android surface, provider or transport dependency.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <atomic>
#include <vector>
#include <zlib.h>
#include <unistd.h>
#include <sys/syscall.h>
#ifdef __ANDROID__
#include <jni.h>
#endif

namespace {
std::atomic<bool> foreground{false};
constexpr int W=24,H=16,MAX_PIXELS=144*144;
struct Pixel { float r=0,g=0,b=0,a=0; };
struct Ambient {
  std::array<Pixel,MAX_PIXELS> history{};
  std::array<Pixel,W*H> palette{},scratch{};
  std::vector<unsigned char> scan,packed,png,header;
  bool ready=false,light=false; int width=0,height=0;
  Ambient(){scan.reserve(144*144*4+144);packed.reserve(144*144*5);png.reserve(144*144*5);header.reserve(13);}
};
float clamp(float x,float lo=0,float hi=1){return std::max(lo,std::min(hi,x));}
Pixel mix(Pixel x,Pixel y,float t){return {x.r*(1-t)+y.r*t,x.g*(1-t)+y.g*t,x.b*(1-t)+y.b*t,x.a*(1-t)+y.a*t};}
Pixel over(Pixel s,Pixel d){return {s.r+d.r*(1-s.a),s.g+d.g*(1-s.a),s.b+d.b*(1-s.a),s.a+d.a*(1-s.a)};}
Pixel sample(const Pixel* p,int w,int h,float x,float y){
  x=clamp(x,0,w-1);y=clamp(y,0,h-1);int ix=(int)x,iy=(int)y;
  return mix(mix(p[iy*w+ix],p[iy*w+std::min(ix+1,w-1)],x-ix),
             mix(p[std::min(iy+1,h-1)*w+ix],p[std::min(iy+1,h-1)*w+std::min(ix+1,w-1)],x-ix),y-iy);
}
Pixel saturated(Pixel p){
  if(p.a<=0)return {};
  // Android ColorMatrix.setSaturation uses .213/.715/.072.
  float l=(.213f*p.r+.715f*p.g+.072f*p.b)/p.a;
  return {clamp(l+1.65f*(p.r/p.a-l))*p.a,clamp(l+1.65f*(p.g/p.a-l))*p.a,clamp(l+1.65f*(p.b/p.a-l))*p.a,p.a};
}
void edge(Ambient& a,int sx,int sy,int sw,int sh,int dx,int dy,int dw,int dh){
  for(int y=dy;y<dy+dh;y++)for(int x=dx;x<dx+dw;x++){
    float px=clamp(sx+(x-dx+.5f)*sw/dw-.5f,sx,sx+sw-1);
    float py=clamp(sy+(y-dy+.5f)*sh/dh-.5f,sy,sy+sh-1);
    a.palette[y*W+x]=over(saturated(sample(a.history.data(),a.width,a.height,px,py)),a.palette[y*W+x]);
  }
}
void blur(const std::array<Pixel,W*H>& in,std::array<Pixel,W*H>& out,bool horizontal){
  for(int y=0;y<H;y++)for(int x=0;x<W;x++){
    Pixel sum;int n=0;
    for(int d=-4;d<=4;d++){int xx=x+(horizontal?d:0),yy=y+(horizontal?0:d);if(xx<0||xx>=W||yy<0||yy>=H)continue;
      Pixel p=in[yy*W+xx];sum.r+=p.r;sum.g+=p.g;sum.b+=p.b;sum.a+=p.a;n++;}
    out[y*W+x]={sum.r/n,sum.g/n,sum.b/n,sum.a/n};
  }
}
void u32(std::vector<unsigned char>& b,uint32_t n){for(int s=24;s>=0;s-=8)b.push_back((n>>s)&255);}
void chunk(std::vector<unsigned char>& b,const char* name,const unsigned char* data,size_t n){
  u32(b,n);size_t start=b.size();b.insert(b.end(),name,name+4);if(n)b.insert(b.end(),data,data+n);
  u32(b,crc32(0,b.data()+start,n+4));
}
}
extern "C" {
int infinity_ambient_version(){return 1;}
int infinity_ambient_memfd(){
#ifdef SYS_memfd_create
  return syscall(SYS_memfd_create,"infinity-ambient-light",1);
#else
  return -1;
#endif
}
int infinity_ambient_allowed(){return foreground.load()?1:0;}
void infinity_ambient_set_active(int active){foreground.store(active!=0);}
void* infinity_ambient_create(){try{return new Ambient;}catch(...){return nullptr;}}
void infinity_ambient_destroy(void* p){delete static_cast<Ambient*>(p);}
void infinity_ambient_reset(void* p){if(p){auto& a=*static_cast<Ambient*>(p);a.ready=false;a.palette.fill({});}}
int infinity_ambient_feed(void* p,const unsigned char* bgra,int bytes,int w,int h,int light){
  if(!p||!bgra||!foreground.load()||w!=144||h<48||h>144||bytes!=w*h*4)return 0;
  auto& a=*static_cast<Ambient*>(p);bool first=!a.ready||a.width!=w||a.height!=h||a.light!=(light!=0);
  a.width=w;a.height=h;a.light=light!=0;float energySum=0;
  for(int i=0;i<w*h;i++){
    float r=bgra[4*i+2]/255.f,g=bgra[4*i+1]/255.f,b=bgra[4*i]/255.f;
    float maximum=std::max(r,std::max(g,b)),minimum=std::min(r,std::min(g,b));
    float neutral=light?0:.55f*std::max(0.f,(maximum-.55f)/.45f);
    float energy=clamp((maximum-.045f)/.45f)*clamp(std::max((maximum-minimum)/.22f,neutral));
    float luminance=.2126f*r+.7152f*g+.0722f*b;
    if(light)energy*=1-.70f*std::max(0.f,(luminance-.65f)/.35f);
    energySum+=energy;Pixel next{r*energy,g*energy,b*energy,energy};
    a.history[i]=first?next:mix(a.history[i],next,.44f);
  }
  // An all-black/unsupported capture never reuses another session's colors.
  if(energySum<.01f&&!a.ready)return 0;
  a.palette.fill({});int ex=std::max(1,(int)std::round(w*.04f)),ey=std::max(1,(int)std::round(h*.04f));
  edge(a,0,0,w,ey,0,0,24,8);edge(a,0,h-ey,w,ey,0,8,24,8);
  edge(a,0,0,ex,h,0,0,4,16);edge(a,w-ex,0,ex,h,20,0,4,16);
  blur(a.palette,a.scratch,true);blur(a.scratch,a.palette,false);a.ready=true;return 1;
}
// Rect coordinates are normalized to the CURRENT skin/window, never the device.
// Output is illumination only (no reconstructible video); placed only on material.
int infinity_ambient_tile(void* p,float left,float top,float right,float bottom,
                         int width,int height,float radius,float lip,
                         const unsigned char** output){
  if(!p||!output||!foreground.load()||width<1||height<1||width>144||height>144)return 0;
  auto& a=*static_cast<Ambient*>(p);if(!a.ready||right<=left||bottom<=top)return 0;
  try{
    a.scan.assign(height*(1+width*4),0);
    radius=clamp(radius,0,std::min(width,height)/2.f);lip=clamp(lip,0,2);
    for(int y=0;y<height;y++)for(int x=0;x<width;x++){
      Pixel color=sample(a.palette.data(),W,H,(left+(x+.5f)/width*(right-left))*W-.5f,(top+(y+.5f)/height*(bottom-top))*H-.5f);
      float qx=std::abs(x+.5f-width/2.f)-(width/2.f-radius),qy=std::abs(y+.5f-height/2.f)-(height/2.f-radius);
      float distance=std::sqrt(std::max(qx,0.f)*std::max(qx,0.f)+std::max(qy,0.f)*std::max(qy,0.f))+std::min(std::max(qx,qy),0.f)-radius;
      float coverage=clamp(.5f-distance),rim=clamp(.5f+distance+lip);
      // Locked Cobra Watch glass: light 62/195, OLED 95/245 transmission/rim.
      float alpha=coverage*((a.light?62.f:95.f)+(a.light?133.f:150.f)*rim)/255.f;
      size_t o=y*(1+width*4)+1+x*4;
      a.scan[o]=color.a>0?std::round(clamp(color.r/color.a)*255):0;
      a.scan[o+1]=color.a>0?std::round(clamp(color.g/color.a)*255):0;
      a.scan[o+2]=color.a>0?std::round(clamp(color.b/color.a)*255):0;
      a.scan[o+3]=std::round(clamp(color.a*alpha)*255);
    }
    uLongf count=compressBound(a.scan.size());a.packed.resize(count);
    if(compress2(a.packed.data(),&count,a.scan.data(),a.scan.size(),1)!=Z_OK)return 0;
    a.png.assign({137,80,78,71,13,10,26,10});a.header.clear();
    u32(a.header,width);u32(a.header,height);a.header.insert(a.header.end(),{8,6,0,0,0});
    chunk(a.png,"IHDR",a.header.data(),a.header.size());chunk(a.png,"IDAT",a.packed.data(),count);chunk(a.png,"IEND",nullptr,0);
    *output=a.png.data();return a.png.size();
  }catch(...){a.ready=false;return 0;}
}
#ifdef __ANDROID__
JNIEXPORT void JNICALL Java_com_projectinfinity_kodi_InfinityKodiAmbientGate_setActive(JNIEnv*,jclass,jboolean active){infinity_ambient_set_active(active);}
#endif
}
