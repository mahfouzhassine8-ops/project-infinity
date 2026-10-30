package com.projectinfinity.kodi;

import android.app.Application;
import android.content.Context;
import android.content.SharedPreferences;
import java.lang.reflect.*;
import java.util.*;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicReference;
import org.json.*;
import org.junit.*;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;

/** Same actual public FeatureRuntime APIs on baseline and parsed-data prototype. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,
        instrumentedPackages={"com.projectinfinity.kodi"})
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraProfileDataReuseTest {
    static final String PROFILES="[{\"id\":\"default\",\"adult_locked\":false},{\"id\":\"locked\",\"adult_locked\":true}]";
    static boolean expectHelper(){return Boolean.parseBoolean(System.getProperty("profile.helper.expected","false"));}
    static ThreadLocal<?> cache() throws Exception {
        try {
            Class<?> helper=Class.forName("com.projectinfinity.kodi.CobraProfileDataReuse");
            assertTrue("Unexpected helper in exact baseline",expectHelper());
            Field f=helper.getDeclaredField("LOCAL");f.setAccessible(true);return (ThreadLocal<?>)f.get(null);
        } catch(ClassNotFoundException absent){assertFalse("Prototype helper missing",expectHelper());return null;}
    }
    @Before public void isolatePrivateTestThreadEntry()throws Exception{ThreadLocal<?> c=cache();if(c!=null)c.remove();}
    static final class Fixture implements InvocationHandler {
        final InfinityCobraFeatureRuntime feature;
        final SharedPreferences real;
        final List<String> reads=Collections.synchronizedList(new ArrayList<String>());
        int writes;
        boolean nullActive,nullRaw;
        Fixture()throws Exception{
            Context context=RuntimeEnvironment.getApplication();
            feature=new InfinityCobraFeatureRuntime(context);
            real=context.getSharedPreferences("profile-reuse-"+UUID.randomUUID(),Context.MODE_PRIVATE);
            real.edit().putString("active_profile","default").putString("profiles",PROFILES).commit();
            SharedPreferences forwarding=(SharedPreferences)Proxy.newProxyInstance(SharedPreferences.class.getClassLoader(),new Class<?>[]{SharedPreferences.class},this);
            Field prefs=InfinityCobraFeatureRuntime.class.getDeclaredField("prefs");prefs.setAccessible(true);prefs.set(feature,forwarding);
        }
        public Object invoke(Object proxy,Method method,Object[] args)throws Throwable{
            if(method.getName().equals("edit"))writes++;
            if(method.getName().equals("getString")){
                String key=(String)args[0];reads.add(key);
                if(key.equals("active_profile")&&nullActive)return null;
                if(key.equals("profiles")&&nullRaw)return null;
            }
            try{return method.invoke(real,args);}catch(InvocationTargetException e){throw e.getCause();}
        }
        void raw(String value){real.edit().putString("profiles",value).commit();}
        void id(String value){real.edit().putString("active_profile",value).commit();}
        boolean read(){
            reads.clear();writes=0;
            try{return feature.adultLocked();}
            finally{
                assertEquals("Original fresh read order/frequency",Arrays.asList("active_profile","profiles"),new ArrayList<>(reads));
                assertEquals("Data reuse helper must never edit preferences",0,writes);
            }
        }
    }
    @Test public void currentRawAndActiveIdAreReadFreshInOriginalOrder()throws Exception{
        Fixture f=new Fixture();assertFalse(f.read());Object first=cache()==null?null:cache().get();
        assertTrue(f.feature.unlockAndSelectProfile("locked",""));assertTrue(f.read());
        if(expectHelper())assertSame("ID selection must re-evaluate policy over same immutable raw data",first,cache().get());
        f.raw("[{\"id\":\"locked\",\"adult_locked\":false}]");assertFalse(f.read());
        if(expectHelper())assertNotSame("Raw edit must replace private parsed snapshot",first,cache().get());
        f.raw(PROFILES);assertTrue(f.read());assertTrue(f.feature.unlockAndSelectProfile("default",""));assertFalse(f.read());
    }
    @Test public void publicProfilesRemainIndependentMutableCopies()throws Exception{
        Fixture f=new Fixture();f.id("locked");assertTrue(f.read());Object prior=cache()==null?null:cache().get();
        JSONArray first=f.feature.profiles(),second=f.feature.profiles();assertNotSame(first,second);
        first.getJSONObject(1).put("adult_locked",false);first.put(new JSONObject().put("id","extra"));
        assertTrue(second.getJSONObject(1).optBoolean("adult_locked"));assertEquals(2,second.length());
        assertTrue(f.read());if(expectHelper())assertSame(prior,cache().get());
        assertEquals("Neither public mutation may change raw preferences",PROFILES,f.real.getString("profiles",""));
    }
    @Test public void malformedWrongTypeAndNullableDataRecoverOnNextCall()throws Exception{
        Fixture f=new Fixture();f.id("locked");assertTrue(f.read());
        for(String raw:new String[]{"not json","{}","null","[1,null,\"ignored\"]","[]"}){f.raw(raw);assertFalse(raw,f.read());}
        f.real.edit().putInt("profiles",7).commit();assertFalse(f.read());assertEquals(0,f.feature.profiles().length());
        f.nullRaw=true;assertFalse(f.read());f.nullRaw=false;f.raw(PROFILES);assertTrue(f.read());
    }
    @Test public void firstMatchOptBooleanMissingIdsAndNullActiveIdMatchOriginalLoop()throws Exception{
        Fixture f=new Fixture();f.id("x");
        f.raw("[{\"id\":\"x\",\"adult_locked\":false},{\"id\":\"x\",\"adult_locked\":true}]");assertFalse(f.read());
        f.raw("[{\"id\":\"x\",\"adult_locked\":true},{\"id\":\"x\",\"adult_locked\":false}]");assertTrue(f.read());
        f.raw("[{\"id\":\"x\"}]");assertFalse(f.read());
        f.raw("[{\"id\":\"x\",\"adult_locked\":\"true\"}]");assertTrue(f.read());
        f.id("");f.raw("[{\"adult_locked\":true}]");assertTrue(f.read());
        f.id("1");f.raw("[{\"id\":1,\"adult_locked\":true}]");assertTrue(f.read());
        f.nullActive=true;f.raw("[1,null]");assertFalse(f.read());
        f.raw("[{}]");try{f.read();fail("Original null active ID must throw when an object is reached");}catch(NullPointerException expected){}
    }
    static String paddedRaw(int length){
        String prefix="[{\"id\":\"x\",\"adult_locked\":true,\"padding\":\"",suffix="\"}]";
        StringBuilder raw=new StringBuilder(length);raw.append(prefix);
        while(raw.length()<length-suffix.length())raw.append('a');raw.append(suffix);
        assertEquals(length,raw.length());return raw.toString();
    }
    @Test public void validOversizeIsEvaluatedUncachedAndAdmissionIsBounded()throws Exception{
        Fixture f=new Fixture();f.id("x");f.raw(paddedRaw(65536));assertTrue(f.read());
        if(expectHelper())assertNotNull("Admission includes exactly64Ki UTF16chars",cache().get());
        f.raw(paddedRaw(65537));assertTrue(f.read());assertTrue(f.read());
        if(expectHelper())assertNull("Oversize data and previous snapshots must not be retained",cache().get());
        f.raw("[{\"id\":\"x\",\"adult_locked\":false}]");assertFalse(f.read());
    }
    @Test public void privateDataSnapshotsAreSeparatePerThread()throws Exception{
        final Fixture f=new Fixture();f.id("locked");
        final Object[] entries=new Object[2];final AtomicReference<Throwable> error=new AtomicReference<>();
        final CountDownLatch ready=new CountDownLatch(2),start=new CountDownLatch(1);
        Thread[] workers=new Thread[2];
        for(int i=0;i<2;i++){final int slot=i;workers[i]=new Thread(new Runnable(){public void run(){
            try{ready.countDown();start.await();assertTrue(f.feature.adultLocked());
                ThreadLocal<?> local=cache();entries[slot]=local==null?null:local.get();
                assertTrue(f.feature.adultLocked());if(local!=null)assertSame(entries[slot],local.get());
            }catch(Throwable failure){error.compareAndSet(null,failure);}
        }},"profile-data-fixture-"+i);workers[i].start();}
        ready.await();start.countDown();for(Thread worker:workers)worker.join();
        if(error.get()!=null)throw new AssertionError("Actual profile reads failed on fixture thread",error.get());
        if(expectHelper()){assertNotNull(entries[0]);assertNotNull(entries[1]);assertNotSame(entries[0],entries[1]);}
        assertEquals(0,f.writes);
    }
}
