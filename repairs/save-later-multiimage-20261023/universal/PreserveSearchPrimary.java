/* Build-only DEX splitter. No runtime code from this adapter is packaged. */
package org.jf.dexlib2.writer.pool;

import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import org.jf.dexlib2.DexFileFactory;
import org.jf.dexlib2.Opcodes;
import org.jf.dexlib2.dexbacked.DexBackedDexFile;
import org.jf.dexlib2.iface.ClassDef;
import org.jf.dexlib2.iface.Field;
import org.jf.dexlib2.iface.value.ArrayEncodedValue;
import org.jf.dexlib2.iface.value.EncodedValue;
import org.jf.dexlib2.immutable.value.ImmutableArrayEncodedValue;
import org.jf.dexlib2.writer.io.FileDataStore;

public final class PreserveSearchPrimary {
    private static final String HELPER="Lcom/projectinfinity/kodi/InfinitySearch101";
    private PreserveSearchPrimary() {}
    private static void require(boolean value,String message) {
        if(!value)throw new IllegalStateException(message);
    }
    private static boolean search(String name) {
        return name.equals(HELPER+";") || name.startsWith(HELPER+"$");
    }
    private static ArrayEncodedValue initializers(PoolClassDef definition) {
        List<EncodedValue> values=new ArrayList<>();boolean ended=false;
        for(Field field:definition.getStaticFields()) {
            EncodedValue value=field.getInitialValue();
            if(value==null)ended=true;
            else {require(!ended,"Non-contiguous static values");values.add(value);}
        }
        return values.isEmpty()?null:new ImmutableArrayEncodedValue(values);
    }
    private static final class ExactValuePool extends DexPool {
        ExactValuePool(Opcodes opcodes) {super(opcodes);}
        @Override protected SectionProvider getSectionProvider() {
            return new DexPoolSectionProvider() {
                @Override public ClassPool getClassSection() {
                    return new ClassPool(ExactValuePool.this) {
                        @Override public ArrayEncodedValue getStaticInitializers(PoolClassDef definition) {
                            return initializers(definition);
                        }
                    };
                }
            };
        }
    }
    public static void main(String[] args)throws Exception {
        require(args.length==3,"input.dex output.dex minimum-api required");
        File input=new File(args[0]),output=new File(args[1]);
        require(input.isFile()&&!output.exists(),"Invalid splitter paths");
        Opcodes opcodes=Opcodes.forApi(Integer.parseInt(args[2]));
        DexBackedDexFile original=DexFileFactory.loadDexFile(input,opcodes);
        ExactValuePool pool=new ExactValuePool(original.getOpcodes());
        // Removing a helper must not renumber any original string. Keeping
        // unused entries also prevents protected const-string opcode widening.
        for(String value:original.getStringSection())pool.stringSection.intern(value);
        Map<String,ClassDef> kept=new TreeMap<>();int removed=0;
        for(ClassDef definition:original.getClasses()) {
            if(search(definition.getType())){removed++;continue;}
            require(kept.put(definition.getType(),definition)==null,"Duplicate class");
            // Every retained class comes from the original, never an assembler.
            pool.internClass(definition);
        }
        require(removed>1,"Original Search helper family missing");
        try {
            FileDataStore store=new FileDataStore(output);
            try{pool.writeTo(store);}finally{store.close();}
            DexBackedDexFile checked=DexFileFactory.loadDexFile(output,opcodes);
            require(checked.getStringSection().equals(original.getStringSection()),"String pool changed");
            require(checked.getClasses().size()==kept.size(),"Class count changed");
            for(ClassDef definition:checked.getClasses())
                require(kept.containsKey(definition.getType()),"Unapproved primary class");
            System.out.println("PROTECTED_CLASSES="+kept.size());
            System.out.println("SEARCH_CLASSES_RELOCATED="+removed);
            System.out.println("ORIGINAL_STRING_POOL_IDENTICAL=true");
        }catch(Exception error){if(output.exists())output.delete();throw error;}
    }
}
