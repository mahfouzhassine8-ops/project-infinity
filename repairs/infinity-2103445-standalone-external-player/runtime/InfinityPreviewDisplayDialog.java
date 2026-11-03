package com.projectinfinity.kodi;

import android.app.Activity;
import android.app.Dialog;
import android.content.Context;
import android.graphics.*;
import android.graphics.drawable.ColorDrawable;
import android.os.Bundle;
import android.view.*;
import android.widget.*;

/** Preview-only menu; it never owns a decoder, saved progress or global theme. */
public final class InfinityPreviewDisplayDialog extends Dialog {
    public interface Actions { void mode(int mode); void appearance(); }
    private final InfinityPreviewChrome chrome;
    private final Actions actions;
    private int selected;
    private final RadioButton[] checks=new RadioButton[3];
    private final LinearLayout[] rows=new LinearLayout[3];
    public InfinityPreviewDisplayDialog(Activity activity,InfinityPreviewChrome chrome,int selected,Actions actions) {
        super(activity,chrome.light?android.R.style.Theme_Material_Light_Dialog_NoActionBar:android.R.style.Theme_Material_Dialog_NoActionBar);
        this.chrome=chrome;this.selected=selected;this.actions=actions;setOwnerActivity(activity);
    }
    private TextView label(String text,int sp,int color) {
        TextView t=new TextView(getContext());t.setText(text);t.setTextSize(sp);t.setTextColor(color);t.setTypeface(chrome.font);return t;
    }
    @Override protected void onCreate(Bundle saved) {
        super.onCreate(saved);requestWindowFeature(Window.FEATURE_NO_TITLE);
        LinearLayout content=new LinearLayout(getContext());content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(chrome.dp(18),chrome.dp(16),chrome.dp(18),chrome.dp(16));content.setBackground(chrome.glass(22,false));
        LinearLayout heading=new LinearLayout(getContext());heading.setGravity(Gravity.CENTER_VERTICAL);
        heading.addView(new Mark(getContext(),chrome,-1),new LinearLayout.LayoutParams(chrome.dp(28),chrome.dp(28)));
        TextView title=label("Display",21,chrome.ink);title.setPadding(chrome.dp(10),0,0,0);heading.addView(title,new LinearLayout.LayoutParams(-2,-2));
        content.addView(heading,new LinearLayout.LayoutParams(-1,chrome.dp(44)));
        ScrollView scroll=new ScrollView(getContext());scroll.setFillViewport(false);
        LinearLayout choices=new LinearLayout(getContext());choices.setOrientation(LinearLayout.VERTICAL);scroll.addView(choices);
        String[] names={"Best Fit","Fill (crop)","Stretch"};
        String[] descriptions={"Show the entire video with no cropping.","Fill the screen and crop the excess edges.","Fill the screen without cropping (may change aspect ratio)."};
        for(int i=0;i<3;i++){
            final int mode=i;LinearLayout row=new LinearLayout(getContext());row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(chrome.dp(12),chrome.dp(10),chrome.dp(8),chrome.dp(10));row.setMinimumHeight(chrome.dp(88));
            rows[i]=row;row.setBackground(chrome.glass(13,false));row.addView(new Mark(getContext(),chrome,i),new LinearLayout.LayoutParams(chrome.dp(32),chrome.dp(36)));
            LinearLayout copy=new LinearLayout(getContext());copy.setOrientation(LinearLayout.VERTICAL);copy.setPadding(chrome.dp(12),0,chrome.dp(8),0);
            copy.addView(label(names[i],16,chrome.ink));TextView help=label(descriptions[i],12,chrome.secondary);help.setPadding(0,chrome.dp(4),0,0);copy.addView(help);
            row.addView(copy,new LinearLayout.LayoutParams(0,-2,1));RadioButton radio=new RadioButton(getContext());checks[i]=radio;radio.setButtonTintList(android.content.res.ColorStateList.valueOf(chrome.accent));radio.setContentDescription(names[i]+" selection");
            row.addView(radio,new LinearLayout.LayoutParams(chrome.dp(48),chrome.dp(48)));
            View.OnClickListener choose=v->{selected=mode;updateSelection();actions.mode(mode);};row.setOnClickListener(choose);radio.setOnClickListener(choose);
            LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.bottomMargin=chrome.dp(8);choices.addView(row,lp);
        }
        content.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        LinearLayout footer=new LinearLayout(getContext());footer.setGravity(Gravity.CENTER_VERTICAL);
        Button appearance=footerButton("Appearance",false);appearance.setOnClickListener(v->actions.appearance());
        Button done=footerButton("Done",true);done.setOnClickListener(v->dismiss());
        LinearLayout.LayoutParams left=new LinearLayout.LayoutParams(0,chrome.dp(50),1);left.rightMargin=chrome.dp(12);footer.addView(appearance,left);footer.addView(done,new LinearLayout.LayoutParams(0,chrome.dp(50),1));
        content.addView(footer,new LinearLayout.LayoutParams(-1,chrome.dp(56)));setContentView(content);updateSelection();
        Window window=getWindow();if(window!=null){window.setBackgroundDrawable(new ColorDrawable(Color.TRANSPARENT));window.addFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND);window.setDimAmount(.42f);}
    }
    private Button footerButton(String text,boolean primary) {
        Button b=new Button(getContext());b.setAllCaps(false);b.setText(text);b.setTextSize(14);b.setTypeface(chrome.font);b.setTextColor(primary?chrome.accent:chrome.ink);b.setBackground(chrome.glass(13,false));return b;
    }
    private void updateSelection() {
        for(int i=0;i<3;i++)if(checks[i]!=null){checks[i].setChecked(i==selected);rows[i].setSelected(i==selected);if(android.os.Build.VERSION.SDK_INT>=23)rows[i].setForeground(i==selected?chrome.glass(13,true):null);else rows[i].setBackground(chrome.glass(13,i==selected));}
    }
    public void resize(int width,int height) {
        Window window=getWindow();if(window!=null){int w=Math.max(1,Math.min(chrome.dp(520),width-chrome.dp(28))),h=Math.max(1,Math.min(chrome.dp(450),height-chrome.dp(28)));if(window.getAttributes().width!=w||window.getAttributes().height!=h)window.setLayout(w,h);}
    }
    private static final class Mark extends View {
        final InfinityPreviewChrome c;final int mode;final Paint p=new Paint(3);
        Mark(Context context,InfinityPreviewChrome c,int mode){super(context);this.c=c;this.mode=mode;setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);}
        protected void onDraw(Canvas canvas){
            canvas.save();canvas.translate(getWidth()/2f,getHeight()/2f);float d=c.dp(1);canvas.scale(d,d);p.setColor(c.accent);p.setStrokeWidth(1.3f);p.setStyle(Paint.Style.STROKE);p.setStrokeCap(Paint.Cap.ROUND);p.setStrokeJoin(Paint.Join.ROUND);
            canvas.drawRoundRect(new RectF(-10,-8,10,7),2,2,p);
            if(mode<0){canvas.drawLine(0,7,0,10,p);canvas.drawLine(-5,10,5,10,p);}
            else if(mode==0){canvas.drawRect(-7,-4,7,3,p);}
            else if(mode==1){canvas.drawLine(-5,-11,-5,10,p);canvas.drawLine(-12,-3,12,-3,p);}
            else{canvas.drawLine(-6,0,6,0,p);canvas.drawLine(-6,0,-3,-3,p);canvas.drawLine(-6,0,-3,3,p);canvas.drawLine(6,0,3,-3,p);canvas.drawLine(6,0,3,3,p);}
            canvas.restore();
        }
    }
}
