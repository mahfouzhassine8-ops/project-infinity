package com.projectinfinity.kodi;
import java.io.*;import java.lang.reflect.*;import java.util.*;import java.util.concurrent.*;
public class DeliveryProbe {
 static int checks;static void need(boolean x,String why){checks++;if(!x)throw new AssertionError(why);}
 static sun.misc.Unsafe memory;static{try{Field f=sun.misc.Unsafe.class.getDeclaredField("theUnsafe");f.setAccessible(true);memory=(sun.misc.Unsafe)f.get(null);}catch(Exception e){throw new ExceptionInInitializerError(e);}}
 static void field(Object x,String name,Object value)throws Exception{Field f=x.getClass().getDeclaredField(name);f.setAccessible(true);f.set(x,value);}
 static InfinityCastHardwareVideo tracker()throws Exception{InfinityCastHardwareVideo x=(InfinityCastHardwareVideo)memory.allocateInstance(InfinityCastHardwareVideo.class);field(x,"delivery",new TreeMap<>());return x;}
 static void sample(InfinityCastHardwareVideo x,int index,long millis)throws Exception{field(x,"begin",index*2000000L);field(x,"end",(index+1)*2000000L);x.qualifyDelivery(millis,2000);}
 static void rejected(RunnableIO work,String reason)throws Exception{try{work.run();throw new AssertionError("accepted "+reason);}catch(IOException e){need(e.getMessage().equals(reason),e.getMessage());}}
 interface RunnableIO{void run()throws Exception;}
 public static void main(String[]args)throws Exception{
  InfinityCastHardwareVideo x=tracker();sample(x,0,2500);sample(x,1,300);sample(x,2,300);sample(x,3,300);x.requireDelivery(0,8000000,0,100000000);need(true,"cold cue plus measured contiguous window");
  rejected(()->x.requireDelivery(0,8000000,1000000,100000000),"cast_hw_delivery_window_invalid");sample(x,4,300);x.requireDelivery(0,10000000,1000000,100000000);need(true,"actual five-cue nonaligned window");
  InfinityCastHardwareVideo gap=tracker();sample(gap,0,300);sample(gap,2,300);sample(gap,3,300);rejected(()->gap.requireDelivery(0,8000000,0,100000000),"cast_hw_delivery_not_buffered");sample(gap,1,300);gap.requireDelivery(0,8000000,0,100000000);
  for(int n=0;n<20;n++)sample(gap,1,300);Field map=gap.getClass().getDeclaredField("delivery");map.setAccessible(true);need(((Map<?,?>)map.get(gap)).size()==4,"repeated regeneration gives no duration credit");rejected(()->sample(gap,3,8000),"cast_hw_delivery_not_realtime");
  InfinityCastHardwareVideo edge=tracker();sample(edge,0,4500);sample(edge,1,1);sample(edge,2,1);sample(edge,3,1);sample(edge,4,4500);rejected(()->edge.requireDelivery(0,10000000,1000000,100000000),"cast_hw_delivery_not_realtime");
  // The ticket is the actual production abandoned-result protocol, not a mirror.
  Class<?> ticket=Class.forName("com.projectinfinity.kodi.InfinityCastRemux$Ticket");Constructor<?> construct=ticket.getDeclaredConstructor(Callable.class);construct.setAccessible(true);Method abandon=ticket.getDeclaredMethod("abandon");abandon.setAccessible(true);
  for(boolean before:new boolean[]{true,false}){InfinityCastResource.Store store=new InfinityCastResource.Store();InfinityCastResource resource=store.create(0);resource.append(new byte[]{1},1);resource.seal(false);Object owned=construct.newInstance((Callable<Object>)()->store.pin(resource));if(before)abandon.invoke(owned);((Callable<?>)owned).call();if(!before)abandon.invoke(owned);store.close();need(store.reserved==0,"late result lease retired");}
  System.out.println("PASS_DELIVERY_AND_ABANDONED_RESULT "+checks);
 }
}
