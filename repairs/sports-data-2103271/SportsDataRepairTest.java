package com.projectinfinity.kodi;

import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import java.io.IOException;
import java.lang.reflect.Method;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=android.app.Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class SportsDataRepairTest {
  CobraNavigationUiTest f;
  @Before public void before(){f=new CobraNavigationUiTest();f.clock();}

  static Object callStatic(String name,Class<?>[] types,Object... args)throws Exception{
    Method m=InfinityLiveActivity.class.getDeclaredMethod(name,types);m.setAccessible(true);return m.invoke(null,args);
  }
  static boolean hasText(View view,String target){
    if(view instanceof TextView&&((TextView)view).getText().toString().contains(target))return true;
    if(view instanceof ViewGroup){ViewGroup group=(ViewGroup)view;for(int i=0;i<group.getChildCount();i++)if(hasText(group.getChildAt(i),target))return true;}
    return false;
  }

  @SuppressWarnings("unchecked") @Test public void scoreboardWindowIsSplitIntoSupportedSingleDayKeys()throws Exception{
    Calendar from=Calendar.getInstance();from.set(2026,Calendar.SEPTEMBER,30,12,0,0);from.set(Calendar.MILLISECOND,0);
    Calendar to=(Calendar)from.clone();to.add(Calendar.DAY_OF_MONTH,7);
    List<String> days=(List<String>)callStatic("cobraSportsDateKeys",new Class<?>[]{long.class,long.class},from.getTimeInMillis(),to.getTimeInMillis());
    assertEquals(8,days.size());assertEquals("20260930",days.get(0));assertEquals("20261007",days.get(7));
    for(String day:days){assertTrue(day.matches("\\d{8}"));assertFalse("Range syntax must never return",day.contains("-"));}
  }

  @Test public void feedErrorsKeepActionableHttpCauseForDeviceDiagnostics()throws Exception{
    String detail=(String)callStatic("cobraSportsErrorDetail",new Class<?>[]{Exception.class},new IOException("HTTP 400"));
    assertTrue(detail.contains("IOException"));assertTrue(detail.contains("HTTP 400"));
  }

  @SuppressWarnings("unchecked") @Test public void successfulEmptyFeedSaysNoGamesInsteadOfDataUnavailable()throws Exception{
    InfinityLiveActivity a=f.fixture(4);try{
      ((List<Object>)CobraNavigationUiTest.get(a,"mCobraSportsGames")).clear();
      CobraNavigationUiTest.put(a,"mCobraSportsLastRefresh",System.currentTimeMillis());
      CobraNavigationUiTest.put(a,"mCobraSportsLastError","");
      CobraNavigationUiTest.call(a,"clearStage","COBRA • SPORTS");
      CobraNavigationUiTest.call(a,"cobraSportsRenderHub");
      View stage=(View)CobraNavigationUiTest.get(a,"mStage");
      assertTrue(hasText(stage,"NO GAMES SCHEDULED"));assertFalse(hasText(stage,"SPORTS DATA UNAVAILABLE"));
    }finally{f.clean(a);}
  }

  @SuppressWarnings("unchecked") @Test public void totalFeedFailureStillShowsUnavailableAndRootCause()throws Exception{
    InfinityLiveActivity a=f.fixture(4);try{
      ((List<Object>)CobraNavigationUiTest.get(a,"mCobraSportsGames")).clear();
      CobraNavigationUiTest.put(a,"mCobraSportsLastRefresh",System.currentTimeMillis());
      CobraNavigationUiTest.put(a,"mCobraSportsLastError","Unavailable leagues: NFL (IOException: HTTP 400)");
      CobraNavigationUiTest.call(a,"clearStage","COBRA • SPORTS");
      CobraNavigationUiTest.call(a,"cobraSportsRenderHub");
      View stage=(View)CobraNavigationUiTest.get(a,"mStage");
      assertTrue(hasText(stage,"SPORTS DATA UNAVAILABLE"));assertTrue(hasText(stage,"HTTP 400"));assertFalse(hasText(stage,"NO GAMES SCHEDULED"));
    }finally{f.clean(a);}
  }
}
