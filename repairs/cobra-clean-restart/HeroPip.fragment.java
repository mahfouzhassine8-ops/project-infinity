    /** Place only the new target. Never move, shrink or repurpose an approved control. */
    void layoutPip(int w,int h){
      if(pip.getVisibility()!=VISIBLE)return;
      java.util.ArrayList<android.graphics.RectF> occupied=new java.util.ArrayList<>();
      for(View v:new View[]{live,source,logo,status,preview,unmute,left,right,sportsWatch,sportsStats,sportsMulti,info,dots}){
        if(v.getParent()!=this||v.getVisibility()!=VISIBLE||v.getAlpha()<=0f||v.getWidth()<=0||v.getHeight()<=0)continue;
        float x=v.getLeft()+v.getTranslationX()+v.getPivotX()*(1-v.getScaleX());
        float y=v.getTop()+v.getTranslationY()+v.getPivotY()*(1-v.getScaleY());
        android.graphics.RectF box=new android.graphics.RectF(x,y,x+v.getWidth()*v.getScaleX(),y+v.getHeight()*v.getScaleY());
        if(box.intersect(0,0,w,h))occupied.add(box);
      }
      int gap=px(getContext(),2);
      // The compact Fold window has a 112dp Hero. 40dp is the smallest new target;
      // full-size windows retain 48dp. Original targets keep their exact geometry.
      for(int sideDp:new int[]{48,44,40}){
        int side=px(getContext(),sideDp);
        java.util.LinkedHashSet<Integer> xs=new java.util.LinkedHashSet<>(),ys=new java.util.LinkedHashSet<>();
        xs.add((w-side)/2);xs.add(gap);xs.add(w-side-gap);ys.add(gap);ys.add(h-side-gap);
        for(android.graphics.RectF box:occupied){xs.add((int)Math.ceil(box.right)+gap);xs.add((int)Math.floor(box.left)-side-gap);ys.add((int)Math.ceil(box.bottom)+gap);ys.add((int)Math.floor(box.top)-side-gap);}
        for(int y:ys)for(int x:xs){
          if(x<gap||y<gap||x+side>w-gap||y+side>h-gap)continue;
          android.graphics.RectF trial=new android.graphics.RectF(x,y,x+side,y+side);boolean free=true;
          for(android.graphics.RectF box:occupied)if(android.graphics.RectF.intersects(trial,box)){free=false;break;}
          if(free){place(pip,x,y,side,side);return;}
        }
      }
      // No unsafe fallback over existing controls. Runtime validation must reject
      // an unsupported geometry rather than disguising overlap as a successful fit.
      place(pip,0,0,0,0);
    }
