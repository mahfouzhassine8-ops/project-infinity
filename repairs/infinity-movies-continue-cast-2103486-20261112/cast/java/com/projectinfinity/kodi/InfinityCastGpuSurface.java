package com.projectinfinity.kodi;

import android.graphics.SurfaceTexture;
import android.opengl.*;
import android.os.Handler;
import android.os.HandlerThread;
import android.view.Surface;
import java.io.IOException;
import java.nio.*;

/** One codec-owner thread; decoded pixels never leave the GPU. */
final class InfinityCastGpuSurface implements AutoCloseable {
    interface Check {void check() throws IOException;}
    private EGLDisplay display=EGL14.EGL_NO_DISPLAY;
    private EGLContext context=EGL14.EGL_NO_CONTEXT;
    private EGLSurface window=EGL14.EGL_NO_SURFACE;
    private SurfaceTexture texture;
    private Surface decoderSurface;
    private HandlerThread callbacks;
    private final Object signal=new Object();
    private boolean available,closing;
    private int textureId,program,position,texcoord,matrix;
    private final FloatBuffer vertices=buffer(new float[]{-1,-1,0,0,1,-1,1,0,-1,1,0,1,1,1,1,1});
    private final float[] transform=new float[16];
    private final int drawWidth,drawHeight;
    private static FloatBuffer buffer(float[] v){FloatBuffer b=ByteBuffer.allocateDirect(v.length*4).order(ByteOrder.nativeOrder()).asFloatBuffer();b.put(v).position(0);return b;}
    InfinityCastGpuSurface(Surface encoder,int sourceWidth,int sourceHeight,int sarNum,int sarDen) throws IOException {
        double aspect=(double)sourceWidth/sourceHeight*(sarNum>0&&sarDen>0?(double)sarNum/sarDen:1);
        drawWidth=Math.max(2,(int)Math.min(1280,720*aspect));drawHeight=Math.max(2,(int)Math.min(720,1280/aspect));
        try{
            display=EGL14.eglGetDisplay(EGL14.EGL_DEFAULT_DISPLAY);int[] version=new int[2];
            require(display!=EGL14.EGL_NO_DISPLAY && EGL14.eglInitialize(display,version,0,version,1),"cast_hw_egl_initialize");
            int[] attributes={EGL14.EGL_RED_SIZE,8,EGL14.EGL_GREEN_SIZE,8,EGL14.EGL_BLUE_SIZE,8,EGL14.EGL_RENDERABLE_TYPE,EGL14.EGL_OPENGL_ES2_BIT,EGL14.EGL_SURFACE_TYPE,EGL14.EGL_WINDOW_BIT,0x3142,1,EGL14.EGL_NONE};
            EGLConfig[] configs=new EGLConfig[1];int[] count=new int[1];require(EGL14.eglChooseConfig(display,attributes,0,configs,0,1,count,0)&&count[0]==1,"cast_hw_egl_config");
            context=EGL14.eglCreateContext(display,configs[0],EGL14.EGL_NO_CONTEXT,new int[]{EGL14.EGL_CONTEXT_CLIENT_VERSION,2,EGL14.EGL_NONE},0);
            require(context!=EGL14.EGL_NO_CONTEXT,"cast_hw_egl_context");window=EGL14.eglCreateWindowSurface(display,configs[0],encoder,new int[]{EGL14.EGL_NONE},0);require(window!=EGL14.EGL_NO_SURFACE,"cast_hw_egl_window");current();
            int[] names=new int[1];GLES20.glGenTextures(1,names,0);textureId=names[0];GLES20.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES,textureId);
            GLES20.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES,GLES20.GL_TEXTURE_MIN_FILTER,GLES20.GL_LINEAR);GLES20.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES,GLES20.GL_TEXTURE_MAG_FILTER,GLES20.GL_LINEAR);
            GLES20.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES,GLES20.GL_TEXTURE_WRAP_S,GLES20.GL_CLAMP_TO_EDGE);GLES20.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES,GLES20.GL_TEXTURE_WRAP_T,GLES20.GL_CLAMP_TO_EDGE);
            texture=new SurfaceTexture(textureId);texture.setDefaultBufferSize(sourceWidth,sourceHeight);
            callbacks=new HandlerThread("InfinityCastVideoFrames");callbacks.start();
            texture.setOnFrameAvailableListener(value->{synchronized(signal){if(!closing){available=true;signal.notifyAll();}}},new Handler(callbacks.getLooper()));decoderSurface=new Surface(texture);
            int vertex=shader(GLES20.GL_VERTEX_SHADER,"attribute vec4 aPosition; attribute vec2 aTex; uniform mat4 uMatrix; varying vec2 vTex; void main(){gl_Position=aPosition;vTex=(uMatrix*vec4(aTex,0.0,1.0)).xy;}");
            int fragment=shader(GLES20.GL_FRAGMENT_SHADER,"#extension GL_OES_EGL_image_external : require\nprecision mediump float; varying vec2 vTex; uniform samplerExternalOES sTexture; void main(){gl_FragColor=texture2D(sTexture,vTex);}");
            try{program=GLES20.glCreateProgram();GLES20.glAttachShader(program,vertex);GLES20.glAttachShader(program,fragment);GLES20.glLinkProgram(program);int[] ok=new int[1];GLES20.glGetProgramiv(program,GLES20.GL_LINK_STATUS,ok,0);require(ok[0]==GLES20.GL_TRUE,"cast_hw_gl_link");}
            finally{GLES20.glDeleteShader(vertex);GLES20.glDeleteShader(fragment);}
            position=GLES20.glGetAttribLocation(program,"aPosition");texcoord=GLES20.glGetAttribLocation(program,"aTex");matrix=GLES20.glGetUniformLocation(program,"uMatrix");require(position>=0&&texcoord>=0&&matrix>=0,"cast_hw_gl_locations");glCheck();
        }catch(Throwable failure){try{close();}catch(Exception ignored){}if(failure instanceof IOException)throw (IOException)failure;if(failure instanceof Error)throw (Error)failure;throw new IOException("cast_hw_gpu_initialize");}
    }
    Surface decoderSurface(){return decoderSurface;}
    private void current()throws IOException{require(EGL14.eglMakeCurrent(display,window,window,context),"cast_hw_egl_current");}
    static void require(boolean v,String reason)throws IOException{if(!v)throw new IOException(reason);}
    private static int shader(int type,String source)throws IOException{int shader=GLES20.glCreateShader(type);GLES20.glShaderSource(shader,source);GLES20.glCompileShader(shader);int[] ok=new int[1];GLES20.glGetShaderiv(shader,GLES20.GL_COMPILE_STATUS,ok,0);if(ok[0]!=GLES20.GL_TRUE){GLES20.glDeleteShader(shader);throw new IOException("cast_hw_gl_shader");}return shader;}
    private static void glCheck()throws IOException{require(GLES20.glGetError()==GLES20.GL_NO_ERROR,"cast_hw_gl_error");}
    void wake(){synchronized(signal){signal.notifyAll();}}
    void render(long ptsUs,Check check)throws IOException {
        long until=android.os.SystemClock.elapsedRealtime()+1200;
        synchronized(signal){while(!available){check.check();require(!closing&&android.os.SystemClock.elapsedRealtime()<until,"cast_hw_surface_frame_deadline");try{signal.wait(10);}catch(InterruptedException e){Thread.currentThread().interrupt();throw new IOException("cast_hw_interrupted");}}available=false;}
        check.check();current();texture.updateTexImage();texture.getTransformMatrix(transform);
        GLES20.glViewport(0,0,1280,720);GLES20.glClearColor(0,0,0,1);GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT);
        GLES20.glViewport((1280-drawWidth)/2,(720-drawHeight)/2,drawWidth,drawHeight);GLES20.glUseProgram(program);GLES20.glActiveTexture(GLES20.GL_TEXTURE0);GLES20.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES,textureId);
        vertices.position(0);GLES20.glVertexAttribPointer(position,2,GLES20.GL_FLOAT,false,16,vertices);GLES20.glEnableVertexAttribArray(position);
        vertices.position(2);GLES20.glVertexAttribPointer(texcoord,2,GLES20.GL_FLOAT,false,16,vertices);GLES20.glEnableVertexAttribArray(texcoord);GLES20.glUniformMatrix4fv(matrix,1,false,transform,0);GLES20.glDrawArrays(GLES20.GL_TRIANGLE_STRIP,0,4);glCheck();
        require(EGLExt.eglPresentationTimeANDROID(display,window,Math.multiplyExact(ptsUs,1000)),"cast_hw_egl_timestamp");require(EGL14.eglSwapBuffers(display,window),"cast_hw_egl_swap");check.check();
    }
    @Override public void close()throws IOException {
        synchronized(signal){closing=true;signal.notifyAll();}
        if(texture!=null)texture.setOnFrameAvailableListener(null);
        if(decoderSurface!=null){decoderSurface.release();decoderSurface=null;}if(texture!=null){texture.release();texture=null;}
        if(display!=EGL14.EGL_NO_DISPLAY){
            if(context!=EGL14.EGL_NO_CONTEXT&&window!=EGL14.EGL_NO_SURFACE&&EGL14.eglMakeCurrent(display,window,window,context)){if(program!=0)GLES20.glDeleteProgram(program);if(textureId!=0)GLES20.glDeleteTextures(1,new int[]{textureId},0);}program=textureId=0;
            require(EGL14.eglMakeCurrent(display,EGL14.EGL_NO_SURFACE,EGL14.EGL_NO_SURFACE,EGL14.EGL_NO_CONTEXT),"cast_hw_egl_unbind");
            if(window!=EGL14.EGL_NO_SURFACE){require(EGL14.eglDestroySurface(display,window),"cast_hw_egl_surface_release");window=EGL14.EGL_NO_SURFACE;}
            if(context!=EGL14.EGL_NO_CONTEXT){require(EGL14.eglDestroyContext(display,context),"cast_hw_egl_context_release");context=EGL14.EGL_NO_CONTEXT;}
            require(EGL14.eglReleaseThread(),"cast_hw_egl_thread_release");require(EGL14.eglTerminate(display),"cast_hw_egl_display_release");display=EGL14.EGL_NO_DISPLAY;
        }
        if(callbacks!=null){callbacks.quitSafely();try{callbacks.join(1500);}catch(InterruptedException e){Thread.currentThread().interrupt();throw new IOException("cast_hw_callback_interrupted");}require(!callbacks.isAlive(),"cast_hw_callback_not_retired");callbacks=null;}
    }
}
