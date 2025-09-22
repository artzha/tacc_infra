#!/usr/bin/env bash
# Build a local Docker image (with defaults), then optionally push to Docker Hub.
# Defaults:
#   DOCKERFILE = docker/Dockerfile
#   IMAGE      = yourname/yourimage:latest
#   CONTEXT    = .
#
# Usage:
#   ./build_and_maybe_push.sh                # uses all defaults
#   ./build_and_maybe_push.sh youruser/myimg:dev
#   ./build_and_maybe_push.sh youruser/myimg:dev --context subdir
#   ./build_and_maybe_push.sh --no-cache
#
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker is not installed or not on PATH." >&2
  exit 1
fi

# Defaults
DOCKERFILE="docker/Dockerfile"
IMAGE="artzha/tacc_infra_ros:latest"
CONTEXT="."
NO_CACHE=""

# Optional first positional can override IMAGE if it doesn't look like a flag
if [[ $# -gt 0 && "$1" != --* ]]; then
  IMAGE="$1"; shift
fi

# Parse optional flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    --file)    DOCKERFILE="${2:-$DOCKERFILE}"; shift 2;;
    --context) CONTEXT="${2:-$CONTEXT}"; shift 2;;
    --no-cache) NO_CACHE="--no-cache"; shift;;
    -h|--help)
      sed -n '1,120p' "$0"; exit 0;;
    *)
      echo "Unknown argument: $1" >&2; exit 1;;
  esac
done

if [[ ! -f "$DOCKERFILE" ]]; then
  echo "ERROR: Dockerfile not found at '$DOCKERFILE'." >&2
  exit 1
fi

echo "==> Building image"
echo "    Image     : $IMAGE"
echo "    Dockerfile: $DOCKERFILE"
echo "    Context   : $CONTEXT"
echo

docker build $NO_CACHE -f "$DOCKERFILE" -t "$IMAGE" "$CONTEXT"

echo
echo "✅ Build complete: $IMAGE"
echo
read -r -p "Push to Docker Hub? [y/N]: " ANSWER

case "${ANSWER:-N}" in
  y|Y|yes|YES)
    # Best-effort login check (won’t prompt if already logged in)
    if ! docker system info 2>/dev/null | grep -q "^ Username:"; then
      echo "Not logged in to Docker Hub. Running 'docker login'…"
      docker login
    fi
    echo "==> Pushing $IMAGE"
    docker push "$IMAGE"
    echo "🚀 Pushed: $IMAGE"
    ;;
  *)
    echo "Skipping push."
    ;;
esac
