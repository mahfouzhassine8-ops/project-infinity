package com.projectinfinity.kodi;

import android.content.Context;
import android.content.res.loader.ResourcesLoader;
import android.content.res.loader.ResourcesProvider;
import android.os.Build;
import android.os.ParcelFileDescriptor;
import android.system.Os;
import android.system.OsConstants;
import org.json.JSONObject;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;

/** Cast resources use their own 0x80 package, leaving original 0x7f IDs intact.
 * One provider/loader per :kodi process. No Cobra/default-process initializer.
 */
final class InfinityCastResources {
    private static ResourcesLoader loader;
    private InfinityCastResources() {}

    private static String hex(byte[] bytes) {
        StringBuilder out=new StringBuilder();
        for(byte b:bytes) out.append(String.format(java.util.Locale.ROOT,"%02x",b&255));
        return out.toString();
    }
    private static String sha(File file) throws Exception {
        MessageDigest digest=MessageDigest.getInstance("SHA-256");
        try(InputStream stream=new FileInputStream(file)) {
            byte[] buffer=new byte[65536];int n;
            while((n=stream.read(buffer))!=-1)digest.update(buffer,0,n);
        }
        return hex(digest.digest());
    }
    static synchronized void install(Context context) throws Exception {
        if(loader!=null)return;
        if(Build.VERSION.SDK_INT<30)throw new IllegalStateException("Cast requires Android 11 or newer");
        String expected;
        try(InputStream stream=context.getAssets().open("infinity-cast/RESOURCE-IDENTITY.json")) {
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();
            byte[] buffer=new byte[1024];int count;
            while((count=stream.read(buffer))!=-1) {
                if(bytes.size()+count>4096)throw new IllegalStateException("Cast resource identity exceeds limit");
                bytes.write(buffer,0,count);
            }
            byte[] data=bytes.toByteArray();
            if(data.length>4096)throw new IllegalStateException("Cast resource identity exceeds limit");
            JSONObject identity=new JSONObject(new String(data,StandardCharsets.UTF_8));
            if(identity.getInt("resource_package_id")!=128)throw new IllegalStateException("Cast resource package changed");
            expected=identity.getString("sha256");
        }
        if(!expected.matches("[a-f0-9]{64}"))throw new IllegalStateException("Cast resource identity is invalid");
        File cache=context.getCodeCacheDir().getCanonicalFile();
        File target=new File(cache,"infinity-cast-resources-"+expected+".apk");
        if(!target.getCanonicalFile().equals(target) || Files.isSymbolicLink(target.toPath()))
            throw new IllegalStateException("Cast resource cache is not owned");
        if(!target.exists()) {
            File temporary=File.createTempFile(".infinity-cast-resource-",".part",cache);
            try {
                try(InputStream in=context.getAssets().open("infinity-cast/resources.apk");
                    FileOutputStream out=new FileOutputStream(temporary)) {
                    byte[] data=new byte[65536];long total=0;int n;
                    while((n=in.read(data))!=-1) {
                        total+=n;if(total>64L*1024*1024)throw new IllegalStateException("Cast resource size limit");
                        out.write(data,0,n);
                    }
                    out.getFD().sync();
                }
                if(!expected.equals(sha(temporary)))throw new IllegalStateException("Cast resource verification failed");
                if(!temporary.setReadOnly())throw new IllegalStateException("Cast resource permissions failed");
                Files.move(temporary.toPath(),target.toPath(),StandardCopyOption.ATOMIC_MOVE);
            } finally {
                // Only this invocation's newly created incomplete cache file.
                Files.deleteIfExists(temporary.toPath());
            }
        }
        ResourcesLoader next=new ResourcesLoader();
        java.io.FileDescriptor pinned=Os.open(target.getPath(),OsConstants.O_RDONLY|OsConstants.O_NOFOLLOW,0);
        try(ParcelFileDescriptor descriptor=ParcelFileDescriptor.dup(pinned)) {
            android.system.StructStat stat=Os.fstat(pinned);
            if(!OsConstants.S_ISREG(stat.st_mode) || stat.st_uid!=android.os.Process.myUid() ||
                stat.st_size>64L*1024*1024)throw new IllegalStateException("Cast resource ownership failed");
            MessageDigest digest=MessageDigest.getInstance("SHA-256");
            byte[] buffer=new byte[65536];int count;
            while((count=Os.read(pinned,buffer,0,buffer.length))>0)digest.update(buffer,0,count);
            if(!expected.equals(hex(digest.digest())))throw new IllegalStateException("Cast resource verification failed");
            Os.lseek(pinned,0,OsConstants.SEEK_SET);
            next.addProvider(ResourcesProvider.loadFromApk(descriptor));
        } finally { Os.close(pinned); }
        context.getApplicationContext().getResources().addLoaders(next);
        loader=next;
    }
}
