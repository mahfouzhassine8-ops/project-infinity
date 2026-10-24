#!/usr/bin/env bash
# Production path: one retained owner key, pinned certificate, no throwaway fallback.
set -euo pipefail
[[ $# == 2 ]] || { echo 'Usage: sign-infinity-mobile.sh unsigned.apk signed.apk' >&2; exit 2; }
INPUT=$1; OUTPUT=$2
[[ -f "$INPUT" && ! -e "$OUTPUT" && "$INPUT" != "$OUTPUT" ]] || { echo 'Invalid input or existing output' >&2; exit 2; }
for name in INFINITY_KEYSTORE_B64 INFINITY_STORE_PASSWORD INFINITY_KEY_PASSWORD INFINITY_KEY_ALIAS INFINITY_SIGNER_SHA256; do
  [[ -n "${!name:-}" ]] || { echo 'BLOCKED: persistent signing configuration is incomplete; no fallback key created.' >&2; exit 3; }
done
EXPECTED=${INFINITY_SIGNER_SHA256,,}
[[ "$EXPECTED" =~ ^[0-9a-f]{64}$ ]] || { echo 'Invalid pinned certificate fingerprint' >&2; exit 3; }
BT="${ANDROID_HOME:?}/build-tools/34.0.0"
[[ -x "$BT/apksigner" && -x "$BT/zipalign" ]] || { echo 'Real Android signing tools required' >&2; exit 2; }
umask 077
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
printf '%s' "$INFINITY_KEYSTORE_B64" | base64 --decode > "$TMP/owner.keystore"
keytool -exportcert -keystore "$TMP/owner.keystore" -storepass:env INFINITY_STORE_PASSWORD \
  -alias "$INFINITY_KEY_ALIAS" -file "$TMP/certificate.der" >/dev/null 2>&1
ACTUAL=$(sha256sum "$TMP/certificate.der" | cut -d' ' -f1)
[[ "$ACTUAL" == "$EXPECTED" ]] || { echo 'BLOCKED: supplied signing identity does not match the pinned certificate.' >&2; exit 3; }
"$BT/zipalign" -p -f 4 "$INPUT" "$TMP/aligned.apk"
"$BT/apksigner" sign --ks "$TMP/owner.keystore" --ks-key-alias "$INFINITY_KEY_ALIAS" \
  --ks-pass env:INFINITY_STORE_PASSWORD --key-pass env:INFINITY_KEY_PASSWORD \
  --v1-signing-enabled true --v2-signing-enabled true --v3-signing-enabled true \
  --out "$TMP/signed.apk" "$TMP/aligned.apk"
"$BT/apksigner" verify --verbose --print-certs "$TMP/signed.apk" > "$TMP/verification.txt"
grep -Fq "Signer #1 certificate SHA-256 digest: $EXPECTED" "$TMP/verification.txt"
"$BT/zipalign" -c -p 4 "$TMP/signed.apk"
# No signed output is published before both verifiers pass.
cp "$TMP/signed.apk" "$OUTPUT"
cp "$TMP/verification.txt" "${OUTPUT%.apk}.signing.txt"
printf '\nSigning mode: retained-owner-key\nDevice acceptance: pending\n' >> "${OUTPUT%.apk}.signing.txt"
sha256sum "$OUTPUT" > "${OUTPUT%.apk}.sha256"
