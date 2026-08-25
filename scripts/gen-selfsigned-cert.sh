#!/usr/bin/env bash
# Generate a self-signed TLS certificate for the demo deployment.
# Usage: scripts/gen-selfsigned-cert.sh [domain]   (default: blg-demo.local)
set -euo pipefail

DOMAIN="${1:-blg-demo.local}"
CERT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/deploy/certs"
mkdir -p "$CERT_DIR"

openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout "$CERT_DIR/key.pem" \
    -out "$CERT_DIR/cert.pem" \
    -days 825 \
    -subj "/CN=$DOMAIN" \
    -addext "subjectAltName=DNS:$DOMAIN"

echo "Wrote $CERT_DIR/cert.pem and $CERT_DIR/key.pem (CN=$DOMAIN, valid 825 days)"
