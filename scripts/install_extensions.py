#!/usr/bin/env python3
"""Install extension repositories at exact commits without tracking mutable branches."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path


COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def run(command: list[str]) -> None:
    print("[extensions]", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def is_enabled(extension: dict[str, object], defaults_only: bool) -> bool:
    if defaults_only:
        return bool(extension.get("default"))
    env_name = extension.get("enable_env")
    return bool(env_name and os.environ.get(str(env_name), "0") == "1")


def install(extension: dict[str, object], destination: Path, dry_run: bool) -> None:
    name = str(extension["name"])
    repository = str(extension["repository"])
    commit = str(extension["commit"])
    target = destination / name

    if not COMMIT_RE.fullmatch(commit):
        raise ValueError(f"Invalid commit for {name}: {commit}")
    if not repository.startswith("https://"):
        raise ValueError(f"Only HTTPS repositories are allowed: {repository}")

    if dry_run:
        print(f"[extensions] would install {name}@{commit}")
        return

    if target.is_symlink():
        print(f"[extensions] keeping image-provided symlink: {target}")
        return

    if (target / ".git").is_dir():
        current = subprocess.check_output(
            ["git", "-C", str(target), "rev-parse", "HEAD"], text=True
        ).strip()
        if current == commit:
            print(f"[extensions] already pinned: {name}@{commit}")
            return
        print(
            f"[extensions] keeping user-managed {name}@{current}; "
            f"set a clean workspace to restore {commit}"
        )
        return

    if target.exists():
        print(f"[extensions] keeping non-git user directory: {target}")
        return

    destination.mkdir(parents=True, exist_ok=True)
    target.mkdir(parents=True)
    try:
        run(["git", "-C", str(target), "init"])
        run(["git", "-C", str(target), "remote", "add", "origin", repository])
        run(["git", "-C", str(target), "fetch", "--depth=1", "origin", commit])
        run(["git", "-C", str(target), "checkout", "--detach", "FETCH_HEAD"])
        run(["git", "-C", str(target), "remote", "remove", "origin"])
    except Exception:
        if target.exists():
            import shutil

            shutil.rmtree(target)
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--defaults", action="store_true")
    parser.add_argument("--optional", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.defaults == args.optional:
        parser.error("choose exactly one of --defaults or --optional")

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    for extension in manifest["extensions"]:
        if is_enabled(extension, defaults_only=args.defaults):
            install(extension, args.destination, args.dry_run)


if __name__ == "__main__":
    main()

