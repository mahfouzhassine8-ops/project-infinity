/* Build-time DEX packaging adapter. Not packaged into Infinity.
 * Uses version-pinned dexlib2 2.5.2 writer extension types. This build-only
 * adapter shares the writer package because PoolClassDef is package-private.
 * Protected definitions come directly from the signed APK's original DEX.
 * No preservation comparison is relaxed or normalized by this adapter.
 */
package org.jf.dexlib2.writer.pool;

import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;
import org.jf.dexlib2.DexFileFactory;
import org.jf.dexlib2.Opcodes;
import org.jf.dexlib2.iface.ClassDef;
import org.jf.dexlib2.iface.DexFile;
import org.jf.dexlib2.iface.Field;
import org.jf.dexlib2.iface.value.ArrayEncodedValue;
import org.jf.dexlib2.iface.value.EncodedValue;
import org.jf.dexlib2.immutable.value.ImmutableArrayEncodedValue;
import org.jf.dexlib2.writer.io.FileDataStore;

public final class PreserveDexFields95 {
    private static final String TARGET =
            "Lcom/projectinfinity/kodi/InfinityInstalledCheckpointInstaller;";

    private static final java.util.Set<String> TARGETS = new java.util.HashSet<>(java.util.Arrays.asList(TARGET,
        "Lcom/projectinfinity/kodi/InfinityAndroidKeyboard$Editor;",
        "Lcom/projectinfinity/kodi/InfinityInstalledCodeEvidence;"));
    private static boolean added(String name) { return name.startsWith("Lcom/projectinfinity/kodi/InfinitySearch95") || name.startsWith("Lcom/projectinfinity/kodi/InfinityEvidence95"); }
    private PreserveDexFields95() {}

    private static void require(boolean condition, String message) {
        if (!condition) throw new IllegalStateException(message);
    }

    private static ArrayEncodedValue originalInitializers(PoolClassDef definition) {
        List<EncodedValue> values = new ArrayList<>();
        boolean ended = false;
        for (Field field : definition.getStaticFields()) {
            EncodedValue value = field.getInitialValue();
            if (value == null) {
                ended = true;  // No encoded value, not the encoded null constant.
            } else {
                require(!ended, "Non-contiguous original static values: " + definition.getType());
                // Retain explicitly encoded null, false and zero, including
                // the original vector's exact length.
                values.add(value);
            }
        }
        return values.isEmpty() ? null : new ImmutableArrayEncodedValue(values);
    }

    private static final class ExactValuePool extends DexPool {
        ExactValuePool(Opcodes opcodes) { super(opcodes); }

        @Override protected SectionProvider getSectionProvider() {
            return new DexPoolSectionProvider() {
                @Override public ClassPool getClassSection() {
                    return new ClassPool(ExactValuePool.this) {
                        @Override public ArrayEncodedValue getStaticInitializers(PoolClassDef definition) {
                            return originalInitializers(definition);
                        }
                    };
                }
            };
        }
    }

    private static Map<String, ClassDef> classes(DexFile dex) {
        Map<String, ClassDef> result = new TreeMap<>();
        for (ClassDef definition : dex.getClasses()) {
            require(result.put(definition.getType(), definition) == null, "Duplicate class");
        }
        require(result.containsKey(TARGET), "Original startup class missing");
        return result;
    }

    private static Map<String, Field> fields(ClassDef definition) {
        Map<String, Field> result = new HashMap<>();
        for (Field field : definition.getFields()) {
            require(result.put(field.getName() + ":" + field.getType(), field) == null,
                    "Duplicate field in " + definition.getType());
        }
        return result;
    }

    private static int verifyFields(Map<String, ClassDef> original, Map<String, ClassDef> candidate) {
        require(candidate.keySet().containsAll(original.keySet()), "Original class missing");
        for(String name:candidate.keySet()) require(original.containsKey(name)||added(name), "Unapproved added class");
        int verified = 0;
        for (String type : original.keySet()) {
            Map<String, Field> before = fields(original.get(type));
            Map<String, Field> after = fields(candidate.get(type));
            require(before.keySet().equals(after.keySet()), "Field set changed: " + type);
            for (String name : before.keySet()) {
                Field a = before.get(name);
                Field b = after.get(name);
                require(a.getAccessFlags() == b.getAccessFlags(), "Field flags changed: " + type + name);
                require(a.getAnnotations().equals(b.getAnnotations()), "Field annotations changed");
                require(a.getHiddenApiRestrictions().equals(b.getHiddenApiRestrictions()),
                        "Hidden API field restrictions changed");
                require(Objects.equals(a.getInitialValue(), b.getInitialValue()),
                        "Encoded field value/presence changed: " + type + name);
                verified++;
            }
        }
        return verified;
    }

    public static void main(String[] arguments) throws Exception {
        require(arguments.length == 4, "original.dex assembled.dex preserved.dex minimum-api required");
        File originalFile = new File(arguments[0]);
        File assembledFile = new File(arguments[1]);
        File output = new File(arguments[2]);
        require(originalFile.isFile() && assembledFile.isFile(), "DEX inputs missing");
        require(!output.exists(), "Refusing output overwrite");
        Opcodes opcodes = Opcodes.forApi(Integer.parseInt(arguments[3]));
        DexFile originalDex = DexFileFactory.loadDexFile(originalFile, opcodes);
        Map<String, ClassDef> original = classes(originalDex);
        Map<String, ClassDef> assembled = classes(DexFileFactory.loadDexFile(assembledFile, opcodes));
        require(assembled.keySet().containsAll(original.keySet()), "Original class missing");
        for(String name:assembled.keySet()) require(original.containsKey(name)||added(name), "Unapproved added class");
        ExactValuePool pool = new ExactValuePool(originalDex.getOpcodes());
        for (Map.Entry<String, ClassDef> item : original.entrySet()) {
            // Protected classes never come from transformed assembler definitions.
            // Only the reviewed startup class is replaced.
            ClassDef selected = TARGETS.contains(item.getKey()) ? assembled.get(item.getKey()) : item.getValue();
            pool.internClass(selected);
        }
        for(String name:assembled.keySet()) if(!original.containsKey(name)) pool.internClass(assembled.get(name));
        try {
            FileDataStore store = new FileDataStore(output);
            try {
                pool.writeTo(store);
            } finally {
                store.close();
            }
            Map<String, ClassDef> checked = classes(DexFileFactory.loadDexFile(output, opcodes));
            int verified = verifyFields(original, checked);
            System.out.println("PRESERVED_CLASSES=" + (original.size() - TARGETS.size()));
            System.out.println("VERIFIED_EXACT_FIELD_DEFINITIONS=" + verified);
            System.out.println("EXPLICIT_INITIALIZER_PRESENCE_AND_VALUES_PRESERVED=true");
        } catch (Exception error) {
            if (output.exists() && !output.delete()) {
                throw new IllegalStateException("Failed DEX must not be published: " + output, error);
            }
            throw error;
        }
    }
}
