package com.projectinfinity.kodi;

import android.app.Activity;
import java.lang.reflect.Field;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;
import java.util.TimeZone;
import java.util.WeakHashMap;

/** Cobra presentation only. No player, provider, persistence, worker or view ownership. */
public final class CobraGuidePresentation {
 private CobraGuidePresentation() {}
 private static final ThreadLocal<ClockFormat> CLOCK = new ThreadLocal<ClockFormat>();
 static final class ClockFormat {
  final SimpleDateFormat format = new SimpleDateFormat("EEE MMM d • h:mm a", Locale.US);
  final Date date = new Date();
  TimeZone zone;
 }
 public static String time(long timestamp) {
  ClockFormat clock=CLOCK.get();
  if(clock==null){clock=new ClockFormat();CLOCK.set(clock);}
  TimeZone zone=TimeZone.getDefault();
  if(!zone.equals(clock.zone)){clock.format.setTimeZone(zone);clock.zone=zone;}
  clock.date.setTime(timestamp);
  return clock.format.format(clock.date);
 }

 private static final int MAX_ENTRIES=32,MAX_INPUT_PROGRAMS=16384,MAX_SINGLE_INPUT=4096;
 // A state contains programme references only: it cannot retain its weak Activity key.
 private static final WeakHashMap<Activity,State> STATES=new WeakHashMap<Activity,State>();
 static final class State {
  final LinkedHashMap<Pair,Entry> entries=new LinkedHashMap<Pair,Entry>(32,.75f,true);
  int retained;
 }
 static final class Pair {
  final ArrayList first,second;
  Pair(ArrayList a,ArrayList b){first=a;second=b;}
  public int hashCode(){return 31*System.identityHashCode(first)+System.identityHashCode(second);}
  public boolean equals(Object other){return other instanceof Pair&&((Pair)other).first==first&&((Pair)other).second==second;}
 }
 static final class ProgramFields {
  final Field start,stop,title;
  ProgramFields(Class<?> type) throws ReflectiveOperationException {
   start=type.getDeclaredField("start");stop=type.getDeclaredField("stop");title=type.getDeclaredField("title");
   start.setAccessible(true);stop.setAccessible(true);title.setAccessible(true);
  }
 }
 static final class Snapshot {
  final Object[] programs,titles;
  final long[] starts,stops;
  final ProgramFields fields;
  Snapshot(ArrayList input) throws ReflectiveOperationException {
   programs=input.toArray();titles=new Object[programs.length];starts=new long[programs.length];stops=new long[programs.length];
   fields=programs.length==0?null:new ProgramFields(programs[0].getClass());
   for(int i=0;i<programs.length;i++){starts[i]=fields.start.getLong(programs[i]);stops[i]=fields.stop.getLong(programs[i]);titles[i]=fields.title.get(programs[i]);}
  }
  boolean matches(ArrayList input) throws IllegalAccessException {
   if(input.size()!=programs.length)return false;
   for(int i=0;i<programs.length;i++){
    Object p=input.get(i);if(p!=programs[i]||fields.start.getLong(p)!=starts[i]||fields.stop.getLong(p)!=stops[i])return false;
    Object title=fields.title.get(p);if(title!=titles[i]&&(title==null||!title.equals(titles[i])))return false;
   }
   return true;
  }
 }
 static final class Entry {
  final Snapshot first,second;
  final ArrayList merged;
  final int count;
  Entry(ArrayList a,ArrayList b,ArrayList result) throws ReflectiveOperationException {
   first=new Snapshot(a);second=new Snapshot(b);merged=result;count=a.size()+b.size();
  }
 }
 private static ArrayList original(Activity owner,ArrayList first,ArrayList second) {
  return (ArrayList)CobraArrange.ownedCall(owner,"cobraMergeProgrammeRanges",new Class<?>[]{java.util.List.class,java.util.List.class},first,second);
 }
 /** Only cobraNextProgram's private read path may consume this projection.
  * Every input object/order/start/stop/title is checked, including same-size edits.
  * Description/other metadata remains live through the original programme objects.
  * The result is never exposed to callers that can mutate a schedule list.
  */
 public static ArrayList nextPrograms(Activity owner,ArrayList first,ArrayList second) {
  int count=first.size()+second.size();
  if(count>MAX_SINGLE_INPUT)return original(owner,first,second);
  synchronized(STATES){
   State state=STATES.get(owner);if(state==null){state=new State();STATES.put(owner,state);}
   Pair key=new Pair(first,second);Entry old=state.entries.get(key);
   try {
    if(old!=null&&old.first.matches(first)&&old.second.matches(second))return old.merged;
    ArrayList result=original(owner,first,second);
    Entry entry=new Entry(first,second,result);
    if(old!=null){state.entries.remove(key);state.retained-=old.count;}
    Iterator<Map.Entry<Pair,Entry>> iterator=state.entries.entrySet().iterator();
    while(iterator.hasNext()&&(state.entries.size()>=MAX_ENTRIES||state.retained+count>MAX_INPUT_PROGRAMS)){
     state.retained-=iterator.next().getValue().count;iterator.remove();
    }
    state.entries.put(key,entry);state.retained+=count;return result;
   }catch(ReflectiveOperationException e){throw new IllegalStateException("Cobra programme presentation contract",e);}
  }
 }
}
