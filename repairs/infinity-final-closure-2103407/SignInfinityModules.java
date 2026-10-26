// CI build tool only. Never packaged in an APK or component ZIP.
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.KeyStore;
import java.security.MessageDigest;
import java.security.PrivateKey;
import java.security.Signature;
import java.security.cert.Certificate;
import java.util.Arrays;

final class SignInfinityModules {
  private static String env(String name) {
    String value=System.getenv(name);
    if(value==null || value.isEmpty())throw new IllegalStateException("Existing permanent signing credentials required");
    return value;
  }
  private static String hex(byte[] raw)throws Exception {
    StringBuilder result=new StringBuilder();
    for(byte b:raw)result.append(String.format(java.util.Locale.ROOT,"%02x",b&255));
    return result.toString();
  }
  public static void main(String[] args)throws Exception {
    if(args.length!=2)throw new IllegalArgumentException("Keystore path and canonical manifest path required");
    Path path=Paths.get(args[1]);
    byte[] payload=Files.readAllBytes(path);
    if(payload.length==0 || payload.length>131072 || payload[payload.length-1]!='\n' ||
       !new String(payload,java.nio.charset.StandardCharsets.US_ASCII).startsWith("INFINITY-MODULES/1\npackage\t"))
      throw new IllegalArgumentException("Only a bounded Infinity module payload may be signed");
    Path output=Paths.get(args[1]+".sig");
    if(Files.exists(output))throw new IllegalStateException("Existing signature must not be overwritten");
    char[] storePass=env("INFINITY_STORE_PASSWORD").toCharArray();
    char[] keyPass=env("INFINITY_KEY_PASSWORD").toCharArray();
    try {
      KeyStore store=KeyStore.getInstance(KeyStore.getDefaultType());
      try(InputStream input=Files.newInputStream(Paths.get(args[0]))) {store.load(input,storePass);}
      String alias=env("INFINITY_KEY_ALIAS");
      Certificate certificate=store.getCertificate(alias);
      if(certificate==null || !hex(MessageDigest.getInstance("SHA-256").digest(certificate.getEncoded())).equals(
          "d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7"))
        throw new SecurityException("Original permanent signing certificate required");
      PrivateKey key=(PrivateKey)store.getKey(alias,keyPass);
      if(key==null || !"RSA".equals(key.getAlgorithm()))throw new SecurityException("Original RSA private key required");
      Signature signer=Signature.getInstance("SHA256withRSA");
      signer.initSign(key);signer.update(payload);byte[] signed=signer.sign();
      Signature verifier=Signature.getInstance("SHA256withRSA");
      verifier.initVerify(certificate);verifier.update(payload);
      if(!verifier.verify(signed))throw new SecurityException("Signature self-verification failed");
      if(!Arrays.equals(payload,Files.readAllBytes(path)))throw new SecurityException("Manifest generation changed");
      Files.write(output,signed,java.nio.file.StandardOpenOption.CREATE_NEW);
      System.out.println("ORIGINAL_PERMANENT_RSA_SIGNATURE manifest="+hex(MessageDigest.getInstance("SHA-256").digest(payload)));
    } finally {Arrays.fill(storePass,'\0');Arrays.fill(keyPass,'\0');}
  }
}
