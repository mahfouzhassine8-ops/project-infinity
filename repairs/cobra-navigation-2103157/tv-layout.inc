        // Dimensions come from the measured shell, including portrait/Fold, not device orientation.
        int rail=w>=960&&avail>=300?48:0;
        int dir=expanded&&w>=760&&avail>=220?Math.min(188,Math.round(148+24*(f-1))):0;
        if(rail>0)box(p.rail,0,y,rail,avail);
        int dx=rail>0?rail+gap:0;
        if(dir>0)box(p.directory,dx,y,dir,avail);
        int x=dx+(dir>0?dir+gap:0),body=w-x;
        // Portrait uses the full width for video with compact information BELOW it.
        // Landscape/Fold uses preview + information side by side, leaving a dense EPG below.
        int hero;
        if(body<540 && h>w){
          int vh=Math.min(body*9/16,Math.max(36,avail*28/100));
          int info=Math.min(Math.round(70*f),Math.max(36,avail/7));
          int ceiling=Math.max(70,avail-Math.min(240,avail/2)-gap);
          if(vh+info>ceiling)vh=Math.max(32,ceiling-info);
          box(p.video,x,y,body,vh);box(p.details,x,y+vh,body,info);hero=vh+info;
        }else{
          hero=Math.min(Math.round(154+18*(f-1)),Math.max(48,avail*29/100));
          int vw=Math.min(Math.round(body*.43f),hero*16/9);
          box(p.video,x,y,vw,Math.min(hero,vw*9/16));
          box(p.details,x+vw+gap,y,body-vw-gap,hero);
        }
        box(p.browser,x,y+hero+gap,body,h-y-hero-gap);
        p.channelWidth=Math.min(Math.round(132+20*(f-1)),Math.max(72,body/3));
        p.timeSpan=body>=940?10800000L:body>=540?7200000L:3600000L;p.smallPreview=true;
