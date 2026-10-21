package com.projectinfinity.kodi;

import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.inputmethod.EditorInfo;
import android.widget.*;
import org.json.*;

/** One scoped search surface, using the existing editor/IME lifetime and tokens. */
final class InfinitySearch95 {
  static final String PREFIX="Infinity.Search.2103395:";
  static void decorate(InfinityAndroidKeyboard.Editor e,String heading,boolean hidden,boolean search) {
    if(hidden || e.kind!=0 || heading==null || !heading.startsWith(PREFIX))return;
    try {
      if(heading.length()>24000)throw new IllegalArgumentException();
      JSONObject data=new JSONObject(heading.substring(PREFIX.length()));
      String token=data.getString("token");
      if(!token.matches("[a-f0-9]{32}"))throw new IllegalArgumentException();
      JSONArray providers=data.getJSONArray("providers");
      if(providers.length()>24)throw new IllegalArgumentException();
      String theme=data.getString("theme");
      if(!theme.matches("light|dark|oled"))throw new IllegalArgumentException();
      boolean light=theme.equals("light"),oled=theme.equals("oled");
      int ink=light?0xff18354c:0xfff1f7fb,muted=light?0xff547087:0xffb1c5d3;
      LinearLayout panel=(LinearLayout)e.input.getParent();
      panel.removeAllViews();panel.setPadding(e.dp(16),e.dp(12),e.dp(16),e.dp(14));
      panel.setBackground(surface(e,light?0xfff3f9fd:oled?Color.BLACK:0xff081a26,light?0xff128ab5:0xff24cce8,22));
      LinearLayout header=new LinearLayout(e.owner);header.setGravity(Gravity.CENTER_VERTICAL);
      TextView mark=text(e,"∞",32,light?0xff098bb8:0xff24cce8,true);
      header.addView(mark,new LinearLayout.LayoutParams(e.dp(44),e.dp(52)));
      LinearLayout titles=new LinearLayout(e.owner);titles.setOrientation(1);
      titles.addView(text(e,"Infinity Search",21,ink,true));
      titles.addView(text(e,data.optString("media","Movies")+"  ·  choose where to search",12,muted,false));
      header.addView(titles,new LinearLayout.LayoutParams(0,-2,1));
      TextView close=text(e,"×",28,ink,false);close.setGravity(Gravity.CENTER);
      close.setContentDescription("Close Infinity Search");close.setFocusable(true);
      close.setOnClickListener(v->e.finish(false));header.addView(close,new LinearLayout.LayoutParams(e.dp(48),e.dp(48)));
      panel.addView(header);
      e.input.setHint("Search movies or TV shows");e.input.setTextSize(18);e.input.setTextColor(ink);e.input.setHintTextColor(muted);
      e.input.setFilters(new android.text.InputFilter[]{new android.text.InputFilter.LengthFilter(160)});
      e.input.setBackground(surface(e,light?0xffe1f3fb:oled?Color.BLACK:0xff05131e,light?0xff098bb8:0xff24cce8,15));
      LinearLayout.LayoutParams field=new LinearLayout.LayoutParams(-1,e.dp(56));field.topMargin=e.dp(12);field.bottomMargin=e.dp(12);panel.addView(e.input,field);
      TextView caption=text(e,"SEARCH WITH",12,muted,true);panel.addView(caption);
      boolean available=false;
      for(int i=0;i<providers.length();i++)available|=providers.getJSONObject(i).optBoolean("available");
      final boolean any=available;
      View all=row(e,"Search All","All compatible installed add-ons","",light,ink,muted,true,any);
      all.setId(0x00950001);all.setOnClickListener(v->{if(any)submit(e,token,"all",false);});panel.addView(all,spacing(e));
      LinearLayout list=new LinearLayout(e.owner);list.setOrientation(1);
      for(int i=0;i<providers.length();i++) {
        JSONObject provider=providers.getJSONObject(i);String id=provider.getString("id");
        if(!id.matches("plugin\\.video\\.[A-Za-z0-9._-]{1,90}"))throw new IllegalArgumentException();
        boolean enabled=provider.optBoolean("available");
        String name=provider.getString("name");if(name.length()>100)name=name.substring(0,100);
        String detail=provider.optString("description",enabled?"Search this provider":"Unavailable");
        if(detail.length()>160)detail=detail.substring(0,160);
        View view=row(e,name,detail,provider.optString("icon"),light,ink,muted,false,enabled);
        view.setTag(id);view.setOnClickListener(v->{if(enabled)submit(e,token,id,false);});
        view.setOnLongClickListener(v->{if(enabled){submit(e,token,id,true);return true;}return false;});
        view.setContentDescription(name+". "+detail+(enabled?". Hold for provider search history":""));
        list.addView(view,spacing(e));
      }
      panel.addView(list);
      TextView footer=text(e,"Enabled, verified providers only. Hold a provider for its search history.",11,muted,false);footer.setPadding(e.dp(4),e.dp(12),e.dp(4),0);panel.addView(footer);
      e.input.setImeOptions(EditorInfo.IME_ACTION_SEARCH|EditorInfo.IME_FLAG_NO_EXTRACT_UI|EditorInfo.IME_FLAG_NO_PERSONALIZED_LEARNING);
      e.input.setOnEditorActionListener((v,action,event)-> {
        if(action==EditorInfo.IME_ACTION_SEARCH || action==EditorInfo.IME_ACTION_DONE ||
           (event!=null && event.getKeyCode()==android.view.KeyEvent.KEYCODE_ENTER && event.getAction()==android.view.KeyEvent.ACTION_UP)) {
          if(any)submit(e,token,"all",false);return true;
        }return false;
      });
      e.dialog.getWindow().setTitle("Infinity Search");
    } catch(Exception invalid) {
      // A malformed private request must not become a generic query editor.
      e.input.post(()->e.finish(false));
    }
  }
  static void submit(InfinityAndroidKeyboard.Editor e,String token,String id,boolean history) {
    String query=e.input.getText().toString().trim();
    if(!history && (query.isEmpty()||query.length()>160)){e.input.setError("Enter a search query");e.input.requestFocus();return;}
    try {
      JSONObject result=new JSONObject();result.put("token",token);result.put("provider",id);result.put("query",query);result.put("history",history);
      e.input.setFilters(new android.text.InputFilter[0]);e.input.setText(result.toString());e.finish(true);
    }catch(JSONException impossible){e.finish(false);}
  }
  static LinearLayout.LayoutParams spacing(InfinityAndroidKeyboard.Editor e){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.topMargin=e.dp(5);return p;}
  static TextView text(InfinityAndroidKeyboard.Editor e,String s,int size,int color,boolean bold){TextView v=new TextView(e.owner);v.setText(s);v.setTextSize(size);v.setTextColor(color);v.setTypeface(Typeface.create(bold?"sans-serif-medium":"sans-serif",0));return v;}
  static GradientDrawable surface(InfinityAndroidKeyboard.Editor e,int color,int border,int radius){GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(e.dp(radius));d.setStroke(e.dp(1),border);return d;}
  static View row(InfinityAndroidKeyboard.Editor e,String title,String description,String icon,boolean light,int ink,int muted,boolean prominent,boolean available){
    LinearLayout row=new LinearLayout(e.owner);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(e.dp(10),e.dp(7),e.dp(10),e.dp(7));row.setMinimumHeight(e.dp(58));row.setFocusable(available);row.setClickable(available);row.setAlpha(available?1f:.58f);
    row.setBackground(surface(e,light?(prominent?0xffd4edf9:0xffedf6fb):(prominent?0xff103d50:0xff0c202e),prominent?0xff17b5db:(light?0xffc8dfe9:0xff294657),13));
    ImageView logo=new ImageView(e.owner);boolean decoded=false;
    try{
      java.io.File f=new java.io.File(icon);
      if(f.isAbsolute() && f.equals(f.getCanonicalFile()) && f.isFile() && f.length()<=1048576 && icon.contains("/addons/plugin.video.")){
        android.graphics.BitmapFactory.Options o=new android.graphics.BitmapFactory.Options();o.inJustDecodeBounds=true;android.graphics.BitmapFactory.decodeFile(icon,o);
        if(o.outWidth>0&&o.outHeight>0&&o.outWidth<=4096&&o.outHeight<=4096){o.inSampleSize=Math.max(1,Math.max(o.outWidth,o.outHeight)/128);o.inJustDecodeBounds=false;android.graphics.Bitmap b=android.graphics.BitmapFactory.decodeFile(icon,o);if(b!=null){logo.setImageBitmap(b);decoded=true;}}
      }
    }catch(Exception unavailable){/* Visible name remains authoritative. */}
    if(decoded){logo.setScaleType(ImageView.ScaleType.FIT_CENTER);row.addView(logo,new LinearLayout.LayoutParams(e.dp(42),e.dp(42)));}
    else {TextView initial=text(e,prominent?"⌕":title.substring(0,1),25,prominent?0xff17b5db:ink,true);initial.setGravity(Gravity.CENTER);row.addView(initial,new LinearLayout.LayoutParams(e.dp(42),e.dp(42)));}
    LinearLayout labels=new LinearLayout(e.owner);labels.setOrientation(1);labels.setPadding(e.dp(10),0,e.dp(8),0);labels.addView(text(e,title,17,ink,prominent));TextView detail=text(e,description,11,muted,false);detail.setMaxLines(2);labels.addView(detail);row.addView(labels,new LinearLayout.LayoutParams(0,-2,1));
    TextView arrow=text(e,available?"›":"—",26,muted,false);row.addView(arrow,new LinearLayout.LayoutParams(e.dp(20),-2));return row;
  }
}
