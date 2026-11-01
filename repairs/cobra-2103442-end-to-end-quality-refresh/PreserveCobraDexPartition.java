package org.jf.dexlib2.writer.pool;

import java.nio.file.*;
import java.util.*;
import org.jf.dexlib2.iface.ClassDef;

/** Build-only: retain the signed owner's exact class partition and untouched second DEX.
 * Uses the original writer's field/default checks and exact unoptimized class writer.
 */
public final class PreserveCobraDexPartition {
    public static void main(String[] args) throws Exception {
        ModuleDexWriter.require(args.length == 4, "out patch original-part0 original-part1");
        Path directory = Paths.get(args[0]); Files.createDirectories(directory);
        Map<String,ClassDef> first = ModuleDexWriter.read(args[2]);
        Map<String,ClassDef> second = ModuleDexWriter.read(args[3]);
        Map<String,ClassDef> patches = ModuleDexWriter.read(args[1]);
        for (Map.Entry<String,ClassDef> entry : patches.entrySet()) {
            String name = entry.getKey();
            ModuleDexWriter.require(!second.containsKey(name), "Protected second DEX modification: " + name);
            if (first.containsKey(name)) first.put(name, ModuleDexWriter.restoreDefaults(first.get(name), entry.getValue()));
            else {
                Set<String> reviewed = new HashSet<>();
                for (String suffix : new String[]{"", "$ClockFormat", "$State", "$Pair", "$ProgramFields", "$Snapshot", "$Entry"})
                    reviewed.add("Lcom/projectinfinity/kodi/CobraGuidePresentation" + suffix + ";");
                ModuleDexWriter.require(reviewed.contains(name), "Unreviewed new class " + name);
                first.put(name, entry.getValue());
            }
        }
        ModuleDexWriter.ExactPool pool = new ModuleDexWriter.ExactPool();
        for (ClassDef definition : first.values()) pool.internClass(definition);
        ModuleDexWriter.require(!pool.hasOverflowed(65535), "Original DEX partition exceeds format capacity");
        ModuleDexWriter.write(pool, directory.resolve("part-0.dex"), new ArrayList<>(first.values()));
        Files.copy(Paths.get(args[3]), directory.resolve("part-1.dex"));
        System.out.println("ORIGINAL_PARTITION_PRESERVED first=" + first.size() + " second=" + second.size());
    }
}
