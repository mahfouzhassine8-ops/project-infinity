package com.projectinfinity.kodi;

import java.util.WeakHashMap;

/** Cobra-owned liveness, separate from durability of its individual writes. */
public final class CobraRuntimeLease {
  private static final Object LOCK=new Object();
  private static final WeakHashMap<Object,Boolean> owners=new WeakHashMap<>();
  private CobraRuntimeLease() {}
  public static void acquire(Object owner) {
    if(owner==null)throw new NullPointerException();
    // Match the container's lock order. A newly created Cobra owner revokes
    // only Cobra's old receipt, never Infinity's admission or saved state.
    synchronized(CobraJavaWriteBarrier.ownerLock()) {
      synchronized(LOCK){owners.put(owner,Boolean.TRUE);CobraJavaWriteBarrier.userEntry();}
    }
  }
  public static void release(Object owner) { synchronized(LOCK){owners.remove(owner);} }
  public static Object ownerLock(){return LOCK;}
  public static boolean active(){synchronized(LOCK){return !owners.isEmpty();}}
}
