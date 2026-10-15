import com.sun.source.tree.*;
import com.sun.source.util.*;
import javax.tools.*;
import java.net.URI;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;

/** Host-only parser. Never included in the Android application. */
public class MemberInventory {
  static String quote(String s){return "\""+s.replace("\\","\\\\").replace("\"","\\\"").replace("\n","\\n").replace("\r","\\r").replace("\t","\\t")+"\"";}
  static String hash(String s){try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(s.getBytes(StandardCharsets.UTF_8)));}catch(Exception e){throw new RuntimeException(e);}}
  public static void main(String[] args)throws Exception{
    String code=Files.readString(Path.of(args[0])).replace("@APP_PACKAGE@","com.projectinfinity.kodi");
    JavaFileObject file=new SimpleJavaFileObject(URI.create("string:///Input.java"),JavaFileObject.Kind.SOURCE){@Override public CharSequence getCharContent(boolean ignore){return code;}};
    DiagnosticCollector<JavaFileObject> diagnostics=new DiagnosticCollector<>();
    JavacTask task=(JavacTask)ToolProvider.getSystemJavaCompiler().getTask(null,null,diagnostics,List.of("-proc:none"),null,List.of(file));
    CompilationUnitTree unit=task.parse().iterator().next();
    for(Diagnostic<?> d:diagnostics.getDiagnostics())if(d.getKind()==Diagnostic.Kind.ERROR)throw new IllegalStateException(d.toString());
    SortedMap<String,String> out=new TreeMap<>();
    new TreeScanner<Void,String>() {
      @Override public Void visitClass(ClassTree node,String owner){
        if(node.getSimpleName().length()==0)return null;
        String name=owner==null?node.getSimpleName().toString():owner+"$"+node.getSimpleName();
        String head=node.getModifiers()+" "+node.getKind()+" "+node.getSimpleName()+" "+node.getTypeParameters()+" "+node.getExtendsClause()+" "+node.getImplementsClause();
        put(name+"::<class>",head);return super.visitClass(node,name);
      }
      void put(String key,String value){if(out.put(key,hash(value))!=null)throw new IllegalStateException("Duplicate member "+key);}
      @Override public Void visitMethod(MethodTree node,String owner){
        List<String> types=new ArrayList<>();for(VariableTree p:node.getParameters())types.add(p.getType().toString());
        put(owner+"::"+node.getName()+"("+String.join(",",types)+")",node.toString());return null;
      }
      @Override public Void visitVariable(VariableTree node,String owner){put(owner+"::field:"+node.getName(),node.toString());return null;}
      @Override public Void visitBlock(BlockTree node,String owner){put(owner+"::<initializer@"+unit.getLineMap().getLineNumber(Trees.instance(task).getSourcePositions().getStartPosition(unit,node))+">",node.toString());return null;}
    }.scan(unit,null);
    StringJoiner json=new StringJoiner(",\n","{\n","\n}\n");for(var e:out.entrySet())json.add(quote(e.getKey())+":"+quote(e.getValue()));Files.writeString(Path.of(args[1]),json.toString());
  }
}
