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
    return len(ids), total_bytes


def validate_extensions() -> int:
    manifest = load("manifests/extensions.lock.json")
    assert manifest["schema_version"] == 1
    names: set[str] = set()
    for extension in manifest["extensions"]:
        assert extension["name"] not in names, extension["name"]
        names.add(extension["name"])
        assert extension["repository"].startswith("https://")
        assert COMMIT_RE.fullmatch(extension["commit"]), extension["name"]
        if not extension["default"]:
            assert extension.get("enable_env"), extension["name"]
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
    assert ":latest" not in dockerfile


def validate_runpod_templates() -> int:
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
        assert template["env"]["WEBUI_AUTH"] == "1", relative
        assert template["env"]["ENABLE_API"] == "0", relative
        assert "WEBUI_PASSWORD" not in template["env"], relative
        assert template["imageName"].endswith(":0.1.2"), relative
        assert template["isPublic"] is False, relative
        assert template["isServerless"] is False, relative
    return len(expected)


def main() -> None:
    asset_count, total_bytes = validate_assets()
    extension_count = validate_extensions()
    validate_dockerfile()
    template_count = validate_runpod_templates()
    print(
        f"validated {asset_count} assets ({total_bytes / 1024**3:.1f} GiB declared), "
        f"{extension_count} pinned extensions, {template_count} private RunPod templates, "
        "and Dockerfile invariants"
    )


if __name__ == "__main__":
    main()
