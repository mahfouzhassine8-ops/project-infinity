#!/usr/bin/env bash
# Disposable GitHub runner only. Same packages and Ubuntu signature validation;
# avoid its repeatedly DNS-failing azure.archive mirror-list endpoint.
set -euo pipefail
test "${GITHUB_ACTIONS:-}" = true
test "${GITHUB_REPOSITORY:-}" = mahfouzhassine8-ops/project-infinity
test "${GITHUB_REF:-}" = refs/heads/work/infinity-movies-continue-cast-2103486-20261112
test -f /usr/share/keyrings/ubuntu-archive-keyring.gpg
. /etc/os-release
test "$ID" = ubuntu
test "$VERSION_CODENAME" = jammy
case "${1:-native}" in
  native) infinity_ci_packages=(python3-yaml python3-dev libsqlite3-dev libssl-dev libffi-dev autoconf automake libtool pkg-config libcurl4-openssl-dev); infinity_ci_out=cast-native-output ;;
  emulator) infinity_ci_packages=(libpulse0); infinity_ci_out=cast-sdk ;;
  *) exit 2 ;;
esac
mkdir -p "$infinity_ci_out"
infinity_ci_sources="$PWD/$infinity_ci_out/official-ubuntu-sources.txt"
cat > "$infinity_ci_sources" <<'SOURCES'
deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] https://archive.ubuntu.com/ubuntu jammy main restricted universe multiverse
deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] https://archive.ubuntu.com/ubuntu jammy-updates main restricted universe multiverse
deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] https://security.ubuntu.com/ubuntu jammy-security main restricted universe multiverse
SOURCES
infinity_ci_apt=(-o "Dir::Etc::sourcelist=$infinity_ci_sources" -o Dir::Etc::sourceparts=- -o Acquire::Retries=1 -o Acquire::http::Timeout=20 -o Acquire::https::Timeout=20)
timeout 180 sudo apt-get "${infinity_ci_apt[@]}" -o APT::Update::Error-Mode=any update -qq
timeout 180 sudo apt-get "${infinity_ci_apt[@]}" install -y "${infinity_ci_packages[@]}"
