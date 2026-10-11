#!/bin/bash
set -e

KERNEL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SIGN_TOOL="$KERNEL_DIR/scripts/sign-file"
KEY="$KERNEL_DIR/certs/yandex_whitelist.pem"
CERT="$KERNEL_DIR/certs/yandex_whitelist.x509"

if [ ! -f "$SIGN_TOOL" ]; then
    echo "Building sign-file tool..."
    gcc -o "$SIGN_TOOL" "$KERNEL_DIR/scripts/sign-file.c" -lcrypto
fi

if [ ! -f "$KEY" ] || [ ! -f "$CERT" ]; then
    echo "Error: Key or cert not found in $KERNEL_DIR/certs/"
    exit 1
fi

TARGET_DIR="${1:-/home/lmods/yandex_vendor/lib/modules}"

echo "=== Signing all modules in $TARGET_DIR ==="
count=0
for mod in $(find "$TARGET_DIR" -type f -name "*.ko"); do
    echo "Signing: $(basename "$mod")"
    "$SIGN_TOOL" sha256 "$KEY" "$CERT" "$mod"
    ((count++))
done

echo "=== Successfully signed $count modules with Yandex-Custom-ROM-Module-Whitelist cert ==="
