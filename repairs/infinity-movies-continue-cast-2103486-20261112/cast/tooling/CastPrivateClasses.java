import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.jar.*;
import org.objectweb.asm.*;
import org.objectweb.asm.commons.*;

/** Build-time relocation only; this class and ASM are never APK inputs. */
public final class CastPrivateClasses {
    static final String PREFIX="assets/infinity/cast/privatehttp/";
    static String mapName(String name) {
        for(String root:new String[]{"okhttp3/","okio/","kotlin/","com/google/common/","androidx/concurrent/"})
            if(name.startsWith(root))return PREFIX+name;
        return name;
    }
    public static void main(String[] args) throws Exception {
        Path input=Paths.get(args[0]),output=Paths.get(args[1]),resources=Paths.get(args[2]);
        Remapper remapper=new Remapper(){
            @Override public String map(String name){return mapName(name);}
            @Override public Object mapValue(Object value) {
                // Kotlin/HTTP reflective fallbacks must not resolve their old
                // runtime class names against Cobra after relocation.
                if(value instanceof String) {
                    String name=(String)value,internal=name.replace('.','/');
                    if(internal.matches("[A-Za-z_$][A-Za-z0-9_$/]*")) {
                        String mapped=mapName(internal);
                        if(!mapped.equals(internal))return name.indexOf('/')>=0?mapped:mapped.replace('/','.');
                    }
                }
                return super.mapValue(value);
            }
        };
        Set<String> names=new HashSet<>();
        try(JarInputStream source=new JarInputStream(Files.newInputStream(input));JarOutputStream target=new JarOutputStream(Files.newOutputStream(output))) {
            JarEntry entry;
            while((entry=source.getNextJarEntry())!=null) {
                String name=entry.getName();if(!name.endsWith(".class"))continue;
                ClassReader reader=new ClassReader(source.readAllBytes());ClassWriter writer=new ClassWriter(0);
                reader.accept(new ClassRemapper(writer,remapper),0);
                String mapped=mapName(name.substring(0,name.length()-6))+".class";
                if(!names.add(mapped))throw new IOException("Duplicate relocated class");
                target.putNextEntry(new JarEntry(mapped));target.write(writer.toByteArray());target.closeEntry();
            }
        }
        // The official keep-name rule exists for this relative resource.
        // Relocate BOTH name and resource, rather than discarding the rule or
        // resolving it against Cobra's original class/resource namespace.
        try(JarFile source=new JarFile(input.toFile())) {
            JarEntry resource=source.getJarEntry("okhttp3/internal/publicsuffix/publicsuffixes.gz");
            if(resource!=null) {
                Path path=resources.resolve(PREFIX+resource.getName());Files.createDirectories(path.getParent());
                try(InputStream data=source.getInputStream(resource)){Files.copy(data,path,StandardCopyOption.REPLACE_EXISTING);}
            }
        }
    }
}
