#!/usr/bin/env python3
"""Static validation for the Docker project; it never downloads model files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
IMAGE_VERSION = "0.1.7"
IMAGE_AMD64_DIGEST = "9389a4d09a5c08c3b78cf1f8272c3623aeb4b10a3ec2706063f78ab9ce35a66a"
CONTROLNET_EXTENSION_COMMIT = "56cec5b2958edf3b1807b7e7b2b1b5186dbd2f81"
MEDIAPIPE_VERSION = "0.10.21"
NUMPY_VERSION = "1.26.2"
PROTOBUF_VERSION = "4.25.3"
REQUIRED_CONTROLNET_WEIGHTS = {
    "control_v11e_sd15_ip2p_fp16.safetensors",
    "control_v11e_sd15_shuffle_fp16.safetensors",
    "control_v11f1e_sd15_tile_fp16.safetensors",
    "control_v11f1p_sd15_depth_fp16.safetensors",
    "control_v11p_sd15_canny_fp16.safetensors",
    "control_v11p_sd15_inpaint_fp16.safetensors",
    "control_v11p_sd15_lineart_fp16.safetensors",
    "control_v11p_sd15_mlsd_fp16.safetensors",
    "control_v11p_sd15_normalbae_fp16.safetensors",
    "control_v11p_sd15_openpose_fp16.safetensors",
    "control_v11p_sd15_scribble_fp16.safetensors",
    "control_v11p_sd15_seg_fp16.safetensors",
    "control_v11p_sd15_softedge_fp16.safetensors",
    "control_v11p_sd15s2_lineart_anime_fp16.safetensors",
    "control_v1p_sd15_qrcode_monster.safetensors",
    "controlnet++_canny_sd15_fp16.safetensors",
    "controlnet++_depth_sd15_fp16.safetensors",
    "controlnet++_hed_softedge_sd15_fp16.safetensors",
    "controlnet++_lineart_sd15_fp16.safetensors",
    "controlnet++_seg_sd15_fp16.safetensors",
    "ip-adapter-plus-face_sd15.pth",
    "ip-adapter-plus_sd15.pth",
    "ip-adapter_sd15.pth",
}


def load(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def validate_assets() -> tuple[int, int]:
    manifest = load("manifests/assets.json")
    assert manifest["schema_version"] == 1
    ids: set[str] = set()
    destinations: set[str] = set()
    total_bytes = 0
    for asset in manifest["assets"]:
        assert asset["id"] not in ids, f"duplicate asset id: {asset['id']}"
        assert asset["destination"] not in destinations, (
            f"duplicate asset destination: {asset['destination']}"
        )
        ids.add(asset["id"])
        destinations.add(asset["destination"])
        parsed = urlparse(asset["url"])
        assert parsed.scheme == "https" and parsed.netloc, asset["url"]
        assert asset["profiles"], asset["id"]
        assert set(asset["profiles"]) <= {"lite", "colab"}, asset["id"]
        destination = Path(asset["destination"])
        assert not destination.is_absolute() and ".." not in destination.parts
        if asset.get("sha256"):
            assert SHA256_RE.fullmatch(asset["sha256"]), asset["id"]
        if asset.get("size"):
            assert asset["size"] > 0, asset["id"]
            total_bytes += asset["size"]
    controlnet_weights = {
        Path(destination).name
        for destination in destinations
        if destination.startswith("models/ControlNet/")
        and Path(destination).suffix in {".safetensors", ".pth"}
    }
    assert REQUIRED_CONTROLNET_WEIGHTS <= controlnet_weights
    assert (
        "models/ControlNet-Preprocessors/clip_vision/clip_h.safetensors"
        in destinations
    )
    return len(ids), total_bytes


def validate_extensions() -> int:
    manifest = load("manifests/extensions.lock.json")
    assert manifest["schema_version"] == 1
    names: set[str] = set()
    by_name = {extension["name"]: extension for extension in manifest["extensions"]}
    for extension in manifest["extensions"]:
        assert extension["name"] not in names, extension["name"]
        names.add(extension["name"])
        assert extension["repository"].startswith("https://")
        assert COMMIT_RE.fullmatch(extension["commit"]), extension["name"]
        if not extension["default"]:
            assert extension.get("enable_env"), extension["name"]
    assert by_name["sd-webui-controlnet"]["commit"] == CONTROLNET_EXTENSION_COMMIT
    return len(names)


def validate_dockerfile() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04" in dockerfile
    assert "A1111_COMMIT=82a973c04367123ae98bd9abdf80d9eda9b910e2" in dockerfile
    assert "EXPOSE 7860" in dockerfile
    assert "ENTRYPOINT" in dockerfile
    assert "pip==24.0" in dockerfile
    assert "setuptools==69.5.1" in dockerfile
    assert "STABLE_DIFFUSION_REPO=https://github.com/w-e-w/stablediffusion.git" in dockerfile
    assert "STABLE_DIFFUSION_COMMIT_HASH=cf1d67a6fd5ea1aa600c4df58e5b47da45f6bdbf" in dockerfile
    assert "patch_controlnet_clipvision.py" in dockerfile
    assert f"ARG MEDIAPIPE_VERSION={MEDIAPIPE_VERSION}" in dockerfile
    assert f"ARG NUMPY_VERSION={NUMPY_VERSION}" in dockerfile
    assert f"ARG PROTOBUF_VERSION={PROTOBUF_VERSION}" in dockerfile
    assert '"mediapipe==${MEDIAPIPE_VERSION}"' in dockerfile
    assert '"numpy==${NUMPY_VERSION}"' in dockerfile
    assert '"protobuf==${PROTOBUF_VERSION}"' in dockerfile
    assert '"s/protobuf==3.20.0/protobuf==${PROTOBUF_VERSION}/"' in dockerfile
    assert ":latest" not in dockerfile


def validate_runpod_templates() -> int:
    expected_image = (
        "ghcr.io/trin-zenityx/zenityx-a1111-runpod:"
        f"{IMAGE_VERSION}@sha256:{IMAGE_AMD64_DIGEST}"
    )
    expected = {
        "runpod/template-lite.json": ("lite", 30),
        "runpod/template-colab.json": ("colab", 50),
    }
    for relative, (profile, volume_size) in expected.items():
        template = load(relative)
        assert template["category"] == "NVIDIA", relative
        assert template["containerDiskInGb"] == 40, relative
        assert template["volumeInGb"] == volume_size, relative
        assert template["volumeMountPath"] == "/workspace", relative
        assert template["ports"] == ["7860/http"], relative
        assert template["env"]["ZENITYX_PROFILE"] == profile, relative
        assert template["env"]["WEBUI_AUTH"] == "0", relative
        assert template["env"]["ENABLE_API"] == "0", relative
        assert "WEBUI_USERNAME" not in template["env"], relative
        assert "WEBUI_PASSWORD" not in template["env"], relative
        assert template["imageName"] == expected_image, relative
        assert template["isPublic"] is True, relative
        assert template["isServerless"] is False, relative
        assert "docs/RUNPOD-TH.md" in template["readme"], relative
    return len(expected)


def validate_runtime_overrides() -> None:
    overrides = load("config/runtime-overrides.json")
    assert overrides["control_net_models_path"] == "${WORKSPACE}/models/ControlNet"
    assert overrides["control_net_modules_path"] == (
        "${WORKSPACE}/models/ControlNet-Preprocessors"
    )


def main() -> None:
    asset_count, total_bytes = validate_assets()
    extension_count = validate_extensions()
    validate_dockerfile()
    validate_runtime_overrides()
    template_count = validate_runpod_templates()
    print(
        f"validated {asset_count} assets ({total_bytes / 1024**3:.1f} GiB declared), "
        f"{extension_count} pinned extensions, {template_count} public RunPod templates, "
        "and Dockerfile invariants"
    )


if __name__ == "__main__":
    main()
