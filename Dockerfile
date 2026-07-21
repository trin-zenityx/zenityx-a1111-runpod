FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

ARG A1111_COMMIT=82a973c04367123ae98bd9abdf80d9eda9b910e2

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    VENV_DIR=- \
    PORT=7860 \
    WORKSPACE_ROOT=/workspace \
    ZENITYX_PROFILE=colab \
    ZENITYX_CONFIG_PRESET=sd15-v2 \
    STABLE_DIFFUSION_REPO=https://github.com/w-e-w/stablediffusion.git \
    STABLE_DIFFUSION_COMMIT_HASH=cf1d67a6fd5ea1aa600c4df58e5b47da45f6bdbf

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        aria2 \
        build-essential \
        ca-certificates \
        curl \
        ffmpeg \
        git \
        jq \
        libcairo2-dev \
        libgl1 \
        libglib2.0-0 \
        libgoogle-perftools4 \
        libsm6 \
        libtcmalloc-minimal4 \
        libxext6 \
        libxrender1 \
        pkg-config \
        python3 \
        python3-dev \
        python3-pip \
        python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

RUN python -m pip install \
        pip==24.0 \
        setuptools==69.5.1 \
        wheel==0.43.0 \
    && python -m pip install \
        torch==2.6.0+cu124 \
        torchvision==0.21.0+cu124 \
        torchaudio==2.6.0+cu124 \
        --index-url https://download.pytorch.org/whl/cu124 \
    && python -m pip install xformers==0.0.29.post3 gdown==5.2.0

RUN git clone --filter=blob:none https://github.com/AUTOMATIC1111/stable-diffusion-webui.git /opt/stable-diffusion-webui \
    && git -C /opt/stable-diffusion-webui checkout --detach "${A1111_COMMIT}" \
    && git -C /opt/stable-diffusion-webui remote remove origin

RUN mkdir -p /opt/zenityx/manifests /opt/zenityx/scripts
COPY manifests/extensions.lock.json /opt/zenityx/manifests/extensions.lock.json
COPY scripts/install_extensions.py /opt/zenityx/scripts/install_extensions.py
COPY scripts/patch_controlnet_clipvision.py /opt/zenityx/scripts/patch_controlnet_clipvision.py

RUN python /opt/zenityx/scripts/install_extensions.py \
        --manifest /opt/zenityx/manifests/extensions.lock.json \
        --destination /opt/stable-diffusion-webui/extensions \
        --defaults \
    && python /opt/zenityx/scripts/patch_controlnet_clipvision.py \
        --target /opt/stable-diffusion-webui/extensions/sd-webui-controlnet/annotator/clipvision/__init__.py \
    && cd /opt/stable-diffusion-webui \
    && python launch.py --skip-torch-cuda-test --xformers --exit

COPY manifests/assets.json /opt/zenityx/manifests/assets.json
COPY config/runtime-overrides.json /opt/zenityx/config/runtime-overrides.json
COPY scripts/bootstrap_workspace.py /opt/zenityx/scripts/bootstrap_workspace.py
COPY docker/entrypoint.sh /opt/zenityx/entrypoint.sh

RUN chmod +x /opt/zenityx/entrypoint.sh \
    && mkdir -p /workspace

WORKDIR /opt/stable-diffusion-webui
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=30m --retries=5 \
    CMD curl --fail --silent --show-error --user "$(head -n 1 /workspace/config/gradio-auth.txt 2>/dev/null || true)" "http://127.0.0.1:${PORT}/" >/dev/null || exit 1

ENTRYPOINT ["/opt/zenityx/entrypoint.sh"]
