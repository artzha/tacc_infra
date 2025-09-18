#!/usr/bin/env bash
# Usage:
#   ./vscode-remote-bootstrap.sh user@host [user@host2 ...]
# Options:
#   ENV: VSCODE_AGENT_FOLDER (default ~/.vscode-server)
#   Flags: --commit <hash>   (override)
#          --channel <stable|insider> (override)
#          --agent-dir <remote/path>  (override)

set -euo pipefail

AGENT_DIR_DEFAULT="${VSCODE_AGENT_FOLDER:-$HOME/.vscode-server}"
OVERRIDE_COMMIT=""
OVERRIDE_CHANNEL=""
OVERRIDE_AGENT_DIR=""
HOSTS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --commit)   OVERRIDE_COMMIT="$2"; shift 2;;
    --channel)  OVERRIDE_CHANNEL="$2"; shift 2;;
    --agent-dir)OVERRIDE_AGENT_DIR="$2"; shift 2;;
    -h|--help)
      sed -n '2,99p' "$0"; exit 0;;
    *)
      HOSTS+=("$1"); shift;;
  esac
done

if [[ ${#HOSTS[@]} -eq 0 ]]; then
  echo "ERROR: provide at least one SSH host (e.g., user@host)"
  exit 1
fi

# ---- Determine local VS Code commit & channel (works for Stable/Insiders/OSS) ----
if [[ -z "$OVERRIDE_COMMIT" ]]; then
  if ! command -v code >/dev/null 2>&1; then
    echo "ERROR: 'code' CLI not found. Install VS Code and enable 'Shell Command: Install 'code' command'."
    exit 1
  fi
  LOCAL_COMMIT="$(code --version | sed -n '2p')"
else
  LOCAL_COMMIT="$OVERRIDE_COMMIT"
fi

if [[ -z "$OVERRIDE_CHANNEL" ]]; then
  FIRST_LINE="$(code --version | sed -n '1p' || true)"
  if echo "$FIRST_LINE" | grep -qi "insider"; then
    CHANNEL="insider"
  else
    CHANNEL="stable"
  fi
else
  CHANNEL="$OVERRIDE_CHANNEL"
fi

echo "Local VS Code:"
echo "  Commit : $LOCAL_COMMIT"
echo "  Channel: $CHANNEL"

# ---- For each host: detect arch, install if missing ----
for HOST in "${HOSTS[@]}"; do
  echo "==> Bootstrapping $HOST ..."
  # Remote arch
  REMOTE_ARCH="$(ssh -o BatchMode=yes -o ConnectTimeout=10 "$HOST" 'uname -m' 2>/dev/null || true)"
  if [[ -z "$REMOTE_ARCH" ]]; then
    echo "  ERROR: Could not SSH into $HOST"; continue
  fi
  case "$REMOTE_ARCH" in
    x86_64|amd64) SERVER_FLAVOR="server-linux-x64";;
    aarch64|arm64) SERVER_FLAVOR="server-linux-arm64";;
    *)
      echo "  ERROR: Unsupported remote arch: $REMOTE_ARCH"; continue;;
  esac

  # Agent dir
  REMOTE_AGENT_DIR="${OVERRIDE_AGENT_DIR:-$AGENT_DIR_DEFAULT}"

  # Check if present
  if ssh "$HOST" "test -d '$REMOTE_AGENT_DIR/bin/$LOCAL_COMMIT'"; then
    echo "  Already present: $REMOTE_AGENT_DIR/bin/$LOCAL_COMMIT (skipping)"
    continue
  fi

  # Ensure dir exists and enough space (best effort)
  ssh "$HOST" "mkdir -p '$REMOTE_AGENT_DIR/bin'"

  # Build URL
  SERVER_URL="https://update.code.visualstudio.com/commit:${LOCAL_COMMIT}/${SERVER_FLAVOR}/${CHANNEL}"
  echo "  Fetching: $SERVER_URL"
  echo "  Target  : $REMOTE_AGENT_DIR/bin/$LOCAL_COMMIT"

  # Download + extract on remote with retries, low memory footprint
  ssh "$HOST" bash -s <<EOF
set -euo pipefail
TMPDIR="\${TMPDIR:-/tmp}"
DOWNLOAD="\$TMPDIR/vscode-server-\$RANDOM.tar.gz"
curl -fsSL --retry 3 --retry-delay 2 "$SERVER_URL" -o "\$DOWNLOAD"
mkdir -p "$REMOTE_AGENT_DIR/bin/$LOCAL_COMMIT"
tar -xzf "\$DOWNLOAD" -C "$REMOTE_AGENT_DIR/bin/$LOCAL_COMMIT" --strip-components=1
rm -f "\$DOWNLOAD"
# Ensure node binaries are executable
if command -v find >/dev/null 2>&1; then
  find "$REMOTE_AGENT_DIR/bin/$LOCAL_COMMIT" -type f -name node -exec chmod +x {} +
else
  chmod +x "$REMOTE_AGENT_DIR/bin/$LOCAL_COMMIT/node" || true
fi
# Persist agent dir for future sessions
PROFILE="\$HOME/.bashrc"
if ! grep -q 'VSCODE_AGENT_FOLDER' "\$PROFILE"; then
  echo 'export VSCODE_AGENT_FOLDER="$REMOTE_AGENT_DIR"' >> "\$PROFILE"
fi
EOF

  echo "  Installed VS Code Server for commit $LOCAL_COMMIT on $HOST"
done

echo "Done. You can now Remote-SSH into these hosts without the WASM download path."
