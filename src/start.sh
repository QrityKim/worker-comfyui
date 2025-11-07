#!/usr/bin/env bash
set -e # 명령어 실행 중 에러가 발생하면 스크립트를 즉시 중단 (디버깅에 필수)

echo "--- STARTING CONTAINER ---"

echo "Starting model sync from R2 using Boto3..."
python -u /sync_r2.py
echo "Model sync script finished."

# Use libtcmalloc for better memory management
TCMALLOC="$(ldconfig -p | grep -Po "libtcmalloc.so.\d" | head -n 1)"
export LD_PRELOAD="${TCMALLOC}"

# Ensure ComfyUI-Manager runs in offline network mode inside the container
# (set -e 때문에 에러 발생 시 컨테이너가 죽는 것을 방지하기 위해 || true 추가)
comfy-manager-set-mode offline || echo "worker-comfyui - Could not set ComfyUI-Manager network_mode" >&2 || true

echo "worker-comfyui: Starting ComfyUI"

# Allow operators to tweak verbosity; default is DEBUG.
: "${COMFY_LOG_LEVEL:=DEBUG}"

# Serve the API and don't shutdown the container
if [ "$SERVE_API_LOCALLY" == "true" ]; then
    # 경로가 /comfyui/main.py 인지 다시 한 번 확인하세요. (Dockerfile 기준으로는 맞습니다)
    python -u /comfyui/main.py --disable-auto-launch --disable-metadata --listen --verbose "${COMFY_LOG_LEVEL}" --log-stdout &

    echo "worker-comfyui: Starting RunPod Handler"
    python -u /handler.py --rp_serve_api --rp_api_host=0.0.0.0
else
    python -u /comfyui/main.py --disable-auto-launch --disable-metadata --verbose "${COMFY_LOG_LEVEL}" --log-stdout &

    echo "worker-comfyui: Starting RunPod Handler"
    python -u /handler.py
fi
