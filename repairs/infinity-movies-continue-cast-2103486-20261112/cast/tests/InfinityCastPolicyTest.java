package com.projectinfinity.kodi;
/** Actual policy, host URI parser. No network or receiver simulation. */
public final class InfinityCastPolicyTest {
 public static void main(String[] args) {
  String[] refused={"https://user:secret@example.invalid/video.mp4",
   "https://example.invalid/video.mp4?token=secret","https://example.invalid/video.mp4#private",
   "https://example.invalid/video.mp4|Cookie=secret","https://example.invalid/token/secret/video.mp4",
   "https://example.invalid/ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz/video.mp4",
   "file:///private/video.mp4","https://example.invalid/unverified-transport",
   "http://localhost/video.mp4","http://127.0.0.1/video.mp4","http://[::1]/video.mp4",
   "https://example.invalid/video.mp4\n"};
  for(String url:refused)if(InfinityCastPolicy.mime(url)!=null)throw new AssertionError("Private or unsupported URI admitted");
  if(!"video/mp4".equals(InfinityCastPolicy.mime("https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4")))throw new AssertionError("Public MP4 refused");
  if(!"application/x-mpegURL".equals(InfinityCastPolicy.mime("https://media.invalid/public/stream.m3u8")))throw new AssertionError("Public HLS refused");
  System.out.println("PASS_CAST_URI_POLICY_12_REFUSALS_AND_PUBLIC_FORMATS_HOST_ONLY_NOT_RECEIVER_OR_AUTH_PROVENANCE");
 }
}
