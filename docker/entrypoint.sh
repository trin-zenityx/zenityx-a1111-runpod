#!/usr/bin/env bash
set -Eeuo pipefail

WORKSPACE_ROOT="${WORKSPACE_ROOT:-/workspace}"
DATA_DIR="${DATA_DIR:-${WORKSPACE_ROOT}/a1111}"
MODELS_DIR="${MODELS_DIR:-${WORKSPACE_ROOT}/models}"
EMBEDDINGS_DIR="${EMBEDDINGS_DIR:-${WORKSPACE_ROOT}/embeddings}"
PORT="${PORT:-7860}"

export WORKSPACE_ROOT DATA_DIR MODELS_DIR EMBEDDINGS_DIR PORT
export HF_HOME="${HF_HOME:-${WORKSPACE_ROOT}/.cache/huggingface}"
export TORCH_HOME="${TORCH_HOME:-${WORKSPACE_ROOT}/.cache/torch}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-${WORKSPACE_ROOT}/.cache}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-${WORKSPACE_ROOT}/.cache/matplotlib}"
export MPLBACKEND=agg

if [[ -r /usr/lib/x86_64-linux-gnu/libtcmalloc_minimal.so.4 ]]; then
  export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libtcmalloc_minimal.so.4
fi

python /opt/zenityx/scripts/bootstrap_workspace.py \
  --workspace "${WORKSPACE_ROOT}" \
  --profile "${ZENITYX_PROFILE:-colab}" \
  --preset "${ZENITYX_CONFIG_PRESET:-sd15-v2}"

args=(
  --listen
  --port "${PORT}"
  --theme "${WEBUI_THEME:-dark}"
  --data-dir "${DATA_DIR}"
  --models-dir "${MODELS_DIR}"
  --embeddings-dir "${EMBEDDINGS_DIR}"
  --no-download-sd-model
  --xformers
)

if [[ "${ENABLE_API:-1}" == "1" ]]; then
  args+=(--api)
fi

auth_file="${WORKSPACE_ROOT}/config/gradio-auth.txt"
if [[ "${WEBUI_AUTH:-1}" == "1" ]]; then
  if [[ ! -s "${auth_file}" ]]; then
    echo "[zenityx] authentication file is missing: ${auth_file}" >&2
    exit 1
  fi
  auth_value="$(head -n 1 "${auth_file}")"
  args+=(--gradio-auth-path "${auth_file}")
  if [[ "${ENABLE_API:-1}" == "1" ]]; then
    args+=(--api-auth "${auth_value}")
  fi
  echo "[zenityx] WebUI login: ${auth_value}"
else
  echo "[zenityx] WARNING: WebUI authentication is disabled; the RunPod proxy URL is public."
fi

if [[ -n "${WEBUI_EXTRA_ARGS:-}" ]]; then
  read -r -a extra_args <<<"${WEBUI_EXTRA_ARGS}"
  args+=("${extra_args[@]}")
fi

echo "[zenityx] Starting A1111 on port ${PORT}"
exec python /opt/stable-diffusion-webui/launch.py "${args[@]}"

