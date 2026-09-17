package android.net;
public class Uri {
 public static Uri parse(String s){throw new UnsupportedOperationException("Android URI not under host test");}
 public String getPath(){throw new UnsupportedOperationException();}
 public String getQueryParameter(String k){throw new UnsupportedOperationException();}
 public Builder buildUpon(){throw new UnsupportedOperationException();}
 public static class Builder {public Builder path(String x){return this;}public Builder clearQuery(){return this;}public Builder appendQueryParameter(String k,String v){return this;}public Uri build(){throw new UnsupportedOperationException();}}
}