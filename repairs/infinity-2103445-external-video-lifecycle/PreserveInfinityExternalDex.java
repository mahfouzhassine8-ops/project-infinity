package org.jf.dexlib2.writer.pool;
import java.nio.file.*;import java.util.*;import org.jf.dexlib2.iface.ClassDef;
/** Build only: exact original definitions and encoded field defaults, no optimizer. */
public final class PreserveInfinityExternalDex {
 public static void main(String[] args)throws Exception {
  ModuleDexWriter.require(args.length==3,"output patch baseline");
  Map<String,ClassDef> original=ModuleDexWriter.read(args[2]),patch=ModuleDexWriter.read(args[1]);
  Set<String> existing=new HashSet<>(Arrays.asList("Lcom/projectinfinity/kodi/Main;","Lcom/projectinfinity/kodi/Main$3;"));
  Set<String> added=new HashSet<>(Arrays.asList("Lcom/projectinfinity/kodi/InfinityExternalVideoIntents;","Lcom/projectinfinity/kodi/InfinityExternalVideoIntents$State;"));
  Set<String> expected=new HashSet<>(existing);expected.addAll(added);ModuleDexWriter.require(patch.keySet().equals(expected),"Exact external-intent class boundary");
  for(String name:existing){ModuleDexWriter.require(original.containsKey(name),"Baseline class missing");original.put(name,ModuleDexWriter.restoreDefaults(original.get(name),patch.get(name)));}
  for(String name:added){ModuleDexWriter.require(!original.containsKey(name),"New class collision");original.put(name,patch.get(name));}
  ModuleDexWriter.ExactPool pool=new ModuleDexWriter.ExactPool();for(ClassDef c:original.values())pool.internClass(c);
  ModuleDexWriter.require(!pool.hasOverflowed(65535),"DEX format capacity");ModuleDexWriter.write(pool,Paths.get(args[0]),new ArrayList<>(original.values()));
 }
}
