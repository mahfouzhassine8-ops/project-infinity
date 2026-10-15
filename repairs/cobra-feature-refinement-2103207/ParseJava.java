import java.nio.file.*;
import java.net.URI;
import java.util.*;
import javax.tools.*;
import com.sun.source.util.JavacTask;

/** Syntax only: deliberately does not claim Android compilation. */
class ParseJava {
  public static void main(String[] args) throws Exception {
    var diagnostics=new DiagnosticCollector<JavaFileObject>();
    var files=new ArrayList<JavaFileObject>();
    try(var paths=Files.walk(Path.of(args[0]))) {
      for(var path:paths.filter(p->p.toString().endsWith(".java.in")||p.toString().endsWith(".java")).toList()) {
        String name=path.getFileName().toString().replace(".in", "");
        String source=Files.readString(path).replace("@APP_PACKAGE@","com.projectinfinity.kodi")
          .replaceAll("@[A-Z_]+@", "GeneratedValue");
        files.add(new SimpleJavaFileObject(URI.create("string:///"+name),JavaFileObject.Kind.SOURCE){
          public CharSequence getCharContent(boolean ignored){return source;}
        });
      }
    }
    JavacTask task=(JavacTask)ToolProvider.getSystemJavaCompiler().getTask(null,null,diagnostics,List.of("-proc:none"),null,files);
    task.parse();
    long errors=diagnostics.getDiagnostics().stream().filter(d->d.getKind()==Diagnostic.Kind.ERROR).peek(System.err::println).count();
    if(errors>0)throw new AssertionError(errors+" syntax errors");
    System.out.println("PASS syntax only: "+files.size()+" Java templates");
  }
}
