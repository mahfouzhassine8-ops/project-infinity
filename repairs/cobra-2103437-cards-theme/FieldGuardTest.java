package org.jf.dexlib2.writer.pool;
import java.util.*;
import org.jf.dexlib2.iface.*;
import org.jf.dexlib2.immutable.*;
public class FieldGuardTest {
 static final String CARD="Lcom/projectinfinity/kodi/CobraCardsLayout$PanelSurface;",TYPE="Lcom/projectinfinity/kodi/CobraCardsTheme$Colors;";
 static Field field(String c,String name,String type){return new ImmutableField(c,name,type,0,null,Collections.emptySet(),Collections.emptySet());}
 static ClassDef cls(String name,Field... fields){return new ImmutableClassDef(name,0,"Ljava/lang/Object;",Collections.emptyList(),null,Collections.emptySet(),Arrays.asList(fields),Collections.emptyList());}
 static void rejected(ClassDef a,ClassDef b){try{ModuleDexWriter.restoreDefaults(a,b);}catch(IllegalStateException expected){return;}throw new AssertionError("Unexpected field mutation accepted: "+a.getType());}
 public static void main(String[] args){
  ModuleDexWriter.restoreDefaults(cls(CARD),cls(CARD,field(CARD,"palette",TYPE)));
  String foreign="Lcom/projectinfinity/kodi/InfinityLiveActivity;";rejected(cls(foreign),cls(foreign,field(foreign,"palette",TYPE)));
  rejected(cls(CARD),cls(CARD,field(CARD,"palette","I")));
  rejected(cls(CARD),cls(CARD,field(CARD,"palette",TYPE),field(CARD,"other","I")));
  rejected(cls(CARD,field(CARD,"keep","I")),cls(CARD,field(CARD,"palette",TYPE)));
  System.out.println("PASS 1 exact Cards field admission; 4 negative mutation controls");
 }
}
