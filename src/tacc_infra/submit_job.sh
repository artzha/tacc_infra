#!/usr/bin/env bash
# Interactive-only launcher for TACC (prefers `idev`, else `salloc` + `srun`).
# Slack: posts ⏳ when queued, ✅ when allocation starts.

set -euo pipefail

PARTITION=""
TIME_REQ="00:30:00"          # HH:MM:SS
ACCOUNT="${SLURM_ACCOUNT:-}" # or pass -A/--account
NODES=1
CPUS=1
MEM=""

# Slack config
SLACK_WEBHOOK="${SLACK_WEBHOOK_URL:-}"       # incoming webhook URL
SLACK_MENTION_ID="${SLACK_MENTION_ID:-}"     # e.g., U012ABCDEF (will post <@U012ABCDEF>)
SLACK_MENTION="${SLACK_MENTION:-}"           # "here" or "channel" → <!here> / <!channel>

die(){ echo "ERROR: $*" >&2; exit 1; }

list_partitions() {
  echo "== Available partitions (queues) =="
  if command -v sinfo >/dev/null 2>&1; then
    sinfo -s -o "%P %l %a %D %C"
  else
    echo "sinfo not found on PATH."
  fi
  cat <<'EOS'

Tip:
- Interactive on TACC (preferred):
    idev -m 30 -p <partition> -A <allocation>
EOS
}

usage() {
  cat <<EOF
Usage:
  taccenv submit_job --time HH:MM:SS --partition NAME -A ACCOUNT [options]

Required:
  --time HH:MM:SS        Wall time (default: ${TIME_REQ})
  --partition NAME       Queue/partition (e.g., normal, gpu-a100-small)
  -A, --account NAME     Allocation (or set SLURM_ACCOUNT)

Optional (fallback only): --nodes N  --cpus N  --mem SIZE
Slack:
  --slack-webhook URL          (or env SLACK_WEBHOOK_URL)
  --slack-mention-id USERID    Mention user by ID (e.g., U012ABCDEF)  (or env SLACK_MENTION_ID)
  --slack-mention here|channel Mention @here or @channel              (or env SLACK_MENTION=here|channel)

Other:
  --list | -h | --help
EOF
}

# ---- args ----
if [[ $# -eq 0 ]]; then usage; echo; list_partitions; exit 0; fi
while [[ $# -gt 0 ]]; do
  case "$1" in
    --time) TIME_REQ="$2"; shift 2;;
    --partition) PARTITION="$2"; shift 2;;
    -A|--account) ACCOUNT="$2"; shift 2;;
    --nodes) NODES="$2"; shift 2;;
    --cpus) CPUS="$2"; shift 2;;
    --mem) MEM="$2"; shift 2;;
    --slack-webhook) SLACK_WEBHOOK="$2"; shift 2;;
    --slack-mention-id) SLACK_MENTION_ID="$2"; shift 2;;
    --slack-mention) SLACK_MENTION="$2"; shift 2;;
    --list) list_partitions; exit 0;;
    -h|--help) usage; exit 0;;
    *) die "Unknown argument: $1";;
  esac
done

[[ -n "$PARTITION" ]] || die "--partition is required (use --list)"
[[ -n "$ACCOUNT"   ]] || die "--account/-A is required (or set SLURM_ACCOUNT)"

USER_NAME="${USER:-$(id -un)}"
HOSTNAME_SHORT="$(hostname 2>/dev/null || echo host)"

# ---- Slack helpers ----
_slack_prefix() {
  local pfx=""
  if [[ -n "$SLACK_MENTION_ID" ]]; then
    pfx="<@${SLACK_MENTION_ID}> "
  elif [[ "$SLACK_MENTION" == "here" ]]; then
    pfx="<!here> "
  elif [[ "$SLACK_MENTION" == "channel" ]]; then
    pfx="<!channel> "
  fi
  printf "%s" "$pfx"
}

slack_post() {
  local msg="${1:-}"
  [[ -n "$SLACK_WEBHOOK" && -n "$msg" ]] || return 0
  local pfx; pfx="$(_slack_prefix)"
  curl -s -X POST -H 'Content-type: application/json' \
    --data "{\"text\":\"${pfx}${msg}\"}" "$SLACK_WEBHOOK" >/dev/null || true
}

# ---- robust IDEV watcher (simpler, no nested reads) ----
# Anchors on submission time and picks the newest job (prefers names containing "idev").
idev_watch_until_running_by_time() {
  local mark_epoch="$1"      # epoch seconds (when we queued)
  local partition="$2"
  local cushion=60           # allow jobs submitted up to 60s before mark (clock skew)
  local deadline=$(( mark_epoch + 7200 ))  # stop after 2h

  # Find candidate jobid: most recent for this user/partition after mark; prefer names with "idev"
  local jobid=""
  while [[ -n "$partition" && -z "$jobid" && $(date +%s) -lt $deadline ]]; do
    jobid="$(
      squeue -u "$USER_NAME" -p "$partition" -h -o '%i|%j|%V' 2>/dev/null \
      | awk -F'|' -v mk=$((mark_epoch - cushion)) '
          function to_epoch(ts,   cmd, out) {
            gsub("T"," ", ts)
            cmd = "date -d \"" ts "\" +%s"
            cmd | getline out
            close(cmd)
            return (out ~ /^[0-9]+$/) ? out : 0
          }
          {
            ep = to_epoch($3)
            if (ep >= mk) {
              score = ep
              if (tolower($2) ~ /(^|[^a-z])idev([^a-z]|$)/) score += 1000000000
              printf "%012d|%s\n", score, $1
            }
          }
        ' \
      | sort -t'|' -k1,1nr \
      | head -n1 \
      | cut -d'|' -f2
    )"
    [[ -n "$jobid" ]] || sleep 5
  done
  [[ -n "$jobid" ]] || return 0  # nothing found; exit quietly

  # Helper: TIME string -> seconds (supports D-HH:MM:SS, HH:MM:SS, MM:SS)
  time_to_seconds() {
    local t="$1" days=0 h=0 m=0 s=0
    [[ -z "$t" ]] && { echo 0; return; }
    if [[ "$t" == *-* ]]; then days="${t%%-*}"; t="${t#*-}"; fi
    IFS=: read -r h m s <<<"$t"
    h=${h:-0}; m=${m:-0}; s=${s:-0}; s="${s%%.*}"
    echo $((10#$days*86400 + 10#$h*3600 + 10#$m*60 + 10#$s))
  }

  # Poll TIME for this job via `squeue -u USER`, post when TIME > 0
  while true; do
    local time_str
    time_str="$(squeue -u "$USER_NAME" -h -o '%i|%M' 2>/dev/null | awk -F'|' -v id="$jobid" '$1==id{print $2}')"
    [[ -z "$time_str" ]] && break  # job not visible anymore
    local secs
    secs="$(time_to_seconds "$time_str")"
    if (( secs > 0 )); then
      slack_post ":white_check_mark: Interactive job *started* (job \`$jobid\`, queue \`${PARTITION}\`, user \`${USER_NAME}\`, TIME \`$time_str\`)."
      break
    fi
    sleep 5
  done
}

# ---- launch ----
if command -v idev >/dev/null 2>&1; then
  # Convert HH:MM:SS → minutes for idev
  IFS=: read -r HH MM SS <<<"${TIME_REQ}"
  MINUTES=$((10#$HH*60 + 10#$MM + (10#$SS > 0 ? 1 : 0)))  # round up if seconds present

  # ⏳ queued
  slack_post ":hourglass_flowing_sand: \`taccenv\` requested *interactive* on \`${HOSTNAME_SHORT}\` — queue \`${PARTITION}\`, time \`${TIME_REQ}\`, account \`${ACCOUNT}\` (user: \`${USER_NAME}\`)."

  # mark time, start watcher
  MARK_EPOCH="$(date +%s)"
  ( idev_watch_until_running_by_time "$MARK_EPOCH" "$PARTITION" ) >/dev/null 2>&1 & disown

  echo "Launching interactive via idev:"
  echo "  idev -m ${MINUTES} -p ${PARTITION} -A ${ACCOUNT}"
  exec idev -m "${MINUTES}" -p "${PARTITION}" -A "${ACCOUNT}"

else
  # salloc + srun fallback
  ALLOC_CMD=( salloc --time="${TIME_REQ}" -p "${PARTITION}" -A "${ACCOUNT}" --nodes "${NODES}" --cpus-per-task "${CPUS}" )
  [[ -n "${MEM}" ]] && ALLOC_CMD+=( --mem "${MEM}" )

  # ⏳ queued
  slack_post ":hourglass_flowing_sand: \`taccenv\` requesting *interactive* (salloc) on \`${HOSTNAME_SHORT}\` — queue \`${PARTITION}\`, time \`${TIME_REQ}\`, account \`${ACCOUNT}\` (user: \`${USER_NAME}\`)."

  echo "Allocating with: ${ALLOC_CMD[*]}"
  if "${ALLOC_CMD[@]}"; then
    # ✅ allocation granted
    slack_post ":white_check_mark: Interactive allocation *granted* (queue \`${PARTITION}\`, user \`${USER_NAME}\`)."
    exec srun --pty bash -l
  else
    slack_post ":x: Interactive allocation *failed* (queue \`${PARTITION}\`, user \`${USER_NAME}\`)."
    exit 1
  fi
fi
