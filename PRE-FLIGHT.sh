#!/usr/bin/env bash
# --- Preflight (safe to run before bootstrap_mvp.sh) ---
set -e
OS=$(uname -s || true)
have(){ command -v "$1" >/dev/null 2>&1; }
pm=""; if [[ "$OS" == "Darwin" ]]; then have brew || echo "Install Homebrew: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)""; pm="brew"; elif have apt; then pm="apt"; fi
need_install=()
for bin in bash python3; do have "$bin" || need_install+=("$bin"); done
read -p "Target cloud? (gcp/aws) [gcp]: " CLOUD; CLOUD=${CLOUD:-gcp}
if [[ "$CLOUD" == "gcp" ]]; then
  have gcloud || need_install+=("gcloud")
  echo "Auth check:"; gcloud auth list 2>/dev/null || true
  echo "If empty: gcloud auth login && gcloud auth application-default login"
else
  have aws || need_install+=("aws")
  echo "Auth check:"; aws sts get-caller-identity 2>/dev/null || echo "(not authenticated)"
  echo "If not authenticated: aws configure"
fi
if [[ ${#need_install[@]} -gt 0 ]]; then
  echo "Missing tools: ${need_install[*]}"
fi
have docker || echo "Docker not found (optional). Install: https://docs.docker.com/get-docker/"
echo "--- Preflight complete ---"
