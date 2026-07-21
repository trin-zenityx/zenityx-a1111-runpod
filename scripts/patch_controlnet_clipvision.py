#!/usr/bin/env python3
"""Patch pinned ControlNet CLIP-H loading to use a pinned safetensors file."""

from __future__ import annotations

import argparse
from pathlib import Path


PINNED_CLIP_H_URL = (
    "https://huggingface.co/h94/IP-Adapter/resolve/"
    "018e402774aeeddd60609b4ecdb7e298259dc729/"
    "models/image_encoder/model.safetensors"
)

REPLACEMENTS = (
    (
        "'clip_h': 'https://huggingface.co/h94/IP-Adapter/resolve/main/"
        "models/image_encoder/pytorch_model.bin'",
        f"'clip_h': '{PINNED_CLIP_H_URL}'",
    ),
    (
        "self.file_name = config + '.pth'",
        "self.file_name = (config + '.safetensors' if config == 'clip_h' "
        "else config + '.pth')",
    ),
    (
        "        sd = torch.load(file_path, map_location=self.device)\n",
        "        if file_path.endswith('.safetensors'):\n"
        "            from safetensors.torch import load_file\n"
        "            sd = load_file(file_path, device=str(self.device))\n"
        "        else:\n"
        "            sd = torch.load(file_path, map_location=self.device)\n",
    ),
)


def patch(target: Path) -> None:
    source = target.read_text(encoding="utf-8")
    changed = False
    for original, replacement in REPLACEMENTS:
        if replacement in source:
            continue
        if original not in source:
            raise RuntimeError(
                f"ControlNet CLIP Vision source changed; expected snippet missing: {original!r}"
            )
        source = source.replace(original, replacement, 1)
        changed = True

    if changed:
        target.write_text(source, encoding="utf-8")
        print(f"[controlnet-patch] patched CLIP-H safetensors loader: {target}")
    else:
        print(f"[controlnet-patch] already patched: {target}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, required=True)
    args = parser.parse_args()
    patch(args.target)


if __name__ == "__main__":
    main()
