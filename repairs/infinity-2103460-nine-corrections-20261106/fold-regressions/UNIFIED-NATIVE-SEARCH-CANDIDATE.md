# Unified native-provider Search — isolated source candidate

Source parent: 86d5b5e2b65acb878632d407c3a3a07dd1af3b6d

This candidate implements the owner's common Search UI routing correction.
The provider is still the sole engine executing its own native search through
the verified existing route() + Files.GetDirectory path. There is no new
scraper, provider code, network client, or replacement results UI.

## Scoped source modification
- In the existing Search form, Search All continues to use search-all.
- An explicitly selected provider now routes to the ALREADY-existing
  Command Center search-provider action rather than leaving Infinity Search
  for the provider's separate native GUI. The existing one-provider result
  collector still invokes that provider's verified original native route
  through Kodi's owned Files.GetDirectory and publishes rows through
  _publish_result. Its native result destinations and headings remain intact.
- Legacy provider history continues to use the provider's verified original
  native history route without entering the aggregate result collector.
- Verify the source route before selecting any target and again after the
  original history writer; abort still takes precedence over activation.
- Add independent process-local atomic modal admission BEFORE slow inventory,
  history and xbmc.Keyboard.doModal; a repeated tap cannot start a second
  first-party Search modal while the first entry is open. This uses the same
  Android/Linux abstract Unix-socket technique as the already shipped native
  RPC admission, but with a separate key and lifetime. It does not modify
  keyboard internals and is NOT a native crash repair.

## Explicit limits
This is a candidate, not an installed fix. No signed ZIP, APK, recovery,
native compilation, Android test, or Fold acceptance. The frozen 86d5b5e2
branch, installed components, original signer and all other Kodi/Cobra/Preview
sources remain unchanged.

The shared strict settings.xml state/ABA/source validation is unchanged. The
existing false-positive rejection when provider settings are rewritten during
an owned native search remains a separate release blocker. Do not accept
final-XML-only comparison or timestamp exceptions; an unobserved meaningful
change followed by restoration is not safe to ignore. Real writer provenance
or a verified equivalent consistency contract is needed before accepting
those rows. A provider update which genuinely changes verified source code
also still requires compatible source verification.

Native keyboard callback ownership and GraphicContext origin stack crashes
remain unresolved. Modal single-flight reduces a suspected first-party
overlap risk only; it cannot prove either native fault is repaired.

## Required host checks
- Search All action and explicit provider action take the same Infinity
  search-results publisher with one or all verified native providers.
- Single-provider selection uses search-provider with original provider ID,
  category and query; no duplicate native request.
- Legacy history remains provider-native; changed source after history
  persistence and abort refuse dispatch.
- Double invocation cannot open a second Search modal; admission releases
  after normal return.
- Verify unchanged _provider_result/_query_signature/_leased_directory,
  native route checks, publisher, plugin, Cobra, Preview and other components.
- Retain the baseline frozen 7/7 source regression PASS separately.

This is the smallest compatible UI-routing implementation of the new
architecture; it is NOT an end-to-end universal Search release.
