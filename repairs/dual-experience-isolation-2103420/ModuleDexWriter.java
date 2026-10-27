// PoolClassDef is package-private in the pinned build-only dexlib2 writer.
package org.jf.dexlib2.writer.pool;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import org.jf.dexlib2.DexFileFactory;
import org.jf.dexlib2.Opcodes;
import org.jf.dexlib2.iface.ClassDef;
import org.jf.dexlib2.iface.Field;
import org.jf.dexlib2.iface.value.*;
import org.jf.dexlib2.immutable.ImmutableClassDef;
import org.jf.dexlib2.immutable.ImmutableField;
import org.jf.dexlib2.immutable.value.ImmutableArrayEncodedValue;
import org.jf.dexlib2.writer.io.FileDataStore;
import org.jf.dexlib2.writer.pool.*;

/** Original definitions are copied directly from their signed-baseline DEX.
 * Only explicit delta classes use assembler definitions. No optimizer runs.
 */
public final class ModuleDexWriter {
  static void require(boolean v,String why){if(!v)throw new IllegalStateException(why);}
  static final Opcodes OPS=Opcodes.forApi(21);
  static final class ExactPool extends DexPool {
    ExactPool(){super(OPS);}
    @Override protected SectionProvider getSectionProvider(){
      return new DexPoolSectionProvider(){
        @Override public ClassPool getClassSection(){return new ClassPool(ExactPool.this){
          @Override public ArrayEncodedValue getStaticInitializers(PoolClassDef c){
            List<EncodedValue> values=new ArrayList<>();boolean ended=false;
            for(Field f:c.getStaticFields()){
              if(f.getInitialValue()==null)ended=true;
              else {require(!ended,"Noncontiguous encoded defaults: "+c.getType());values.add(f.getInitialValue());}
            }
            return values.isEmpty()?null:new ImmutableArrayEncodedValue(values);
          }
        };}
      };
    }
  }
  static Map<String,ClassDef> read(String file)throws Exception{
    Map<String,ClassDef> m=new TreeMap<>();
    for(ClassDef c:DexFileFactory.loadDexFile(new File(file),OPS).getClasses())
      require(m.put(c.getType(),c)==null,"Duplicate class: "+c.getType());
    return m;
  }
  static Map<String,Field> fields(ClassDef c){
    Map<String,Field> m=new TreeMap<>();
    for(Field f:c.getFields())require(m.put(f.getName(),f)==null,"Ambiguous origin field");
    return m;
  }
  static boolean defaultValue(EncodedValue v){
    return v instanceof NullEncodedValue || v instanceof BooleanEncodedValue&&!((BooleanEncodedValue)v).getValue()
      || v instanceof ByteEncodedValue&&((ByteEncodedValue)v).getValue()==0
      || v instanceof CharEncodedValue&&((CharEncodedValue)v).getValue()==0
      || v instanceof ShortEncodedValue&&((ShortEncodedValue)v).getValue()==0
      || v instanceof IntEncodedValue&&((IntEncodedValue)v).getValue()==0
      || v instanceof LongEncodedValue&&((LongEncodedValue)v).getValue()==0
      || v instanceof FloatEncodedValue&&Float.floatToRawIntBits(((FloatEncodedValue)v).getValue())==0
      || v instanceof DoubleEncodedValue&&Double.doubleToRawLongBits(((DoubleEncodedValue)v).getValue())==0;
  }
  static ClassDef restoreDefaults(ClassDef original,ClassDef changed){
    Map<String,Field> old=fields(original);List<Field> revised=new ArrayList<>();
    require(old.keySet().equals(fields(changed).keySet()),"Unreviewed field-set mutation "+changed.getType());
    for(Field f:changed.getFields()){
      EncodedValue value=f.getInitialValue(),prior=old.get(f.getName()).getInitialValue();
      if(value==null&&prior!=null){require(defaultValue(prior),"Lost non-default initializer");value=prior;}
      revised.add(new ImmutableField(f.getDefiningClass(),f.getName(),f.getType(),f.getAccessFlags(),value,
                    f.getAnnotations(),f.getHiddenApiRestrictions()));
    }
    return new ImmutableClassDef(changed.getType(),changed.getAccessFlags(),changed.getSuperclass(),
          changed.getInterfaces(),changed.getSourceFile(),changed.getAnnotations(),revised,changed.getMethods());
  }
  public static void main(String[] args)throws Exception{
    require(args.length>=5,"out assignments.tsv origins.tsv patch.dex helper.dex originals... required");
    Path out=new File(args[0]).toPath();Files.createDirectory(out);
    Map<String,String> owners=new TreeMap<>(),origins=new TreeMap<>();
    for(String line:Files.readAllLines(new File(args[1]).toPath())){String[] p=line.split("\t");require(p.length==2,"Owner row");require(owners.put(p[0],p[1])==null,"Duplicate assignment");}
    for(String line:Files.readAllLines(new File(args[2]).toPath())){String[] p=line.split("\t");require(p.length==2,"Origin row");origins.put(p[0],p[1]);}
    Map<String,ClassDef> original=new TreeMap<>();
    for(int i=5;i<args.length;i++)for(Map.Entry<String,ClassDef> e:read(args[i]).entrySet())
      require(original.put(e.getKey(),e.getValue())==null,"Duplicate original");
    Map<String,ClassDef> selected=new TreeMap<>(original),patched=read(args[3]);
    for(Map.Entry<String,ClassDef> e:read(args[4]).entrySet())require(patched.put(e.getKey(),e.getValue())==null,"Duplicate patch");
    for(Map.Entry<String,ClassDef> e:patched.entrySet()){
      String origin=origins.get(e.getKey());
      if(origin!=null){require(original.containsKey(origin),"Unknown origin");selected.put(e.getKey(),restoreDefaults(original.get(origin),e.getValue()));}
      else {require(!original.containsKey(e.getKey()),"Replacement lacks exact origin");selected.put(e.getKey(),e.getValue());}
    }
    require(selected.keySet().equals(owners.keySet()),"Ownership must cover exact selected class set");
    Map<String,List<ClassDef>> groups=new TreeMap<>();
    for(ClassDef c:selected.values())groups.computeIfAbsent(owners.get(c.getType()),k->new ArrayList<>()).add(c);
    int dexCount=0;
    for(Map.Entry<String,List<ClassDef>> group:groups.entrySet()){
      require(group.getKey().matches("[A-Z_]+"),"Invalid owner");
      Path dir=out.resolve(group.getKey());Files.createDirectory(dir);
      List<ClassDef> pending=new ArrayList<>();ExactPool pool=new ExactPool();int part=0;
      for(ClassDef c:group.getValue()){
        pool.mark();pool.internClass(c);
        if(pool.hasOverflowed(60000)){
          pool.reset();require(!pending.isEmpty(),"Single class exceeds DEX capacity");
          write(pool,dir.resolve("part-"+(part++)+".dex"),pending);dexCount++;
          pending.clear();pool=new ExactPool();pool.internClass(c);require(!pool.hasOverflowed(60000),"Class overflow");
        }
        pending.add(c);
      }
      if(!pending.isEmpty()){write(pool,dir.resolve("part-"+part+".dex"),pending);dexCount++;}
    }
    System.out.println("CLASSES="+selected.size()+" OWNER_DEX_FILES="+dexCount);
  }
  static void write(ExactPool pool,Path path,List<ClassDef> expected)throws Exception{
    FileDataStore store=new FileDataStore(path.toFile());try{pool.writeTo(store);}finally{store.close();}
    Map<String,ClassDef> actual=read(path.toString());require(actual.size()==expected.size(),"Lost class");
    for(ClassDef c:expected){Map<String,Field> before=fields(c),after=fields(actual.get(c.getType()));
      require(before.keySet().equals(after.keySet()),"Lost field");
      for(String key:before.keySet())require(Objects.equals(before.get(key).getInitialValue(),after.get(key).getInitialValue()),"Changed encoded default: "+c.getType()+key);
    }
  }
}
