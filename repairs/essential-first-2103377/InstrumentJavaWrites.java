import com.github.javaparser.*;
import com.github.javaparser.ast.*;
import com.github.javaparser.ast.body.*;
import com.github.javaparser.ast.expr.*;
import com.github.javaparser.ast.stmt.*;
import com.github.javaparser.ast.type.*;
import java.nio.file.*;
import java.util.*;

/** Source-range edits only: all bytes outside recorded write boundaries remain
 * unchanged. No optimizer, formatter, bytecode substitution or UI rewrite.
 */
public final class InstrumentJavaWrites {
  static final String HELPER="com.projectinfinity.kodi.InfinityJavaPersistence";
  static final String BARRIER="com.projectinfinity.kodi.InfinityJavaWriteBarrier";
  // These pinned classes write checkpoint receipts/process ownership or
  // diagnostic evidence only. They remain governed by the existing protocol.
  static final Set<String> COORDINATOR=Set.of("InfinityCheckpointProtocol","InfinityCloseGuardService",
      "InfinityCloseNativeLease","InfinityCheckpointEvidence","InfinityInstalledCodeEvidence",
      "InfinityTaskLifecycleGate","InfinityKodiShutdown","InfinityExitCompletion");
  static final Set<String> DIAGNOSTICS=Set.of("InfinityStartupTrace","InfinityResponsiveTrace",
      "InfinityExitDiagnostics","InfinityCobraDiagnostics","InfinityDiagnosticFiles",
      "CobraDiagnosticArchive","InfinityHealthExport","InfinityResponsiveness");
  static final Set<String> QUEUES=Set.of("InfinityStartupPreparation","InfinityLiveActivity",
      "CobraVisualRenderer","CobraPresentationSafety","InfinityCobraRecordingService");
  static final Set<String> THREADS=Set.of("InfinityPowerMenuRoutes","CobraSportsReminderJob");
  static final Set<String> ENTRIES=Set.of("Main","Splash","InfinityLiveActivity","XBMCSearchableActivity");
  static final Set<String> MUTATIONS=Set.of("delete","renameTo","mkdir","mkdirs","createNewFile","setLastModified");
  static final class Edit {
    int start,end;String value,reason;
    Edit(int start,int end,String value,String reason){this.start=start;this.end=end;this.value=value;this.reason=reason;}
  }
  static int offset(String source,Position pos){int at=0;for(int line=1;line<pos.line;line++)at=source.indexOf('\n',at)+1;return at+pos.column-1;}
  static String original(String source,Node node){Range r=node.getRange().orElseThrow();return source.substring(offset(source,r.begin),offset(source,r.end)+1);}
  static void replace(List<Edit> edits,String source,Node node,String value,String reason){Range r=node.getRange().orElseThrow();edits.add(new Edit(offset(source,r.begin),offset(source,r.end)+1,value,reason));}
  static String simple(Type type){String t=type.asString();int last=t.lastIndexOf('.');return last<0?t:t.substring(last+1);}
  static boolean file(Expression e,CompilationUnit unit){
    if(e instanceof ObjectCreationExpr)return simple(((ObjectCreationExpr)e).getType()).equals("File");
    if(e instanceof EnclosedExpr)return file(((EnclosedExpr)e).getInner(),unit);
    if(e instanceof CastExpr)return simple(((CastExpr)e).getType()).equals("File");
    if(e instanceof MethodCallExpr){String name=((MethodCallExpr)e).getNameAsString();
      if(Set.of("getParentFile","getAbsoluteFile","getCanonicalFile","getBaseFile","getFilesDir","getCacheDir").contains(name))return true;
      return unit.findAll(MethodDeclaration.class).stream().anyMatch(m->m.getNameAsString().equals(name)&&simple(m.getType()).equals("File"));}
    String name=e instanceof NameExpr?((NameExpr)e).getNameAsString():e instanceof FieldAccessExpr?((FieldAccessExpr)e).getNameAsString():"";
    if(!name.isEmpty()){
      // Resolve the nearest lexical declaration first (parameters and locals).
      Node scope=e;
      while(scope.getParentNode().isPresent()){
        scope=scope.getParentNode().get();
        if(scope instanceof MethodDeclaration||scope instanceof ConstructorDeclaration||scope instanceof LambdaExpr||scope instanceof ClassOrInterfaceDeclaration){
          List<Type> found=new ArrayList<>();
          for(Parameter p:scope.findAll(Parameter.class))if(p.getNameAsString().equals(name))found.add(p.getType());
          for(VariableDeclarator v:scope.findAll(VariableDeclarator.class))if(v.getNameAsString().equals(name))found.add(v.getType());
          if(!found.isEmpty())return found.stream().allMatch(t->simple(t).equals("File"));
        }
      }
      return unit.findAll(VariableDeclarator.class).stream().anyMatch(v->v.getNameAsString().equals(name)&&simple(v.getType()).equals("File"));
    }
    if(e instanceof ArrayAccessExpr){Expression array=((ArrayAccessExpr)e).getName();
      if(array instanceof NameExpr){String n=((NameExpr)array).getNameAsString();return unit.findAll(VariableDeclarator.class).stream().anyMatch(v->v.getNameAsString().equals(n)&&simple(v.getType()).equals("File[]"));}}
    return false;
  }
  static BlockStmt body(Node node){
    Node parent=node;
    while(parent.getParentNode().isPresent()){
      parent=parent.getParentNode().get();
      if(parent instanceof LambdaExpr){Statement b=((LambdaExpr)parent).getBody();
        if(!b.isBlockStmt())throw new IllegalStateException("Storage mutation in expression lambda: "+parent);return b.asBlockStmt();}
      if(parent instanceof MethodDeclaration)return ((MethodDeclaration)parent).getBody().orElseThrow();
      if(parent instanceof ConstructorDeclaration)return ((ConstructorDeclaration)parent).getBody();
      if(parent instanceof InitializerDeclaration)return ((InitializerDeclaration)parent).getBody();
    }
    throw new IllegalStateException("Storage operation outside a bounded producer: "+node);
  }
  static String quote(String s){return "\""+s.replace("\\","\\\\").replace("\"","\\\"").replace("\n","\\n").replace("\r","\\r").replace("\t","\\t")+"\"";}
  public static void main(String[] args)throws Exception{
    Path root=Path.of(args[0]),report=Path.of(args[1]);
    StaticJavaParser.getParserConfiguration().setLanguageLevel(ParserConfiguration.LanguageLevel.JAVA_17);
    List<String> receipts=new ArrayList<>();
    try(java.util.stream.Stream<Path> paths=Files.walk(root)){
      for(Path path:(Iterable<Path>)paths.filter(p->p.toString().endsWith(".java"))::iterator){
        String name=path.getFileName().toString().replace(".java","");
        if(name.equals("InfinityJavaWriteBarrier")||name.equals("InfinityJavaPersistence")||COORDINATOR.contains(name)||DIAGNOSTICS.contains(name))continue;
        String source=Files.readString(path);CompilationUnit unit=StaticJavaParser.parse(source);
        List<Edit> edits=new ArrayList<>();Set<BlockStmt> scopes=Collections.newSetFromMap(new IdentityHashMap<>());
        for(ObjectCreationExpr call:unit.findAll(ObjectCreationExpr.class)){
          if(simple(call.getType()).equals("FileOutputStream")){
            replace(edits,source,call.getType(),HELPER+".Output","file_output_adapter");scopes.add(body(call));
          }
          if(simple(call.getType()).equals("Thread")&&THREADS.contains(name)&&!call.getArguments().isEmpty()){
            Expression task=call.getArgument(0);
            int begin=offset(source,task.getRange().orElseThrow().begin),end=offset(source,task.getRange().orElseThrow().end)+1;
            edits.add(new Edit(begin,begin,HELPER+".task(","accepted_task_begin"));
            edits.add(new Edit(end,end,", "+quote(name)+")","accepted_task_end"));
          }
        }
        for(ClassOrInterfaceType type:unit.findAll(ClassOrInterfaceType.class)){
          if(type.getNameAsString().equals("AtomicFile"))replace(edits,source,type,HELPER+".Atomic","atomic_file_adapter");
        }
        for(MethodCallExpr call:unit.findAll(MethodCallExpr.class)){
          String method=call.getNameAsString();
          if(QUEUES.contains(name)&&method.equals("shutdownNow")&&call.getScope().isPresent()){
            String target=original(source,call.getScope().get());
            if(Set.of("executor","mIo","IO","CobraVisualRenderer.IO","pool").contains(target))
              replace(edits,source,call,HELPER+".shutdownNow("+target+")","accepted_task_cancel");
          }
          if(QUEUES.contains(name)&&Set.of("execute","submit").contains(method)&&call.getScope().isPresent()&&call.getArguments().size()==1){
            String target=original(source,call.getScope().get());
            if(Set.of("executor","mIo","IO","CobraVisualRenderer.IO","pool").contains(target)){
              Expression task=call.getArgument(0);
              int begin=offset(source,call.getRange().orElseThrow().begin),arg=offset(source,task.getRange().orElseThrow().begin),end=offset(source,call.getRange().orElseThrow().end)+1;
              edits.add(new Edit(begin,arg,HELPER+"."+method+"("+target+", ","accepted_task_adapter"));
              edits.add(new Edit(end-1,end,", "+quote(name)+")","accepted_task_owner"));
            }
          }
          if(method.equals("getSharedPreferences")){
            String context=call.getScope().map(s->original(source,s)).orElse("this");
            if(call.getArguments().size()!=2)throw new IllegalStateException("Unknown preferences overload");
            replace(edits,source,call,HELPER+".preferences("+context+", "+original(source,call.getArgument(0))+", "+original(source,call.getArgument(1))+")","preferences_adapter");
          }else if(MUTATIONS.contains(method)&&call.getScope().isPresent()&&file(call.getScope().get(),unit)){
            String target=original(source,call.getScope().get());
            String extra=call.getArguments().isEmpty()?"":", "+original(source,call.getArgument(0));
            replace(edits,source,call,HELPER+"."+(method.equals("renameTo")?"rename":method)+"("+target+extra+")","file_namespace_adapter");
            scopes.add(body(call));
          }else if(method.equals("rename")&&call.getScope().map(Object::toString).filter(s->s.equals("Os")||s.equals("android.system.Os")).isPresent()){
            replace(edits,source,call,HELPER+".renameOs("+original(source,call.getArgument(0))+", "+original(source,call.getArgument(1))+")","os_rename_adapter");scopes.add(body(call));
          }else if(method.equals("startWrite"))scopes.add(body(call));
        }
        int sequence=0;
        if(ENTRIES.contains(name))for(MethodDeclaration method:unit.findAll(MethodDeclaration.class)){
          if(Set.of("onCreate","onNewIntent").contains(method.getNameAsString())&&method.getBody().isPresent()){
            int position=offset(source,method.getBody().get().getRange().orElseThrow().begin)+1;
            edits.add(new Edit(position,position,"\n"+HELPER+".userEntry(this);\n","explicit_activity_entry"));
          }
        }
        for(BlockStmt scope:scopes){
          Range range=scope.getRange().orElseThrow();int start=offset(source,range.begin)+1,end=offset(source,range.end);
          if(!scope.getStatements().isEmpty()&&scope.getStatement(0).isExplicitConstructorInvocationStmt())start=offset(source,scope.getStatement(0).getRange().orElseThrow().end)+1;
          String owner=name+":"+range.begin.line;
          edits.add(new Edit(start,start,"\ntry ("+BARRIER+".Scope __infinitySave"+(sequence++)+" = "+BARRIER+".enter("+quote(owner)+")) {\n","transaction_begin"));
          edits.add(new Edit(end,end,"\n}\n","transaction_end"));
        }
        if(edits.isEmpty())continue;
        edits.sort(Comparator.comparingInt((Edit e)->e.start).thenComparingInt(e->e.end));
        int previous=-1;for(Edit edit:edits){if(edit.start<previous)throw new IllegalStateException("Overlapping source boundaries: "+path+":"+edit.start);previous=edit.end;}
        List<String> changes=new ArrayList<>();for(Edit e:edits)changes.add("{\"start\":"+e.start+",\"end\":"+e.end+",\"before\":"+quote(source.substring(e.start,e.end))+",\"after\":"+quote(e.value)+",\"reason\":"+quote(e.reason)+"}");
        StringBuilder result=new StringBuilder(source);for(int i=edits.size()-1;i>=0;i--){Edit e=edits.get(i);result.replace(e.start,e.end,e.value);}
        StaticJavaParser.parse(result.toString());Files.writeString(path,result);
        receipts.add("{\"path\":"+quote(root.relativize(path).toString())+",\"edits\":["+String.join(",",changes)+"]}");
      }
    }
    Files.writeString(report,"{\"files\":["+String.join(",",receipts)+"]}\n");
    System.out.println("Recorded Java persistence-only source transformations: "+receipts.size()+" files");
  }
}
