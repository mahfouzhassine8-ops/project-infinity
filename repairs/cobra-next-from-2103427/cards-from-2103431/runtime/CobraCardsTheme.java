package com.projectinfinity.kodi;

import android.app.Activity;

/** Cards-only adapter to the existing native appearance resolver. No settings,
 * palette definitions, listeners or navigation ownership are introduced here. */
final class CobraCardsTheme {
  static final Colors DARK=new Colors(false,0,0,0,0,0,0,0);
  private static final Class<?>[] STRING={String.class};
  private CobraCardsTheme(){}
  static Colors resolve(Activity owner){
    if(Boolean.TRUE.equals(CobraArrange.ownedCall(owner,"cobraModeDark",new Class<?>[0])))return DARK;
    return new Colors(true,color(owner,"background"),color(owner,"panel"),color(owner,"panel2"),
        color(owner,"text"),color(owner,"muted"),color(owner,"accent"),color(owner,"line"));
  }
  private static int color(Activity a,String role){return ((Number)CobraArrange.ownedCall(a,"cobraModeColor",STRING,role)).intValue();}
  static final class Colors {
    final boolean light;final int background,panel,panel2,text,muted,accent,border;
    Colors(boolean l,int b,int p,int p2,int t,int m,int a,int edge){light=l;background=b;panel=p;panel2=p2;text=t;muted=m;accent=a;border=edge;}
    int text(int original){return light?text:original;}
    int muted(int original){return light?muted:original;}
    int accent(int original){return light?accent:original;}
    int edge(int original){return light?border:original;}
    int[] gradient(int a,int b,int c){return light?new int[]{panel,panel2,panel}:new int[]{a,b,c};}
    boolean same(Colors c){return light==c.light && background==c.background && panel==c.panel && panel2==c.panel2 && text==c.text && muted==c.muted && accent==c.accent && border==c.border;}
  }
}
