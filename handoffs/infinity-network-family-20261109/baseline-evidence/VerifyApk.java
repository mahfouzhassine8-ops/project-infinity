import com.android.apksig.ApkVerifier;
import java.io.File;
import java.security.MessageDigest;
import java.util.HexFormat;
public class VerifyApk {
 public static void main(String[] a) throws Exception {
  ApkVerifier.Result r=new ApkVerifier.Builder(new File(a[0])).setMinCheckedPlatformVersion(21).setMaxCheckedPlatformVersion(36).build().verify();
  System.out.println("verified="+r.isVerified()+" v1="+r.isVerifiedUsingV1Scheme()+" v2="+r.isVerifiedUsingV2Scheme()+" v3="+r.isVerifiedUsingV3Scheme());
  for(var c:r.getSignerCertificates())System.out.println("certificate_sha256="+HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(c.getEncoded())));
  for(var e:r.getAllErrors())System.out.println("ERROR "+e);
  if(!r.isVerified())System.exit(1);
 }
}
