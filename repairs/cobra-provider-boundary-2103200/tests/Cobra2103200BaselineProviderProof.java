package com.projectinfinity.kodi;
import android.app.Application;
import android.database.Cursor;
import android.os.ParcelFileDescriptor;
import android.os.Process;
import com.google.gson.*;
import com.projectinfinity.kodi.content.XBMCFileContentProvider;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadows.ShadowBinder;
import static org.junit.Assert.*;

/** Same security expectations run against the unchanged protected provider/RPC. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103200BaselineProviderProof {
 @Test public void externalArbitraryPathMustBeRejectedBeforePipeAllocation()throws Exception {
   XBMCFileContentProvider provider=Robolectric.buildContentProvider(XBMCFileContentProvider.class).create().get();
   ShadowBinder.setCallingUid(Process.myUid()+7001);
   try {
     ParcelFileDescriptor result=provider.openFile(XBMCFileContentProvider.buildUri("/private/fixture-secret"),"r");
     if(result!=null)result.close();
     fail("External arbitrary path was accepted by the provider; native reachability is not asserted");
   }catch(SecurityException expected){}
   finally{ShadowBinder.setCallingUid(Process.myUid());}
 }
 @Test public void quotedExternalSearchTermMustRemainOneLiteralJSONValue()throws Exception {
   final JsonArray[] captured={null};
   XBMCJsonRPC rpc=new XBMCJsonRPC(){@Override public JsonArray request_array(String text){captured[0]=JsonParser.parseString(text).getAsJsonArray();return new JsonArray();}};
   Cursor cursor=rpc.getSuggestions("quote\" and backslash\\ and newline\n",10);
   assertNotNull(cursor);cursor.close();assertEquals(6,captured[0].size());
 }
}
