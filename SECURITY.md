# Security

## Public RunPod deployments

RunPod HTTP proxy addresses are public endpoints. Keep `WEBUI_AUTH=1` and do not
place a shared `WEBUI_PASSWORD` in a public template. If no password is supplied,
this image generates a random password in `/workspace/config/gradio-auth.txt`
and prints the login to Pod logs owned by the RunPod account.

The public templates disable the A1111 API by default. Enable it only when it is
required, and keep authentication enabled.

Do not enable arbitrary extension installation for untrusted users. A WebUI
extension is executable Python code with access to the container and mounted
workspace.

## Reporting

Do not publish credentials, private model URLs, or user images in a public
issue. Contact the repository owner privately before disclosing a vulnerability.
