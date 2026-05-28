#!/usr/bin/env bash
# AI agent wrapper with multi-tier fallback.
#
# Modes:
#   plan      — Claude explores codebase and writes an implementation plan (read-only).
#               Falls back to kimi k2.6 via opencode if Claude is unavailable.
#               Writes plan text to --output-file if provided.
#               Ends output with "IMPLEMENTATION_MODEL: <slug>" for downstream use.
#   implement — OpenCode executes a plan (write tools, Claude skipped entirely).
#               Cascade: mimo-v2.5-free → deepseek-v4-flash-free → qwen3.6-plus
#               Accepts --model to override the primary model (use Claude's pick).
#   review    — Read-only review. Claude → glm-5.1.
#   fix       — Legacy combined mode. Claude → opencode cascade (unchanged behaviour).
#
# Usage:
#   ./ai-agent.sh "<task>" [--mode plan|implement|review|fix]
#                          [--max-turns N]
#                          [--output-file <path>]
#                          [--model <opencode-slug>]
#
# Required env: CLAUDE_CODE_OAUTH_TOKEN, OPENCODE_API_KEY
# MUST NOT BE SET: ANTHROPIC_API_KEY (overrides Pro OAuth and incurs PAYG charges)

set -euo pipefail

TASK="${1:?usage: ai-agent.sh \"<task>\" [--mode plan|implement|review|fix] [--max-turns N] [--output-file PATH] [--model SLUG]}"
MODE="fix"
MAX_TURNS="25"
OUTPUT_FILE=""
MODEL_OVERRIDE=""

shift
while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)        MODE="$2";          shift 2 ;;
    --max-turns)   MAX_TURNS="$2";     shift 2 ;;
    --output-file) OUTPUT_FILE="$2";   shift 2 ;;
    --model)       MODEL_OVERRIDE="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

# Safety: ANTHROPIC_API_KEY must NOT be set, or Claude Code switches to pay-per-token
if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "[ai-agent] FATAL: ANTHROPIC_API_KEY is set; this would override Pro subscription auth" >&2
  echo "[ai-agent] unset ANTHROPIC_API_KEY before continuing" >&2
  exit 3
fi

SKIP_CLAUDE=false

case "$MODE" in
  plan)
    # Read-only: Claude explores + plans; kimi k2.6 if Claude is at quota.
    ALLOWED_TOOLS="Read,Grep,Glob,Bash"
    OPENCODE_MODEL_PRIMARY="${MODEL_OVERRIDE:-${OPENCODE_MODEL_PLAN:-opencode-go/kimi-k2.6}}"
    OPENCODE_MODEL_SECONDARY="${OPENCODE_MODEL_PLAN_FALLBACK:-opencode-go/glm-5.1}"
    OPENCODE_MODEL_TERTIARY=""
    SKIP_CLAUDE=false
    ;;
  implement)
    # Write: opencode executes the plan. Claude is not used.
    ALLOWED_TOOLS="Read,Write,Edit,Grep,Glob,Bash"
    OPENCODE_MODEL_PRIMARY="${MODEL_OVERRIDE:-${OPENCODE_MODEL_IMPL:-opencode/mimo-v2.5-free}}"
    OPENCODE_MODEL_SECONDARY="${OPENCODE_MODEL_IMPL_SECONDARY:-opencode/deepseek-v4-flash-free}"
    OPENCODE_MODEL_TERTIARY="${OPENCODE_MODEL_IMPL_TERTIARY:-opencode-go/qwen3.6-plus}"
    SKIP_CLAUDE=true
    ;;
  review)
    ALLOWED_TOOLS="Read,Grep,Glob,Bash"
    OPENCODE_MODEL_PRIMARY="${OPENCODE_MODEL_REVIEW:-opencode-go/glm-5.1}"
    OPENCODE_MODEL_SECONDARY=""
    OPENCODE_MODEL_TERTIARY=""
    SKIP_CLAUDE=false
    ;;
  fix)
    # Legacy combined mode — Claude → opencode cascade (no behaviour change).
    ALLOWED_TOOLS="Read,Write,Edit,Grep,Glob,Bash"
    OPENCODE_MODEL_PRIMARY="${OPENCODE_MODEL_FIX_FREE:-opencode/deepseek-v4-flash-free}"
    OPENCODE_MODEL_SECONDARY="${OPENCODE_MODEL_FIX_GO:-opencode-go/qwen3.6-plus}"
    OPENCODE_MODEL_TERTIARY="${OPENCODE_MODEL_FIX_FALLBACK:-opencode-go/deepseek-v4-flash}"
    SKIP_CLAUDE=false
    ;;
  *)
    echo "[ai-agent] unknown mode: $MODE" >&2; exit 2 ;;
esac

# ---------------------------------------------------------------------------
# write_output — emit agent output to stdout and optionally to OUTPUT_FILE.
# Called only on success so the file is never written on partial output.
# ---------------------------------------------------------------------------
write_output() {
  local content="$1"
  if [[ -n "$OUTPUT_FILE" ]]; then
    printf '%s\n' "$content" > "$OUTPUT_FILE"
  fi
  printf '%s\n' "$content"
}

is_quota_or_overload_error() {
  echo "$1" | grep -qiE \
    'usage_limit|rate_limit|overloaded|insufficient_quota|429|529|billing|payment_required|reached your usage limit|quota|free.*limit|daily.*limit'
}

log() { echo "[ai-agent] $*" >&2; }

# ---------------------------------------------------------------------------
# try_claude_code
# Runs Claude Code. Stdout (plan/output) is captured cleanly; stderr goes to
# a temp file so quota-error detection works on both streams independently.
# ---------------------------------------------------------------------------
try_claude_code() {
  if [[ "$SKIP_CLAUDE" == "true" ]]; then
    log "skipping Claude (implement mode uses opencode only)"
    return 2
  fi
  if ! command -v claude >/dev/null 2>&1; then
    log "claude CLI not found, skipping tier 1"
    return 2
  fi
  if [[ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]]; then
    log "CLAUDE_CODE_OAUTH_TOKEN not set, skipping tier 1"
    return 2
  fi

  log "tier 1: Claude Code via Pro subscription (mode=$MODE)"
  local out exit_code stderr_tmp
  stderr_tmp=$(mktemp)
  set +e
  out=$(CLAUDE_CODE_OAUTH_TOKEN="$CLAUDE_CODE_OAUTH_TOKEN" \
        claude --print "$TASK" \
          --allowedTools "$ALLOWED_TOOLS" \
          --max-turns "$MAX_TURNS" \
          --output-format text \
          --dangerously-skip-permissions 2>"$stderr_tmp")
  exit_code=$?
  set -e

  if is_quota_or_overload_error "$out" || is_quota_or_overload_error "$(cat "$stderr_tmp")"; then
    log "claude code: quota/overload detected, falling through to tier 2"
    rm -f "$stderr_tmp"
    return 1
  fi
  if [[ $exit_code -ne 0 ]]; then
    log "claude code exited $exit_code, falling through"
    log "stderr tail: $(tail -5 "$stderr_tmp")"
    rm -f "$stderr_tmp"
    return 1
  fi

  rm -f "$stderr_tmp"
  write_output "$out"
  return 0
}

# ---------------------------------------------------------------------------
# try_opencode_model <model-slug>
# ---------------------------------------------------------------------------
try_opencode_model() {
  local model="$1"
  if ! command -v opencode >/dev/null 2>&1; then
    log "opencode CLI not found"
    return 2
  fi
  if [[ -z "${OPENCODE_API_KEY:-}" ]]; then
    log "OPENCODE_API_KEY not set, skipping opencode"
    return 2
  fi

  log "opencode: trying model $model (mode=$MODE)"
  local out exit_code stderr_tmp
  stderr_tmp=$(mktemp)
  set +e
  out=$(OPENCODE_API_KEY="$OPENCODE_API_KEY" \
        opencode run \
          --model "$model" \
          "$TASK" 2>"$stderr_tmp")
  exit_code=$?
  set -e

  if is_quota_or_overload_error "$out" || is_quota_or_overload_error "$(cat "$stderr_tmp")"; then
    log "opencode $model: quota/limit hit, trying next model"
    rm -f "$stderr_tmp"
    return 1
  fi
  if [[ $exit_code -ne 0 ]]; then
    log "opencode $model exited $exit_code, trying next model"
    log "stderr tail: $(tail -5 "$stderr_tmp")"
    rm -f "$stderr_tmp"
    return 1
  fi

  rm -f "$stderr_tmp"
  write_output "$out"
  return 0
}

# ---------------------------------------------------------------------------
# Tier cascade
# ---------------------------------------------------------------------------

# Tier 1: Claude Code (skipped automatically in implement mode)
if try_claude_code; then exit 0; fi

# Tier 2: OpenCode model cascade
if try_opencode_model "$OPENCODE_MODEL_PRIMARY"; then exit 0; fi
if [[ -n "${OPENCODE_MODEL_SECONDARY:-}" ]]; then
  if try_opencode_model "$OPENCODE_MODEL_SECONDARY"; then exit 0; fi
fi
if [[ -n "${OPENCODE_MODEL_TERTIARY:-}" ]]; then
  if try_opencode_model "$OPENCODE_MODEL_TERTIARY"; then exit 0; fi
fi

log "all tiers exhausted — manual intervention needed"
exit 1
