# Selected proxy source evidence

These are read-only source findings. Publisher references are not current Fold source identities.
Native Kodi source bindings are recorded separately in SOURCE-BINDINGS.json.

## Existing Kodi to FFmpeg propagation

`xbmc/cores/VideoPlayer/DVDInputStreams/DVDInputStreamFFmpeg.cpp:73–108`
reads `proxy.type`, `proxy.host`, `proxy.port`, `proxy.user`, `proxy.password` from `m_item`.
`xbmc/cores/VideoPlayer/DVDDemuxers/DVDDemuxFFmpeg.cpp:895–918`:

```cpp
const std::string host = input->GetProxyHost();
if (!host.empty() && input->GetProxyType() == "http")
{
  // Existing code constructs http://[user[:password]@]host:port
  av_dict_set(&options, "http_proxy", urlStream.str().c_str(), 0);
}
```

The comment above summarizes intervening existing code; this is an excerpt, not a patch.
Unknown raw URL protocol options are ignored by the earlier allowlist. `proxy.*` ListItem properties are
the demonstrated caller-owned attachment, not a global preference change.

## POV installed export, 2026-11-08

`resources/lib/modules/session.py`, SHA-256
`4f9ece685c857d6f0f596c290dd78cf04b237ca852539fb65be3e9df845bfc2c`:

```python
def request(self, *args, **kwargs):
    kwargs.setdefault('timeout', self.timeout)
    return requests.Session.request(self, *args, **kwargs)
```

This can forward a proxy supplied by its caller. The reviewed actual callers do not supply one;
no proxy reference/configuration was found in exported Python/settings. No installed Requests dependency
identity was established by generic Requests documentation. The separate scraper client SHA-256 remains
`943248a9e3de0350ba12fe409d17ea23d07fb875c5a9ed6e2bc88b1afb8e54b7`.

## Umbrella and Otaku: explicit argument with prohibited side effects

Umbrella publisher6.8.00 `resources/lib/modules/client.py`, SHA-256
`68b9e0a145554a7d6b13e26c5a0eb84c490e3eb7c37fba665b75f3109fc85e8a`, request proxy branch:

```python
handlers += [urllib2.ProxyHandler({'http': '%s' % (proxy)}), urllib2.HTTPHandler]
opener = urllib2.build_opener(*handlers)
urllib2.install_opener(opener)
```

Otaku publisher5.3.4 [pinned source](https://github.com/Goldenfreddy0703/Otaku/blob/f6d542131c958ca63105e37bcf7cd414c9c55684/plugin.video.otaku/resources/lib/ui/client.py),
Git blob `0e34df10df7f88bef86edbdc8c0cdcf7958ec60d`, lines214–218 uses the equivalent HTTP-only
ProxyHandler followed by `urllib.request.install_opener()`. These are not acceptable global-opener hooks.

## The Crew: local opener capability and certificate limitation

Publisher archive [thecrewwh/zips](https://github.com/thecrewwh/zips/blob/master/matrix/_zip/script.module.thecrew/script.module.thecrew-3.2.28.zip),
Git blob `0dd5feab77f1530867325bc5927e68d1c0862081`, archive SHA-256
`c2b7ac78303575c167e7fd1aacfb3b41bdfebb8b05c9f598bedfff78166c3149`.
Internal `script.module.thecrew/lib/resources/lib/modules/client.py`, SHA-256
`f916f6882e9ac13b5c03ef2f484e47b0f20824bc6dba9d3bd53cccf27dd54192`.

`_build_opener_and_cj()`, lines209–210:

```python
if proxy:
    handlers.append(urllib2.ProxyHandler({'http': proxy, 'https': proxy}))
```

The helper builds a local opener and `request()` uses `opener.open()`; this is a genuine per-request
proxy capability. However the normal TLS branch at228–237 creates a default context and then sets
`check_hostname = False` and `verify_mode = CERT_NONE`, including when `request(..., verify=True)`
is called. The other branch explicitly creates an unverified context. Do not silently repair this
third-party helper or present it as a certificate-preserving HTTPS proof.

## FFmpeg reference: proxy support is distinct from family selection

[FFmpeg6.0.1 HTTP](https://github.com/FFmpeg/FFmpeg/blob/n6.0.1/libavformat/http.c),
Git blob `7bce8215354acf845dd6c78556b3332744504647`, lines217–235 selects an explicit
`s->http_proxy` before environment `http_proxy`, but evaluates `no_proxy` too. For HTTPS it passes
`s->http_proxy` to TLS through the options dictionary.

[FFmpeg6.0.1 TLS](https://github.com/FFmpeg/FFmpeg/blob/n6.0.1/libavformat/tls.c),
Git blob `e42d399862b7715d7b4e3786bccac399e77b81cf`, lines94–114 similarly selects explicit
proxy before environment and checks `no_proxy`, then constructs the `httpproxy` CONNECT transport.
These are pinned upstream references, not independent validation of the built dependency archive or
runtime proof of all HLS/HTTPS paths.

## Inputstream boundary

Inspected cached inputstream.adaptive21.5.25 archive SHA-256
`5bec8b8ca1f1ca8264e32455cb34b2939e523f9bdb18cd65d7383d18afdf04cb` is **not installed Fold proof**.
Its public ListItem-property declaration has no explicit proxy field; its generic config contract
requires separate version-specific evidence. `InputStreamAddon.cpp` forwards declared namespaced properties.
This is NOT_VERIFIED, not proof that all inputstream implementations cannot support a proxy.
