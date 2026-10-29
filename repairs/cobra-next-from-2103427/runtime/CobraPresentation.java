package com.projectinfinity.kodi;

import android.app.Activity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import java.util.WeakHashMap;

/** Reuse exact Cobra views/callbacks; do not reconstruct controls or players. */
public final class CobraPresentation {
  private static final WeakHashMap<LinearLayout,Integer> ORIGINAL_MORE=new WeakHashMap<>();
  private CobraPresentation() {}
  public static void position(View view,int x,int y,int width,int height) {
    if(view==null)return;
    x=Math.max(0,x);y=Math.max(0,y);width=Math.max(1,width);height=Math.max(1,height);
    ViewGroup.LayoutParams old=view.getLayoutParams();
    if(old!=null && old.getClass()==FrameLayout.LayoutParams.class){
      FrameLayout.LayoutParams p=(FrameLayout.LayoutParams)old;
      if(p.width==width && p.height==height && p.leftMargin==x && p.topMargin==y &&
          p.rightMargin==0 && p.bottomMargin==0 && p.gravity==-1 && !p.isMarginRelative())return;
    }
    FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(width,height);
    p.leftMargin=x;p.topMargin=y;view.setLayoutParams(p);
  }
  public static void moreLast(Activity owner,LinearLayout row) {
    if(row==null)return;
    View more=null;
    for(int i=0;i<row.getChildCount();i++){
      View child=row.getChildAt(i);Object tag=child.getTag();
      if("cobra_player_options_anchor".equals(tag) || "cobra_preview_options_anchor".equals(tag)){
        if(more!=null)throw new IllegalStateException("Duplicate Cobra More control");
        more=child;
      }
    }
    if(more==null)return;
    Integer original=ORIGINAL_MORE.get(row);
    if(original==null){original=row.indexOfChild(more);ORIGINAL_MORE.put(row,original);}
    int desired=CobraArrange.isPro(owner)?original:row.getChildCount()-1;
    if(row.indexOfChild(more)!=desired){
      boolean focus=more.hasFocus();ViewGroup.LayoutParams p=more.getLayoutParams();
      row.removeView(more);row.addView(more,Math.min(desired,row.getChildCount()),p);if(focus)more.requestFocus();
    }
  }
  public static void previewReused(Activity owner,FrameLayout root){
    if(root!=null){View controls=root.findViewWithTag("cobra_preview_controls");
      if(controls instanceof LinearLayout)moreLast(owner,(LinearLayout)controls);}
  }
}
