package com.projectinfinity.kodi;

/** Container termination contract. No player, preference or feature state.
 * Owner adapters keep their original private admission locks and receipts.
 * A retained Cobra session and its container preferences remain writable.
 * Their receipts are never used to authorize killing the retained process.
 */
public final class CombinedDurability {
  public interface Port {
    Object lock();
    boolean canBegin(String ticket);
    boolean begin(String ticket);
    String sealIfReady(String ticket);
    boolean authorized(String ticket, String proof);
    String pending();
    void cancel(String ticket);
  }
  public interface Retention {
    Object lock();
    boolean active();
  }
  public static final class Group {
    private final Port[] ports;
    private final Retention cobra;
    private Plan plan;
    private static final class Plan {
      final String ticket;
      final boolean retainCobra;
      Plan(String ticket, boolean retained) { this.ticket=ticket; retainCobra=retained; }
    }
    public Group(Port infinity, Port cobraPort, Port shell, Retention retention) {
      if(infinity==null||cobraPort==null||shell==null||retention==null)throw new NullPointerException();
      ports=new Port[]{infinity,cobraPort,shell}; cobra=retention;
      if(ports[0].lock()==ports[1].lock()||ports[1].lock()==ports[2].lock()||ports[0].lock()==ports[2].lock())
        throw new IllegalArgumentException("Owner locks must be distinct");
    }
    private interface Work<T> { T run(); }
    private <T> T locked(Work<T> work) {
      synchronized(ports[0].lock()) { synchronized(ports[1].lock()) {
        synchronized(ports[2].lock()) { synchronized(cobra.lock()) { return work.run(); } }
      } }
    }
    public boolean begin(final String ticket) { return locked(()->{
      if(ticket==null||ticket.isEmpty())return false;
      if(plan!=null&&plan.ticket.equals(ticket)) {
        for(int i=0;i<3;i++)if(!(i!=0&&plan.retainCobra)&&!ports[i].canBegin(ticket))return false;
        for(int i=0;i<3;i++)if(!(i!=0&&plan.retainCobra)&&!ports[i].begin(ticket))
          throw new IllegalStateException("Owner admission changed under its lock");
        return true;
      }
      boolean retained=cobra.active();
      for(int i=0;i<3;i++)if(!(i!=0&&retained)&&!ports[i].canBegin(ticket))return false;
      for(int i=0;i<3;i++)if(!(i!=0&&retained)&&!ports[i].begin(ticket))
        throw new IllegalStateException("Owner admission changed under its lock");
      plan=new Plan(ticket,retained); return true;
    }); }
    public String sealIfReady(final String ticket) { return locked(()->{
      if(plan==null||!plan.ticket.equals(ticket))return "";
      StringBuilder result=new StringBuilder("owners-v1");
      for(int i=0;i<3;i++) {
        String seal=i!=0&&plan.retainCobra?"retained":ports[i].sealIfReady(ticket);
        if(seal==null||seal.isEmpty()||seal.indexOf('|')>=0)return "";
        result.append('|').append(seal);
      }
      return result.toString();
    }); }
    private boolean valid(String ticket,String proof) {
      if(plan==null||!plan.ticket.equals(ticket)||proof==null)return false;
      String[] pieces=proof.split("\\|",-1);
      if(pieces.length!=4||!pieces[0].equals("owners-v1"))return false;
      for(int i=0;i<3;i++) {
        if(i!=0&&plan.retainCobra) { if(!pieces[i+1].equals("retained"))return false; }
        else if(!ports[i].authorized(ticket,pieces[i+1]))return false;
      }
      return true;
    }
    public boolean authorized(final String ticket, final String proof) {
      return locked(()->valid(ticket,proof));
    }
    public boolean whileAuthorized(final String ticket, final String proof, final Runnable action) {
      if(action==null)throw new NullPointerException();
      return locked(()->{
        if(!valid(ticket,proof)||plan.retainCobra||cobra.active())return false;
        // The existing native authorization/receipt/termination callback stays
        // unchanged and executes while every affected owner's lock is held.
        action.run(); return true;
      });
    }
    /** Only the coordinator's verified engine-retired boundary calls this.
     * Retaining the process reopens admission without clearing pending writes
     * or failures. The engine lease must continue to use whileAuthorized.
     */
    public boolean finishCoordinator(final String ticket, final String proof, final Runnable action) {
      return locked(()->{
        if(whileAuthorized(ticket,proof,action))return true;
        cancel(ticket);
        return false;
      });
    }
    public String pending() { return locked(()->{
      for(int i=0;i<3;i++) {
        if(i!=0&&plan!=null&&plan.retainCobra)continue;
        String value=ports[i].pending(); if(!value.isEmpty())return value;
      }
      return "";
    }); }
    public void cancel(final String ticket) { locked(()->{
      if(plan==null||!plan.ticket.equals(ticket))return null;
      for(int i=0;i<3;i++)if(!(i!=0&&plan.retainCobra))ports[i].cancel(ticket);
      plan=null; return null;
    }); }
  }
  private static final Group GROUP=OwnerDurabilityWiring.create();
  private CombinedDurability() {}
  public static boolean begin(String ticket){return GROUP.begin(ticket);}
  public static String sealIfReady(String ticket){return GROUP.sealIfReady(ticket);}
  public static String pending(){return GROUP.pending();}
  public static boolean authorized(String ticket,String proof){return GROUP.authorized(ticket,proof);}
  public static boolean whileAuthorized(String ticket,String proof,Runnable action){return GROUP.whileAuthorized(ticket,proof,action);}
  public static boolean finishCoordinator(String ticket,String proof,Runnable action){return GROUP.finishCoordinator(ticket,proof,action);}
  public static void cancel(String ticket){GROUP.cancel(ticket);}
}
