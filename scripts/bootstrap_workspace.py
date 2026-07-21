#!/usr/bin/env python3
"""Prepare a persistent RunPod workspace for the ZenityX A1111 image."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ASSET_MANIFEST = Path(
    os.environ.get("ASSET_MANIFEST", "/opt/zenityx/manifests/assets.json")
)
EXTENSION_MANIFEST = Path(
    os.environ.get("EXTENSION_MANIFEST", "/opt/zenityx/manifests/extensions.lock.json")
)
OVERRIDES_FILE = Path(
    os.environ.get("OVERRIDES_FILE", "/opt/zenityx/config/runtime-overrides.json")
)
IMAGE_EXTENSIONS = Path(
    os.environ.get("IMAGE_EXTENSIONS", "/opt/stable-diffusion-webui/extensions")
)
OPTIONAL_INSTALLER = Path(
    os.environ.get("OPTIONAL_INSTALLER", "/opt/zenityx/scripts/install_extensions.py")
)
SUPPORTED_PROFILES = {"lite", "colab"}
SUPPORTED_PRESETS = {"sd15-v2", "sd15-v2-thai", "sd15-legacy", "sdxl", "default"}


def log(message: str) -> None:
    print(f"[zenityx] {message}", flush=True)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write(path: Path, content: str, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(content, encoding="utf-8")
    if mode is not None:
        temporary.chmod(mode)
    temporary.replace(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verification_path(path: Path) -> Path:
    return path.with_name(path.name + ".verified.json")


def record_verification(path: Path, asset: dict[str, Any]) -> None:
    expected_hash = asset.get("sha256")
    if not expected_hash:
        return
    stat = path.stat()
    record = {
        "sha256": expected_hash,
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }
    atomic_write(verification_path(path), json.dumps(record, sort_keys=True) + "\n")


def valid_asset(
    path: Path, asset: dict[str, Any], *, record: bool = True
) -> bool:
    if not path.is_file():
        return False
    expected_size = asset.get("size")
    if expected_size and path.stat().st_size != expected_size:
        return False
    expected_hash = asset.get("sha256")
    if not expected_hash:
        return True

    marker = verification_path(path)
    if marker.is_file():
        try:
            saved = read_json(marker)
            stat = path.stat()
            if (
                saved.get("sha256") == expected_hash
                and saved.get("size") == stat.st_size
                and saved.get("mtime_ns") == stat.st_mtime_ns
            ):
                return True
        except (OSError, ValueError, json.JSONDecodeError):
            pass

    matches = sha256(path) == expected_hash
    if matches and record:
        record_verification(path, asset)
    return matches


def asset_destination(workspace: Path, relative: str) -> Path:
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"Unsafe asset destination: {relative}")
    destination = (workspace / relative_path).resolve()
    if workspace.resolve() not in destination.parents:
        raise ValueError(f"Asset escapes workspace: {relative}")
    return destination


def aria2_download(url: str, destination: Path) -> Path:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"Only HTTPS downloads are accepted: {url}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    command = [
        "aria2c",
        "--console-log-level=warn",
        "--summary-interval=10",
        "--continue=true",
        "--max-connection-per-server=8",
        "--split=8",
        "--min-split-size=1M",
        "--file-allocation=none",
        "--dir",
        str(destination.parent),
        "--out",
        partial.name,
    ]
    if parsed.hostname == "huggingface.co" and os.environ.get("HF_TOKEN"):
        command.extend(["--header", f"Authorization: Bearer {os.environ['HF_TOKEN']}"])
    command.append(url)
    subprocess.run(command, check=True)
    return partial


def download_asset(workspace: Path, asset: dict[str, Any], dry_run: bool) -> None:
    destination = asset_destination(workspace, asset["destination"])
    if valid_asset(destination, asset):
        log(f"ready: {asset['id']}")
        return

    if dry_run:
        size_gb = asset.get("size", 0) / 1_000_000_000
        log(f"would download: {asset['id']} ({size_gb:.2f} GB) -> {destination}")
        return

    if destination.exists():
        backup = destination.with_name(
            f"{destination.name}.invalid-{int(time.time())}"
        )
        destination.replace(backup)
        log(f"moved invalid asset to {backup}")

    log(f"downloading: {asset['id']} -> {destination}")
    partial = aria2_download(asset["url"], destination)
    if not valid_asset(partial, asset, record=False):
        raise RuntimeError(f"Integrity check failed for {asset['id']}: {partial}")
    partial.replace(destination)
    record_verification(destination, asset)
    log(f"verified: {asset['id']}")


def ensure_capacity(workspace: Path, assets: list[dict[str, Any]]) -> None:
    required = 0
    for asset in assets:
        destination = asset_destination(workspace, asset["destination"])
        if not valid_asset(destination, asset):
            required += int(asset.get("size", 0))
    free = shutil.disk_usage(workspace).free
    reserve = 5 * 1024**3
    if required + reserve > free:
        raise RuntimeError(
            "Not enough workspace space: "
            f"need about {(required + reserve) / 1024**3:.1f} GiB, "
            f"have {free / 1024**3:.1f} GiB"
        )


def create_directories(workspace: Path) -> None:
    directories = [
        "a1111/extensions",
        "a1111/localizations",
        "config",
        "embeddings",
        "models/Stable-diffusion",
        "models/Lora",
        "models/VAE",
        "models/ControlNet",
        "models/ControlNet-Preprocessors",
        "models/ESRGAN",
        "outputs/text",
        "outputs/image",
        "outputs/extras",
        "outputs/grids",
        "outputs/save",
        "outputs/init-images",
        ".cache/huggingface",
        ".cache/torch",
        ".cache/matplotlib",
        ".zenityx/presets",
    ]
    for relative in directories:
        (workspace / relative).mkdir(parents=True, exist_ok=True)


def link_default_extensions(workspace: Path, dry_run: bool) -> None:
    data_extensions = workspace / "a1111/extensions"
    manifest = read_json(EXTENSION_MANIFEST)
    for extension in manifest["extensions"]:
        if not extension.get("default"):
            continue
        source = IMAGE_EXTENSIONS / extension["name"]
        target = data_extensions / extension["name"]
        if dry_run:
            log(f"would link extension: {extension['name']}")
            continue
        if target.is_symlink() and target.resolve() == source.resolve():
            continue
        if target.exists() or target.is_symlink():
            log(f"keeping user extension path: {target}")
            continue
        target.symlink_to(source, target_is_directory=True)


def install_optional_extensions(workspace: Path, dry_run: bool) -> None:
    command = [
        sys.executable,
        str(OPTIONAL_INSTALLER),
        "--manifest",
        str(EXTENSION_MANIFEST),
        "--destination",
        str(workspace / "a1111/extensions"),
        "--optional",
    ]
    if dry_run:
        command.append("--dry-run")
    subprocess.run(command, check=True)


def sync_small_assets(workspace: Path, dry_run: bool) -> None:
    if dry_run:
        return
    preset_root = workspace / ".zenityx/presets"
    localization = preset_root / "th_TH.json"
    if localization.is_file():
        shutil.copy2(localization, workspace / "a1111/localizations/th_TH.json")

    config_presets = preset_root / "Config-Presets"
    extension_target = IMAGE_EXTENSIONS / "Config-Presets"
    if config_presets.is_dir() and extension_target.is_dir():
        for source in config_presets.iterdir():
            if source.is_file():
                shutil.copy2(source, extension_target / source.name)


def substitute_workspace(value: Any, workspace: Path) -> Any:
    if isinstance(value, str):
        return value.replace("${WORKSPACE}", str(workspace))
    if isinstance(value, list):
        return [substitute_workspace(item, workspace) for item in value]
    if isinstance(value, dict):
        return {key: substitute_workspace(item, workspace) for key, item in value.items()}
    return value


def initialize_configuration(workspace: Path, preset: str, dry_run: bool) -> None:
    data_dir = workspace / "a1111"
    config_path = data_dir / "config.json"
    ui_path = data_dir / "ui-config.json"
    styles_path = data_dir / "styles.csv"
    force = os.environ.get("FORCE_PRESET", "0") == "1"
    preset_root = workspace / ".zenityx/presets"

    preset_files = {
        "sd15-v2": ("config-sd15-v2.json", "ui-config-sd15-v2.json"),
        "sd15-v2-thai": ("config-sd15-v2-thai.json", "ui-config-sd15-v2.json"),
        "sd15-legacy": ("config-sd15-legacy.json", "ui-config-sd15-legacy.json"),
        "sdxl": ("config-sdxl.json", "ui-config-sdxl.json"),
        "default": (None, None),
    }
    config_name, ui_name = preset_files[preset]

    if dry_run:
        log(f"would initialize preset: {preset} (force={force})")
        return

    if force or not config_path.exists():
        configuration: dict[str, Any] = {}
        if config_name:
            configuration = read_json(preset_root / config_name)
        overrides = substitute_workspace(read_json(OVERRIDES_FILE), workspace)
        configuration.update(overrides)
        if os.environ.get("UI_LANGUAGE"):
            configuration["localization"] = os.environ["UI_LANGUAGE"]
        elif preset == "sd15-v2-thai":
            configuration["localization"] = "th_TH"
        atomic_write(config_path, json.dumps(configuration, indent=2, ensure_ascii=False) + "\n")
        log(f"applied config preset: {preset}")
    else:
        log("keeping existing config.json")

    if (force or not ui_path.exists()) and ui_name:
        shutil.copy2(preset_root / ui_name, ui_path)
    if force or not styles_path.exists():
        shutil.copy2(preset_root / "styles.csv", styles_path)


def configure_authentication(workspace: Path, dry_run: bool) -> None:
    if os.environ.get("WEBUI_AUTH", "1") != "1":
        return
    auth_path = workspace / "config/gradio-auth.txt"
    username = os.environ.get("WEBUI_USERNAME", "zenityx")
    password = os.environ.get("WEBUI_PASSWORD")
    if any(character in username for character in ":,\n\r"):
        raise ValueError("WEBUI_USERNAME cannot contain ':', ',' or newlines")
    if password and any(character in password for character in ":,\n\r"):
        raise ValueError("WEBUI_PASSWORD cannot contain ':', ',' or newlines")

    if dry_run:
        log(f"would configure authentication for user: {username}")
        return

    if password:
        atomic_write(auth_path, f"{username}:{password}\n", 0o600)
    elif not auth_path.exists():
        generated = secrets.token_urlsafe(18)
        atomic_write(auth_path, f"{username}:{generated}\n", 0o600)
        log("generated a persistent WebUI password in /workspace/config/gradio-auth.txt")
    else:
        auth_path.chmod(0o600)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--profile", choices=sorted(SUPPORTED_PROFILES), required=True)
    parser.add_argument("--preset", choices=sorted(SUPPORTED_PRESETS), required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    if not os.access(workspace, os.W_OK):
        raise PermissionError(f"Workspace is not writable: {workspace}")

    create_directories(workspace)
    manifest = read_json(ASSET_MANIFEST)
    selected_assets = [
        asset for asset in manifest["assets"] if args.profile in asset["profiles"]
    ]
    if os.environ.get("SKIP_ASSET_DOWNLOADS", "0") == "1":
        selected_assets = [asset for asset in selected_assets if asset["kind"] == "preset"]
        log("SKIP_ASSET_DOWNLOADS=1: downloading configuration files only")

    if not args.dry_run:
        ensure_capacity(workspace, selected_assets)
    for asset in selected_assets:
        download_asset(workspace, asset, args.dry_run)

    link_default_extensions(workspace, args.dry_run)
    install_optional_extensions(workspace, args.dry_run)
    sync_small_assets(workspace, args.dry_run)
    initialize_configuration(workspace, args.preset, args.dry_run)
    configure_authentication(workspace, args.dry_run)
    log(f"workspace ready: profile={args.profile}, preset={args.preset}")


if __name__ == "__main__":
    main()
