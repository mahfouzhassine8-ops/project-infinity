package com.projectinfinity.kodi;

/** Cobra presentation only. No player, network, persistence or lifecycle APIs. */
public final class CobraLayoutCatalog {
  private CobraLayoutCatalog() {}
  private static final String[] IDS = {"equal2","pip-br","pip-bl","pip-tr","pip-tl",
      "main2","overlay2","columns3","grid4","main3","overlay3"};
  private static final String[] LABELS = {"50/50","Picture in Picture — Bottom Right",
      "Picture in Picture — Bottom Left","Picture in Picture — Top Right",
      "Picture in Picture — Top Left","Main + Two","Main + Two Overlays",
      "Three Columns","2×2 Grid","Main + Three","Main + Three Overlays"};

  public static int count(String id) {
    for (int i=0;i<IDS.length;i++) if (IDS[i].equals(id)) return i<5?2:i<8?3:4;
    return 0;
  }
  public static String[] all(){return IDS.clone();}
  public static boolean valid(String id,int count) { return count>=2 && count<=4 && count(id)==count; }
  public static String label(String id) {
    for(int i=0;i<IDS.length;i++) if(IDS[i].equals(id)) return LABELS[i];
    throw new IllegalArgumentException("Unknown Cobra arrangement");
  }
  public static String[] forCount(int count) {
    int start=count==2?0:count==3?5:count==4?8:-1;
    if(start<0) return new String[0];
    int size=count==2?5:3;String[] result=new String[size];
    System.arraycopy(IDS,start,result,0,size);return result;
  }
  public static int[] rect(String id,int index,int count,int width,int height,int gap) {
    if(!valid(id,count) || index<0 || index>=count || width<1 || height<1)
      throw new IllegalArgumentException("Invalid Cobra arrangement geometry");
    int w=width,h=height,x=0,y=0,rw=w,rh=h;
    gap=Math.max(0,Math.min(gap,Math.min(w,h)/12));
    boolean wide=w>=h;
    if(id.equals("equal2")) {
      if(wide){x=index*w/2;rw=(index+1)*w/2-x;}
      else{y=index*h/2;rh=(index+1)*h/2-y;}
    } else if(id.startsWith("pip-")) {
      if(index==1){rw=Math.max(1,w/3);rh=Math.max(1,h/3);
        x=id.endsWith("r")?w-rw-gap:gap;y=id.contains("-b")?h-rh-gap:gap;}
    } else if(id.equals("columns3")) {
      x=index*w/3;rw=(index+1)*w/3-x;
    } else if(id.equals("grid4")) {
      x=(index%2)*w/2;y=(index/2)*h/2;
      rw=(index%2+1)*w/2-x;rh=(index/2+1)*h/2-y;
    } else if(id.equals("main2") || id.equals("main3")) {
      int small=count-1;
      if(wide){int main=w*2/3;if(index==0)rw=main;
        else{x=main;rw=w-main;y=(index-1)*h/small;rh=index*h/small-y;}}
      else{int main=h*2/3;if(index==0)rh=main;
        else{y=main;rh=h-main;x=(index-1)*w/small;rw=index*w/small-x;}}
    } else if(id.equals("overlay2") && index>0) {
      rw=Math.max(1,w/3);rh=Math.max(1,h/3);x=w-rw-gap;
      y=index==1?gap:h-rh-gap;
    } else if(id.equals("overlay3") && index>0) {
      rw=Math.max(1,(w-gap*4)/3);rh=Math.max(1,h/3);
      x=gap+(index-1)*(rw+gap);y=h-rh-gap;
    }
    x=Math.max(0,Math.min(x,w-1));y=Math.max(0,Math.min(y,h-1));
    rw=Math.max(1,Math.min(rw,w-x));rh=Math.max(1,Math.min(rh,h-y));
    return new int[]{x,y,rw,rh};
  }
}
