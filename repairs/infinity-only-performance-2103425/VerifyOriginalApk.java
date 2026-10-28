// Host verification tool only; never packaged in the application.
import com.android.apksig.ApkVerifier;
import java.io.File;
import java.security.MessageDigest;
import java.util.HexFormat;

class VerifyOriginalApk {
  public static void main(String[] args) throws Exception {
    if (args.length != 1) throw new IllegalArgumentException("APK path required");
    ApkVerifier.Result result = new ApkVerifier.Builder(new File(args[0])).build().verify();
    if (!result.isVerified() || !result.isVerifiedUsingV1Scheme() ||
        !result.isVerifiedUsingV2Scheme() || !result.isVerifiedUsingV3Scheme() ||
        result.getSignerCertificates().size() != 1)
      throw new SecurityException("APK verification failed: " + result.getErrors());
    String fingerprint = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(
        result.getSignerCertificates().get(0).getEncoded()));
    if (!fingerprint.equals("d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7"))
      throw new SecurityException("Original certificate required");
    System.out.println("INDEPENDENT_APK_SIGNATURE_VERIFIED schemes=v1,v2,v3 certificate_sha256=" + fingerprint);
  }
}
