# Third-party software and model assets

This repository contains deployment and bootstrap code. The published container
does not embed the Stable Diffusion checkpoints, ControlNet weights, IP-Adapter
weights, VAE files, or upscalers listed in `manifests/assets.json`; it downloads
selected assets from their pinned upstream URLs at first startup.

## Software

- AUTOMATIC1111 Stable Diffusion WebUI is pinned to the commit documented in
  `Dockerfile` and is licensed under AGPL-3.0.
- Extensions are pinned to upstream repositories and commits in
  `manifests/extensions.lock.json`. Each extension remains subject to its own
  upstream license and notices.
- CUDA, PyTorch, xFormers, Ubuntu packages, and Python dependencies remain
  subject to their respective upstream licenses.

## Models and other assets

Model weights, configuration presets, localizations, and upscalers remain
subject to their upstream terms. The license for this repository does not grant
rights to any downloaded model or asset. Operators must verify that their use,
redistribution, and any commercial offering are permitted by every applicable
upstream license.

The ZenityX Hugging Face repositories used by the manifests did not expose a
clear model license in their public metadata when this deployment project was
prepared. Public or commercial operators should publish the relevant model
cards, provenance, licenses, and attribution before offering those assets to
other users.
