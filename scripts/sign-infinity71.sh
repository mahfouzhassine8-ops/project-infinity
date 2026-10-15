#!/usr/bin/env bash
# Sign a test candidate or use the owner's stable signing secret; never upload a private key.
set -euo pipefail
if [[ $# -ne 2 ]]; then echo 'Usage: sign-infinity71.sh unsigned.apk signed.apk' >&2; exit 2; fi
INPUT=$1
OUTPUT=$2
BT="${ANDROID_HOME:?ANDROID_HOME required}/build-tools/34.0.0"
# Never silently substitute a test identity for a partially configured stable key.
configured=0
for name in INFINITY_KEYSTORE_B64 INFINITY_STORE_PASSWORD INFINITY_KEY_PASSWORD INFINITY_KEY_ALIAS; do
  if [[ -n "${!name:-}" ]]; then configured=$((configured + 1)); fi
done
if [[ "$configured" -ne 0 && "$configured" -ne 4 ]]; then
  echo 'Incomplete stable signing configuration: set all four INFINITY signing secrets or leave all four unset. No fallback signature was created.' >&2
  exit 2
fi
if [[ ! -f "$INPUT" ]]; then echo 'Input APK does not exist' >&2; exit 2; fi
if [[ ! -x "$BT/zipalign" || ! -x "$BT/apksigner" ]]; then
  echo 'Android Build Tools 34.0.0 are required for signing' >&2
  exit 2
fi
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
umask 077
if [[ -n "${INFINITY_KEYSTORE_B64:-}" ]]; then
  : "${INFINITY_STORE_PASSWORD:?Stable keystore password required}"
  : "${INFINITY_KEY_PASSWORD:?Stable key password required}"
  : "${INFINITY_KEY_ALIAS:?Stable key alias required}"
  printf '%s' "$INFINITY_KEYSTORE_B64" | base64 --decode > "$TMP/signing.keystore"
  keytool -list -keystore "$TMP/signing.keystore" \
    -storepass:env INFINITY_STORE_PASSWORD -alias "$INFINITY_KEY_ALIAS" >/dev/null
  MODE=stable-secret
else
  export INFINITY_STORE_PASSWORD=android
  export INFINITY_KEY_PASSWORD=android
  INFINITY_KEY_ALIAS=androiddebugkey
  keytool -genkeypair -noprompt -keystore "$TMP/signing.keystore" \
    -storepass android -keypass android -alias androiddebugkey \
    -keyalg RSA -keysize 2048 -validity 10000 \
    -dname 'CN=Infinity Test Only,O=Project Infinity,C=US' >/dev/null 2>&1
  MODE=ephemeral-test-only
  echo '::warning::This candidate uses a new test certificate. Do not uninstall an existing Infinity installation without a verified backup. Install-over compatibility is NOT promised.'
fi
"$BT/zipalign" -p -f 4 "$INPUT" "$TMP/aligned.apk"
"$BT/apksigner" sign --ks "$TMP/signing.keystore" --ks-key-alias "$INFINITY_KEY_ALIAS" \
  --ks-pass env:INFINITY_STORE_PASSWORD --key-pass env:INFINITY_KEY_PASSWORD \
  --out "$OUTPUT" "$TMP/aligned.apk"
"$BT/apksigner" verify --verbose --print-certs "$OUTPUT" > "${OUTPUT%.apk}.signing.txt"
"$BT/zipalign" -c -p 4 "$OUTPUT"
printf '\nSigning mode: %s\nRuntime/device verification: NOT YET PERFORMED\n' "$MODE" >> "${OUTPUT%.apk}.signing.txt"
sha256sum "$OUTPUT" > "${OUTPUT%.apk}.sha256"
