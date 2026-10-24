package com.projectinfinity.kodi;

import android.app.AlertDialog;
import android.app.Dialog;
import android.graphics.Color;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.view.inputmethod.EditorInfo;
import android.view.inputmethod.InputMethodManager;
import android.widget.*;
import java.text.DateFormat;
import java.util.*;
import org.json.*;

/** Selection-first Infinity Search; shares the original editor and IME lifetime. */
final class InfinitySearch101 {
  static final int ALL=0x00950001, SEARCH=0x01010001, HISTORY=0x01010002;
  private InfinitySearch101() {}
  static void decorate(InfinityAndroidKeyboard.Editor e,String heading,boolean hidden,boolean search) {
    if(hidden || e.kind!=0 || heading==null || !heading.startsWith(InfinitySearch95.PREFIX))return;
    try { new Surface(e,new JSONObject(heading.substring(InfinitySearch95.PREFIX.length())),heading.length()).show(); }
    catch(Exception invalid){e.input.post(()->e.finish(false));}
  }
  static final class Surface {
    final InfinityAndroidKeyboard.Editor e;
    final String token,theme,media;
    final JSONArray providers,history;
    final boolean light,oled;
    final int ink,muted,accent;
    final Set<String> eligible=new LinkedHashSet<>();
    BaseAdapter providerAdapter;
    final android.util.LruCache<String,android.graphics.Bitmap> icons=new android.util.LruCache<String,android.graphics.Bitmap>(2*1024*1024){
      @Override protected int sizeOf(String key,android.graphics.Bitmap image){return image.getAllocationByteCount();}
    };
    final Set<String> missingIcons=new HashSet<>();
    final Map<String,String> names=new LinkedHashMap<>();
    String selected;
    TextView submit;
    boolean finished;
    final boolean openHistory;
    Surface(InfinityAndroidKeyboard.Editor editor,JSONObject data,int length)throws Exception {
      e=editor;token=data.getString("token");theme=data.getString("theme");media=data.getString("media");
      if(length>1048576 || !token.matches("[a-f0-9]{32}") || !theme.matches("light|dark|oled") || !media.matches("Movies|TV Shows|Anime|Cartoons"))throw new IllegalArgumentException();
      providers=data.getJSONArray("providers");history=data.optJSONArray("shared_history");
      if(history!=null && history.length()>50)throw new IllegalArgumentException();
      light=theme.equals("light");oled=theme.equals("oled");
      ink=light?0xff18354c:0xfff1f7fb;muted=light?0xff547087:0xffb1c5d3;accent=light?0xff098bb8:0xff24cce8;
      selected=data.optString("selected","all");openHistory=data.optString("initial_view").equals("history");
      names.put("all","Search All");
      for(int i=0;i<providers.length();i++) {
        JSONObject p=providers.getJSONObject(i);String id=p.getString("id"),name=p.getString("name"),detail=p.optString("description","Unavailable");
        if(!id.matches("plugin\\.video\\.[A-Za-z0-9._-]{1,90}") || name.isEmpty() || name.length()>100 || detail.length()>160 || p.optString("icon").length()>4096 || names.containsKey(id))throw new IllegalArgumentException();
        names.put(id,name);if(p.optBoolean("available"))eligible.add(id);
      }
      if(!eligible.isEmpty())eligible.add("all");
    }
    TextView text(String value,int size,int color,boolean bold){return InfinitySearch95.text(e,value,size,color,bold);}
    LinearLayout column(){LinearLayout v=new LinearLayout(e.owner);v.setOrientation(LinearLayout.VERTICAL);return v;}
    void panelStyle(LinearLayout panel){panel.setPadding(e.dp(16),e.dp(12),e.dp(16),e.dp(14));panel.setBackground(InfinitySearch95.surface(e,light?0xfff3f9fd:oled?Color.BLACK:0xff081a26,accent,22));}
    TextView button(String label,Runnable action){TextView v=text(label,16,ink,true);v.setGravity(Gravity.CENTER);v.setMinHeight(e.dp(48));v.setFocusable(true);v.setOnClickListener(w->action.run());return v;}
    void show()throws Exception {
      LinearLayout panel=(LinearLayout)e.input.getParent();panel.removeAllViews();panel.setOrientation(LinearLayout.VERTICAL);panelStyle(panel);
      LinearLayout header=new LinearLayout(e.owner);header.setGravity(Gravity.CENTER_VERTICAL);
      header.addView(text("∞",32,accent,true),new LinearLayout.LayoutParams(e.dp(44),e.dp(52)));
      LinearLayout titles=column();titles.addView(text("Infinity Search",21,ink,true));titles.addView(text(media+"  ·  choose where to search",12,muted,false));header.addView(titles,new LinearLayout.LayoutParams(0,-2,1));
      TextView close=button("×",()->e.finish(false));close.setTextSize(28);close.setContentDescription("Close Infinity Search");header.addView(close,new LinearLayout.LayoutParams(e.dp(48),e.dp(48)));panel.addView(header);
      LinearLayout query=new LinearLayout(e.owner);query.setGravity(Gravity.CENTER_VERTICAL);
      e.input.setHint("Search "+media.toLowerCase(Locale.ROOT));e.input.setTextSize(18);e.input.setTextColor(ink);e.input.setHintTextColor(muted);
      e.input.setFilters(new android.text.InputFilter[]{new android.text.InputFilter.LengthFilter(160)});
      e.input.setBackground(InfinitySearch95.surface(e,light?0xffe1f3fb:oled?Color.BLACK:0xff05131e,accent,15));
      query.addView(e.input,new LinearLayout.LayoutParams(0,e.dp(56),1));
      ImageView historyButton=icon("clock",ink,26);historyButton.setOnClickListener(v->history());historyButton.setFocusable(true);historyButton.setId(HISTORY);historyButton.setContentDescription("Search History");historyButton.setBackground(InfinitySearch95.surface(e,light?0xffe1f3fb:oled?Color.BLACK:0xff05131e,accent,15));
      LinearLayout.LayoutParams hp=new LinearLayout.LayoutParams(e.dp(52),e.dp(56));hp.leftMargin=e.dp(8);query.addView(historyButton,hp);
      LinearLayout.LayoutParams qp=new LinearLayout.LayoutParams(-1,-2);qp.topMargin=e.dp(12);qp.bottomMargin=e.dp(12);panel.addView(query,qp);
      panel.addView(text("SEARCH WITH",12,muted,true));
      final ListView scroll=new ListView(e.owner);scroll.setDivider(null);scroll.setClipToPadding(false);
      scroll.setItemsCanFocus(true);scroll.setCacheColorHint(Color.TRANSPARENT);
      providerAdapter=new BaseAdapter(){
        @Override public int getCount(){return providers.length()+1;}
        @Override public Object getItem(int position){return position==0?null:providers.optJSONObject(position-1);}
        @Override public long getItemId(int position){return position;}
        @Override public boolean hasStableIds(){return true;}
        @Override public View getView(int position,View recycled,ViewGroup parent){
          if(position==0){View all=option("all","Search All","Search all compatible installed add-ons","",eligible.contains("all"),true,recycled);all.setId(ALL);return all;}
          JSONObject p=providers.optJSONObject(position-1);
          return option(p.optString("id"),p.optString("name"),p.optString("description","Unavailable"),p.optString("icon"),p.optBoolean("available"),false,recycled);
        }
      };
      scroll.setAdapter(providerAdapter);
      // ListView creates only visible provider rows. Inventory size does not
      // create a view/bitmap for every installed add-on on the Android UI thread.
      int availableHeight=e.owner.getResources().getDisplayMetrics().heightPixels-e.dp(292);
      panel.addView(scroll,new LinearLayout.LayoutParams(-1,Math.max(e.dp(116),Math.min(e.dp(395),availableHeight))));
      submit=button("Search",()->submit());submit.setId(SEARCH);submit.setContentDescription("Submit Infinity Search");submit.setTextColor(light?Color.WHITE:0xff031923);submit.setBackground(InfinitySearch95.surface(e,accent,accent,15));
      LinearLayout.LayoutParams sp=new LinearLayout.LayoutParams(-1,e.dp(52));sp.topMargin=e.dp(12);panel.addView(submit,sp);
      submit.setEnabled(!eligible.isEmpty());if(!eligible.contains(selected))selected="all";select(selected);
      TextView footer=text("Enabled, verified providers only.",11,muted,false);footer.setPadding(e.dp(4),e.dp(10),e.dp(4),0);panel.addView(footer);
      panel.getViewTreeObserver().addOnGlobalLayoutListener(()->{
        android.graphics.Rect visible=new android.graphics.Rect();panel.getWindowVisibleDisplayFrame(visible);
        if(visible.height()>0){int height=Math.max(e.dp(58),Math.min(e.dp(395),visible.height()-e.dp(280)));ViewGroup.LayoutParams params=scroll.getLayoutParams();if(params.height!=height){params.height=height;scroll.setLayoutParams(params);}}
      });
      e.input.setImeOptions(EditorInfo.IME_ACTION_SEARCH|EditorInfo.IME_FLAG_NO_EXTRACT_UI|EditorInfo.IME_FLAG_NO_PERSONALIZED_LEARNING);
      e.input.setOnEditorActionListener((v,action,event)->{
        if(action==EditorInfo.IME_ACTION_SEARCH || action==EditorInfo.IME_ACTION_DONE || (event!=null && event.getKeyCode()==android.view.KeyEvent.KEYCODE_ENTER && event.getAction()==android.view.KeyEvent.ACTION_UP)){submit();return true;}return false;
      });
      e.dialog.getWindow().setTitle("Infinity Search");
      if(openHistory)e.input.post(()->history());
    }
    View option(String id,String name,String detail,String icon,boolean enabled,boolean prominent,View recycled) {
      ProviderRow holder;
      if(recycled instanceof LinearLayout && recycled.getTag() instanceof ProviderRow)holder=(ProviderRow)recycled.getTag();
      else {
        holder=new ProviderRow();holder.row=new LinearLayout(e.owner);holder.row.setGravity(Gravity.CENTER_VERTICAL);holder.row.setMinimumHeight(e.dp(58));
        FrameLayout picture=new FrameLayout(e.owner);
        holder.logo=new ImageView(e.owner);holder.logo.setScaleType(ImageView.ScaleType.FIT_CENTER);picture.addView(holder.logo,new FrameLayout.LayoutParams(-1,-1));
        holder.initial=text("",25,ink,true);holder.initial.setGravity(Gravity.CENTER);picture.addView(holder.initial,new FrameLayout.LayoutParams(-1,-1));
        holder.row.addView(picture,new LinearLayout.LayoutParams(e.dp(42),e.dp(42)));
        LinearLayout labels=column();labels.setPadding(e.dp(10),0,e.dp(8),0);
        holder.title=text("",17,ink,false);holder.detail=text("",11,muted,false);holder.detail.setMaxLines(2);
        labels.addView(holder.title);labels.addView(holder.detail);holder.row.addView(labels,new LinearLayout.LayoutParams(0,-2,1));
        holder.mark=text("",26,muted,false);holder.row.addView(holder.mark,new LinearLayout.LayoutParams(e.dp(20),-2));holder.row.setTag(holder);
      }
      LinearLayout row=holder.row;row.setId(id.equals("all")?ALL:View.NO_ID);row.setEnabled(enabled);row.setFocusable(enabled);row.setClickable(enabled);row.setAlpha(enabled?1f:.58f);
      row.setOnClickListener(enabled?v->select(id):null);row.setLongClickable(false);
      holder.title.setText(name);holder.title.setTypeface(android.graphics.Typeface.create(prominent?"sans-serif-medium":"sans-serif",0));holder.detail.setText(detail);
      if(!icon.equals(holder.icon)){
        holder.icon=icon;android.graphics.Bitmap bitmap=iconBitmap(icon);holder.logo.setImageBitmap(bitmap);holder.logo.setVisibility(bitmap==null?View.GONE:View.VISIBLE);holder.initial.setVisibility(bitmap==null?View.VISIBLE:View.GONE);
      }
      holder.initial.setText(prominent?"⌕":name.substring(0,1));holder.initial.setTextColor(prominent?accent:ink);
      boolean chosen=enabled && selected.equals(id);row.setSelected(chosen);
      row.setBackground(InfinitySearch95.surface(e,chosen?(light?0xffd4edf9:0xff103d50):(light?0xffedf6fb:oled?Color.BLACK:0xff0c202e),chosen?accent:(light?0xffc8dfe9:0xff294657),13));
      holder.mark.setText(chosen?"✓":enabled?"›":"—");holder.mark.setTextColor(chosen?accent:muted);
      row.setContentDescription(name+(enabled?(chosen?", selected":", select provider"):". "+detail));
      row.setPadding(e.dp(10),e.dp(10),e.dp(10),e.dp(10));
      return row;
    }
    android.graphics.Bitmap iconBitmap(String path) {
      if(path.isEmpty() || missingIcons.contains(path))return null;
      android.graphics.Bitmap cached=icons.get(path);if(cached!=null)return cached;
      try {
        java.io.File file=new java.io.File(path);
        if(file.isAbsolute() && file.equals(file.getCanonicalFile()) && file.isFile() && file.length()<=1048576 && path.contains("/addons/plugin.video.")){
          android.graphics.BitmapFactory.Options options=new android.graphics.BitmapFactory.Options();options.inJustDecodeBounds=true;android.graphics.BitmapFactory.decodeFile(path,options);
          if(options.outWidth>0 && options.outHeight>0 && options.outWidth<=4096 && options.outHeight<=4096){
            options.inSampleSize=1;while(Math.max(options.outWidth,options.outHeight)/options.inSampleSize>128)options.inSampleSize*=2;
            options.inJustDecodeBounds=false;android.graphics.Bitmap bitmap=android.graphics.BitmapFactory.decodeFile(path,options);
            if(bitmap!=null){icons.put(path,bitmap);return bitmap;}
          }
        }
      }catch(Exception unavailable){/* The visible provider name remains usable. */}
      missingIcons.add(path);return null;
    }
    void select(String id) {
      if(!eligible.contains(id))return;
      selected=id;
      if(providerAdapter!=null)providerAdapter.notifyDataSetChanged();
      submit.setText(id.equals("all")?"Search All":"Search "+names.get(id));submit.setEnabled(true);
    }
    void submit() {
      if(finished || !eligible.contains(selected))return;
      String query=e.input.getText().toString().trim();
      if(query.isEmpty() || query.length()>160){e.input.setError("Enter a search query");e.input.requestFocus();return;}
      finished=true;InfinitySearch95.submit(e,token,selected,false);
    }
    ImageView icon(String kind,int color,int size){ImageView v=new ImageView(e.owner);v.setImageDrawable(new Glyph(e,kind,color,size));v.setScaleType(ImageView.ScaleType.CENTER_INSIDE);return v;}
    void history() {
      if(finished || !e.dialog.isShowing())return;
      try {
        InputMethodManager ime=(InputMethodManager)e.owner.getSystemService(android.content.Context.INPUT_METHOD_SERVICE);if(ime!=null)ime.hideSoftInputFromWindow(e.input.getWindowToken(),0);
        Dialog dialog=new Dialog(e.owner);dialog.requestWindowFeature(android.view.Window.FEATURE_NO_TITLE);
        LinearLayout panel=column();panelStyle(panel);panel.setTag("infinity-history-panel");
        LinearLayout heading=new LinearLayout(e.owner);heading.setGravity(Gravity.CENTER_VERTICAL);
        heading.addView(text("∞",32,accent,true),new LinearLayout.LayoutParams(e.dp(40),e.dp(56)));
        LinearLayout titles=column();titles.addView(text("Search History",21,ink,true));titles.addView(text("Recent searches from all providers",11,muted,false));heading.addView(titles,new LinearLayout.LayoutParams(0,-2,1));panel.addView(heading);
        LinearLayout rows=column();
        if(history==null || history.length()==0){TextView empty=text("No saved searches yet",16,muted,false);empty.setPadding(e.dp(10),e.dp(24),e.dp(10),e.dp(24));rows.addView(empty);}
        else for(int i=0;i<history.length();i++) {
          JSONObject record=history.getJSONObject(i);String query=record.getString("query"),kind=record.getString("media"),name=record.getString("name");
          if(query.isEmpty() || query.length()>160 || !kind.matches("movie|tv|anime|cartoon") || name.length()>100)throw new IllegalArgumentException();
          String when=DateFormat.getDateInstance(DateFormat.MEDIUM).format(new Date(record.getLong("at")*1000));
          LinearLayout row=new LinearLayout(e.owner);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(e.dp(10),e.dp(8),e.dp(10),e.dp(8));row.setMinimumHeight(e.dp(64));row.setFocusable(true);
          row.setBackground(InfinitySearch95.surface(e,light?0xffedf6fb:oled?Color.BLACK:0xff0c202e,light?0xffc8dfe9:0xff294657,13));
          row.addView(icon("clock",muted,24),new LinearLayout.LayoutParams(e.dp(34),e.dp(42)));
          LinearLayout labels=column();labels.setPadding(e.dp(8),0,e.dp(6),0);TextView title=text(query,17,ink,false);title.setMaxLines(2);labels.addView(title);labels.addView(text(name+" · "+(kind.equals("anime")?"Anime":kind.equals("cartoon")?"Cartoons":kind.equals("tv")?"TV Shows":"Movies"),11,muted,false));row.addView(labels,new LinearLayout.LayoutParams(0,-2,1));
          row.addView(icon(kind.equals("tv")?"tv":"movie",muted,22),new LinearLayout.LayoutParams(e.dp(28),e.dp(36)));TextView date=text(when,10,muted,false);date.setGravity(Gravity.RIGHT|Gravity.CENTER_VERTICAL);row.addView(date,new LinearLayout.LayoutParams(e.dp(76),-2));
          row.setTag("history:"+i);row.setOnClickListener(v->{e.input.setText(query);e.input.setSelection(e.input.length());dialog.dismiss();});rows.addView(row,InfinitySearch95.spacing(e));
        }
        ScrollView scroll=new ScrollView(e.owner);scroll.addView(rows);panel.addView(scroll,new LinearLayout.LayoutParams(-1,Math.min(e.dp(380),Math.max(e.dp(100),e.owner.getResources().getDisplayMetrics().heightPixels-e.dp(230)))));
        TextView clear=button("Clear History",()->{
          AlertDialog confirm=new AlertDialog.Builder(e.owner,light?android.R.style.Theme_Material_Light_Dialog_Alert:android.R.style.Theme_Material_Dialog_Alert).setTitle("Clear Search History?").setMessage("Clear Infinity's shared search history? Provider histories and saved progress are kept.").setNegativeButton("Cancel",(d,w)->{}).setPositiveButton("Clear History",(d,w)->{
            if(finished)return;
            try{JSONObject result=new JSONObject().put("token",token).put("provider",selected).put("query",e.input.getText().toString()).put("operation","clear-history").put("confirmed",true);finished=true;dialog.dismiss();e.input.setFilters(new android.text.InputFilter[0]);e.input.setText(result.toString());e.finish(true);}catch(JSONException invalid){e.finish(false);}
          }).create();confirm.setOnShowListener(d->{confirm.getWindow().setBackgroundDrawable(InfinitySearch95.surface(e,light?0xfff3f9fd:oled?Color.BLACK:0xff081a26,accent,20));confirm.getButton(AlertDialog.BUTTON_POSITIVE).setTextColor(accent);confirm.getButton(AlertDialog.BUTTON_NEGATIVE).setTextColor(muted);});confirm.show();
        });clear.setTag("clear-history");clear.setEnabled(history!=null && history.length()>0);clear.setTextColor(accent);clear.setTextSize(12);clear.setCompoundDrawablesWithIntrinsicBounds(new Glyph(e,"trash",accent,16),null,null,null);clear.setCompoundDrawablePadding(e.dp(4));heading.addView(clear,new LinearLayout.LayoutParams(e.dp(110),e.dp(48)));
        dialog.setContentView(panel);dialog.getWindow().setBackgroundDrawableResource(android.R.color.transparent);dialog.getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_HIDDEN);dialog.show();
        dialog.getWindow().setLayout(Math.min(e.dp(560),e.owner.getResources().getDisplayMetrics().widthPixels-e.dp(24)),ViewGroup.LayoutParams.WRAP_CONTENT);
      }catch(Exception invalid){e.input.setError("Search history is unavailable");}
    }
  }
  static final class ProviderRow {
    LinearLayout row;ImageView logo;TextView initial,title,detail,mark;String icon=null;
  }
  /** Small approved UI glyphs, drawn as vectors so Fold scaling stays crisp. */
  static final class Glyph extends android.graphics.drawable.Drawable {
    final android.graphics.Paint p=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);final String kind;final int size;
    Glyph(InfinityAndroidKeyboard.Editor e,String k,int color,int dp){kind=k;size=e.dp(dp);p.setColor(color);p.setStrokeWidth(1.6f);p.setStrokeCap(android.graphics.Paint.Cap.ROUND);p.setStrokeJoin(android.graphics.Paint.Join.ROUND);setBounds(0,0,size,size);}
    @Override public int getIntrinsicWidth(){return size;}@Override public int getIntrinsicHeight(){return size;}
    @Override public void draw(android.graphics.Canvas canvas){int save=canvas.save();android.graphics.Rect b=getBounds();canvas.translate(b.left,b.top);canvas.scale(b.width()/24f,b.height()/24f);p.setStyle(android.graphics.Paint.Style.STROKE);
      if(kind.equals("clock")){canvas.drawCircle(12,12,9,p);canvas.drawLine(12,6,12,12,p);canvas.drawLine(12,12,17,15,p);}
      else if(kind.equals("tv")){canvas.drawRoundRect(3,7,21,21,2,2,p);canvas.drawLine(8,2,12,7,p);canvas.drawLine(16,2,12,7,p);}
      else if(kind.equals("trash")){canvas.drawLine(4,6,20,6,p);canvas.drawLine(9,3,15,3,p);canvas.drawRoundRect(6,7,18,21,2,2,p);canvas.drawLine(10,10,10,18,p);canvas.drawLine(14,10,14,18,p);}
      else {canvas.drawCircle(12,12,9,p);for(int i=0;i<4;i++){double a=i*Math.PI/2;canvas.drawCircle(12+(float)Math.cos(a)*5,12+(float)Math.sin(a)*5,2,p);}}
      canvas.restoreToCount(save);
    }
    @Override public void setAlpha(int a){p.setAlpha(a);}@Override public void setColorFilter(android.graphics.ColorFilter f){p.setColorFilter(f);}@Deprecated @Override public int getOpacity(){return android.graphics.PixelFormat.TRANSLUCENT;}
  }

}
