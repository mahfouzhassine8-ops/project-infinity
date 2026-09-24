import com.sun.source.tree.*;
import com.sun.source.util.*;
import javax.tools.*;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.stream.Collectors;
/** Parse-only declaration inventory; Android type checking is a separate mandatory gate. */
class AuditJavaInventory {
  static String quote(String s){return "\""+s.replace("\\","\\\\").replace("\"","\\\"").replace("\n","\\n").replace("\r","\\r")+"\"";}
  public static void main(String[] args)throws Exception{
    String source=Files.readString(Path.of(args[0])).replace("@APP_PACKAGE@","com.projectinfinity.kodi");
    DiagnosticCollector<JavaFileObject> errors=new DiagnosticCollector<>();
    JavaFileObject input=new SimpleJavaFileObject(URI.create("string:///InfinityLiveActivity.java"),JavaFileObject.Kind.SOURCE){public CharSequence getCharContent(boolean ignore){return source;}};
    JavacTask task=(JavacTask)ToolProvider.getSystemJavaCompiler().getTask(null,null,errors,List.of("-proc:none"),null,List.of(input));
    CompilationUnitTree unit=task.parse().iterator().next();SourcePositions positions=Trees.instance(task).getSourcePositions();
    if(errors.getDiagnostics().stream().anyMatch(d->d.getKind()==Diagnostic.Kind.ERROR))throw new AssertionError(errors.getDiagnostics());
    ClassTree activity=(ClassTree)unit.getTypeDecls().stream().filter(t->t instanceof ClassTree&&((ClassTree)t).getSimpleName().contentEquals("InfinityLiveActivity")).findFirst().orElseThrow();
    List<String> rows=new ArrayList<>();
    for(Tree member:activity.getMembers()){
      String key;
      if(member instanceof MethodTree){MethodTree m=(MethodTree)member;key="method:"+m.getName()+"("+m.getParameters().stream().map(p->p.getType().toString()).collect(Collectors.joining(","))+")";}
      else if(member instanceof ClassTree)key="class:"+((ClassTree)member).getSimpleName();
      else if(member instanceof VariableTree)key="field:"+((VariableTree)member).getName();
      else key=member.getKind().toString()+":"+rows.size();
      int start=(int)positions.getStartPosition(unit,member),end=(int)positions.getEndPosition(unit,member);if(start<0||end<0)continue;
      String digest=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(source.substring(start,end).strip().getBytes(StandardCharsets.UTF_8)));
      rows.add(quote(key)+":{"+"\"sha256\":"+quote(digest)+",\"line\":"+unit.getLineMap().getLineNumber(start)+"}");
    }
    System.out.println("{"+String.join(",\n",rows)+"}");
  }
}
