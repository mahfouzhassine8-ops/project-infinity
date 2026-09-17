// @append
  /** Layout policy is executed by both the Android view tree and the host regression suite. */
  private static final class CobraModeLayout {
    static final String[] MODES={"mobile","grid","compact","cards","focus"};
    final int width,height;
    final int[] toolbar=new int[4],rail=new int[4],directory=new int[4],video=new int[4],details=new int[4],browser=new int[4],footer=new int[4];
    int columns=1,channelWidth=106;long timeSpan=3600000L;
    boolean wide,smallPreview;
    CobraModeLayout(int w,int h){width=w;height=h;}
    static boolean valid(String mode){for(String m:MODES)if(m.equals(mode))return true;return false;}
    static void box(int[] r,int x,int y,int w,int h){r[0]=x;r[1]=y;r[2]=Math.max(0,w);r[3]=Math.max(0,h);}
    static CobraModeLayout solve(String mode,int width,int height,float font,boolean expanded){
      int w=Math.max(1,width),h=Math.max(1,height);float f=Math.max(1f,Math.min(2f,font));
      CobraModeLayout p=new CobraModeLayout(w,h);p.wide=w>=640&&w>h;
      int top=Math.min(h/4,Math.round(48+10*(f-1))),gap=8,y=top+gap,avail=Math.max(1,h-y);
      box(p.toolbar,0,0,w,top);
      if("grid".equals(mode)){
        int rail=w>=720&&h>=300?52:0;
        int dir=expanded&&w-rail>=720?Math.min(204,Math.round(164+20*(f-1))):0;
        if(rail>0)box(p.rail,0,y,rail,avail);
        if(dir>0)box(p.directory,rail+gap,y,dir,avail);
        int x=rail+(dir>0?dir+gap:0)+(rail>0?gap:0),body=w-x;
        int hero=Math.min(p.wide?172:122,Math.max(64,avail/3));
        int vw=Math.min(Math.round(body*(p.wide?.42f:.46f)),hero*16/9);
        if(body<300){hero=Math.min(118,avail/3);vw=body;box(p.video,x,y,vw,hero);box(p.details,x,y+hero,body,Math.min(70,avail/5));hero+=p.details[3];}
        else {box(p.video,x,y,vw,Math.min(hero,vw*9/16));box(p.details,x+vw+gap,y,body-vw-gap,hero);}
        box(p.browser,x,y+hero+gap,body,h-y-hero-gap);
        p.channelWidth=body>=640?Math.round(166*f):body>=420?126:96;
        p.channelWidth=Math.min(p.channelWidth,Math.max(80,body/3));
        p.timeSpan=body>=940?10800000L:body>=560?7200000L:3600000L;p.smallPreview=true;
      }else if("compact".equals(mode)){
        int hero=Math.min(104,Math.max(64,avail/5)),vw=Math.min(172,w/3);
        box(p.video,w-vw,y,vw,Math.min(hero,vw*9/16));box(p.details,0,y,w-vw-gap,hero);
        box(p.browser,0,y+hero+gap,w,h-y-hero-gap);p.smallPreview=true;
      }else if("cards".equals(mode)){
        if(p.wide&&w>=800){int side=Math.min(336,w/3),vh=Math.min(side*9/16,avail/2);box(p.video,0,y,side,vh);box(p.details,0,y+vh+gap,side,avail-vh-gap);box(p.browser,side+16,y,w-side-16,avail);}
        else {int hero=Math.min(190,Math.max(96,avail/4));int vw=Math.min(w/2,hero*16/9);if(w<340){vw=w;hero=Math.min(138,avail/4);box(p.video,0,y,w,hero);box(p.details,0,y+hero,w,Math.min(66,avail/7));hero+=p.details[3];}
          else{box(p.video,0,y,vw,Math.min(hero,vw*9/16));box(p.details,vw+gap,y,w-vw-gap,hero);}box(p.browser,0,y+hero+gap,w,h-y-hero-gap);}
        p.columns=Math.max(1,Math.min(5,(p.browser[2]+10)/Math.round(158+35*(f-1))));p.smallPreview=p.video[2]<280;
      }else if("focus".equals(mode)){
        if(p.wide){int main=Math.round(w*.65f),vh=Math.min(main*9/16,Math.max(80,avail-Math.round(108*f)));box(p.video,0,y,main,vh);box(p.details,0,y+vh+gap,main,avail-vh-gap);box(p.browser,main+16,y,w-main-16,avail);}
        else {int vh=Math.min(w*9/16,Math.max(108,Math.round(avail*.38f))),info=Math.min(Math.round(118*f),Math.max(80,avail/5));box(p.video,0,y,w,vh);box(p.details,0,y+vh,w,info);box(p.browser,0,y+vh+info+gap,w,h-y-vh-info-gap);}
      }else{
        int foot=avail>=420?56:0;
        if(p.wide){int left=Math.min(Math.round(w*.43f),470),vh=Math.min(left*9/16,Math.max(80,avail-106-foot));box(p.video,0,y,left,vh);box(p.details,0,y+vh+gap,left,avail-vh-gap-foot);box(p.browser,left+16,y,w-left-16,avail-foot);}
        else{int vh=Math.min(w*9/16,Math.max(104,Math.round(avail*.29f))),info=Math.min(Math.round(96*f),Math.max(70,avail/6));box(p.video,0,y,w,vh);box(p.details,0,y+vh,w,info);box(p.browser,0,y+vh+info+gap,w,h-y-vh-info-gap-foot);}
        if(foot>0)box(p.footer,0,h-foot,w,foot);
      }
      // In split windows reserve a usable channel browser instead of a huge empty hero.
      if(!p.wide && p.browser[3]<180 && avail>=150){
        int browse=Math.min(180,Math.max(100,avail*3/5));
        int hero=Math.max(24,avail-browse-gap);
        int x=p.browser[0],body=p.browser[2];
        int vw=Math.min(body/2,hero*16/9);
        box(p.video,x,y,vw,Math.min(hero,vw*9/16));
        box(p.details,x+vw+gap,y,Math.max(0,body-vw-gap),hero);
        box(p.browser,x,y+hero+gap,body,h-y-hero-gap);
        box(p.footer,0,0,0,0);p.smallPreview=true;
      }
      // Small split windows retain a useful browser rather than negative/cropped bounds.
      for(int[] r:new int[][]{p.toolbar,p.rail,p.directory,p.video,p.details,p.browser,p.footer}){
        r[0]=Math.max(0,Math.min(w,r[0]));r[1]=Math.max(0,Math.min(h,r[1]));r[2]=Math.min(r[2],w-r[0]);r[3]=Math.min(r[3],h-r[1]);
      }
      return p;
    }
    static long stableId(String key){long h=0xcbf29ce484222325L;for(int i=0;i<key.length();i++){h^=key.charAt(i);h*=0x100000001b3L;}return h;}
    static int cellHeight(String mode,float font){float f=Math.max(1f,Math.min(2f,font));return Math.round(("compact".equals(mode)?50:"cards".equals(mode)?200:"focus".equals(mode)?84:"grid".equals(mode)?56:106)+(f-1)*("cards".equals(mode)?60:36));}
  }
