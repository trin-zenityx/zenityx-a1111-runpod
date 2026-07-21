# ZenityX A1111 for RunPod

Docker image สำหรับเปิด AUTOMATIC1111 Stable Diffusion WebUI บน RunPod โดยย้ายแนวคิดจาก `ZenityX_SD_Webui_Colab V3` มาเป็น container ที่สร้างใหม่ได้ และเก็บโมเดล การตั้งค่า และผลลัพธ์ไว้ถาวรใน `/workspace`.

## Public image

Release image สร้างโดย GitHub Actions จาก source repository เดียวกัน:

- Source: <https://github.com/trin-zenityx/zenityx-a1111-runpod>
- Release: <https://github.com/trin-zenityx/zenityx-a1111-runpod/releases/tag/v0.1.7>

```text
ghcr.io/trin-zenityx/zenityx-a1111-runpod:0.1.7
```

Verified linux/amd64 image digest:

```text
sha256:9389a4d09a5c08c3b78cf1f8272c3623aeb4b10a3ec2706063f78ab9ce35a66a
```

Public RunPod template จะไม่ฝังรหัสผ่านร่วมกัน หากไม่ตั้ง
`WEBUI_PASSWORD` ระบบจะสร้างรหัสเฉพาะ workspace และแสดง login ใน Pod logs.

## เปิดบน RunPod แบบคลิกเดียว

- **Full SD1.5 + ControlNet (แนะนำ):** [Deploy ZenityX A1111 Full](https://console.runpod.io/deploy?template=f6i7jlc22q)
- **Lite สำหรับทดลองเร็ว:** [Deploy ZenityX A1111 Lite](https://console.runpod.io/deploy?template=81l0kb0hvr)

ผู้ใช้แต่ละคนจะได้ Pod, `/workspace`, การตั้งค่า, รหัสผ่าน และไฟล์ผลลัพธ์ของตัวเอง
ไม่ใช่การแชร์ A1111 instance เดียวกัน. อ่านขั้นตอนตั้งแต่สมัคร RunPod, เลือก GPU,
เปิด WebUI, เก็บงาน และหยุดค่าใช้จ่ายได้ที่
**[คู่มือ RunPod + A1111 ภาษาไทย](docs/RUNPOD-TH.md)**.

## สิ่งที่มีให้

- AUTOMATIC1111 `v1.10.1` ที่ตรึง commit ไว้
- Python 3.10, PyTorch 2.6.0 CUDA 12.4 และ xFormers
- Magmix v8, VAE, อัปสเกล 3 ตัว และ preset เดิมของ ZenityX
- Extension หลัก: Tag Complete, Ultimate Upscale, Infinite Image Browsing, ControlNet `v1.1.455`, ADetailer, Batchlinks และ Config Presets
- โปรไฟล์ `colab` มี ControlNet 1.1 SD1.5 ครบ, ControlNet++, QR Monster และ IP-Adapter; `lite` สำหรับทดสอบเร็ว
- ตรึง MediaPipe `0.10.21`, NumPy `1.26.2` และ protobuf `4.25.3` เพื่อให้ ControlNet `v1.1.455`, ADetailer และ A1111 ใช้ dependency ชุดเดียวกันโดยไม่อัปเกรดทับกันตอน startup
- CLIP-H ของ IP-Adapter ใช้ `safetensors` พร้อม SHA-256 และ compatibility patch สำหรับ PyTorch 2.6
- Config, models, LoRA, embeddings, outputs และ cache อยู่บน `/workspace`
- ตรวจขนาดและ SHA-256 ของไฟล์โมเดลที่สำคัญ
- สร้างรหัสผ่าน WebUI อัตโนมัติถ้าไม่ได้ระบุเอง
- เปิด A1111 ที่ HTTP port `7860` สำหรับ RunPod proxy

ไม่ติดตั้ง `camenduru/tunnels` เพราะ RunPod มี HTTPS proxy อยู่แล้ว และไม่เปิด `--enable-insecure-extension-access`.

## โครงสร้างข้อมูลถาวร

```text
/workspace
├── a1111
│   ├── config.json
│   ├── ui-config.json
│   ├── styles.csv
│   ├── localizations
│   └── extensions
├── config
│   └── gradio-auth.txt
├── embeddings
├── models
│   ├── Stable-diffusion
│   ├── Lora
│   ├── VAE
│   ├── ControlNet
│   ├── ControlNet-Preprocessors
│   └── ESRGAN
├── outputs
└── .cache
```

ลบ Pod ได้โดยข้อมูลยังอยู่ ถ้า `/workspace` เป็น RunPod Network Volume.

## Profiles

### `lite`

ดาวน์โหลด Magmix v8, VAE, อัปสเกล, localization และ preset ประมาณ 5.3 GiB เหมาะกับการทดสอบครั้งแรก.

### `colab`

เพิ่ม ControlNet 1.1 SD1.5 fp16 ครบ 14 ตัว, QR Monster, ControlNet++ 5 ตัว,
IP-Adapter 3 ตัว และ CLIP-H image encoder รวม asset ที่ประกาศประมาณ 21.4 GiB.
Annotator weights อื่นจะดาวน์โหลดเมื่อใช้ครั้งแรกและเก็บถาวรใน
`/workspace/models/ControlNet-Preprocessors`.

ไฟล์ดาวน์โหลดเพียงครั้งแรก ถ้าใช้ Network Volume; การเปิด Pod ครั้งถัดไปจะตรวจ marker และข้ามไฟล์ที่สมบูรณ์แล้ว.

การเปลี่ยนจาก `colab` กลับเป็น `lite` จะไม่ลบ ControlNet ที่ดาวน์โหลดไว้แล้ว ระบบนี้ไม่ลบโมเดลหรือไฟล์ผู้ใช้โดยอัตโนมัติ.

## สร้าง image

ใช้ Docker Buildx บนเครื่องที่มีพื้นที่ว่างอย่างน้อย 25 GB:

```bash
docker buildx build \
  --platform linux/amd64 \
  -t YOUR_DOCKERHUB_USER/zenityx-a1111:0.1.7 \
  --push .
```

โมเดลไม่ได้อยู่ใน Docker image แต่จะลง `/workspace` เมื่อ container เริ่มครั้งแรก จึงไม่ทำให้ image ใหญ่ขึ้นอีกหลายสิบ GB.

## สร้าง RunPod Template

1. สร้าง Network Volume อย่างน้อย `100 GB` ใน datacenter ที่ต้องการ
2. สร้าง Custom Pod Template
3. ใส่ Container Image เป็น image ที่ push ไว้
4. Container Disk แนะนำ `30–40 GB`
5. แนบ Network Volume และ mount ที่ `/workspace`
6. Expose HTTP Port เป็น `7860`
7. เพิ่ม environment variables จาก `runpod.env.example`
8. เลือก GPU 24 GB เช่น RTX 4090 แล้ว Deploy
9. เปิด Logs; เมื่อเห็น `Starting A1111 on port 7860` ให้กด Connect ที่ HTTP Service port 7860

ไฟล์ตั้งต้นสำหรับสร้าง template ผ่าน RunPod REST API อยู่ที่:

- `runpod/template-lite.json` — ทดลองเร็ว ใช้ Volume Disk 30 GB
- `runpod/template-colab.json` — ชุด SD1.5 ControlNet เต็ม ใช้ Volume Disk 50 GB

ทั้งสอง template ผ่าน GPU smoke test แล้วและตั้ง `isPublic=true` เพื่อให้ผู้ใช้
RunPod คนอื่นเปิดผ่านลิงก์ Deploy หรือค้นหาชื่อ template ใน RunPod Explore ได้.
Template IDs คือ `f6i7jlc22q` (Full) และ `81l0kb0hvr` (Lite).
Container image ใน template ตรึงทั้ง tag และ linux/amd64 digest เพื่อป้องกัน
registry หรือ host cache ชี้ไป content คนละชุด.

RunPod URL จะมีรูปแบบประมาณ:

```text
https://POD_ID-7860.proxy.runpod.net
```

### Environment ขั้นต่ำ

```env
ZENITYX_PROFILE=lite
ZENITYX_CONFIG_PRESET=sd15-v2
WEBUI_USERNAME=zenityx
```

อย่าใส่ `WEBUI_PASSWORD` ลง public template ระบบจะสร้างรหัสแบบสุ่มให้แต่ละ
workspace. เริ่มด้วย `lite` เพื่อพิสูจน์ว่า image เปิดได้ แล้วเปลี่ยนเป็น
`colab` และ restart container เพื่อเติม ControlNet ลง volume เดิม.

ถ้าไม่กำหนด `WEBUI_PASSWORD` ระบบจะสร้างรหัสแบบสุ่มครั้งแรกและเก็บใน `/workspace/config/gradio-auth.txt`; ดูค่า login ได้จาก Container Logs.

## Presets

กำหนด `ZENITYX_CONFIG_PRESET` เป็นหนึ่งใน:

- `sd15-v2` — ค่าเริ่มต้น
- `sd15-v2-thai`
- `sd15-legacy`
- `sdxl` — มีเฉพาะ config; ต้องใส่ SDXL checkpoint เอง
- `default`

ระบบใช้ preset เฉพาะตอนที่ยังไม่มี `config.json`. หากต้องการรีเซ็ตจริง ๆ ให้ตั้ง `FORCE_PRESET=1` หนึ่งครั้ง แล้วเปลี่ยนกลับเป็น `0`.

จุดนี้แก้ปัญหาใน Colab เดิมที่ดาวน์โหลด preset แล้วเขียนทับ `config.json` ด้วย output paths ทั้งไฟล์: image ใหม่นี้ใช้การ merge output paths เข้า preset แทน.

## เพิ่มโมเดลเอง

อัปโหลดไฟล์ตรงไปยัง Network Volume:

```text
/workspace/models/Stable-diffusion  Checkpoint
/workspace/models/Lora              LoRA
/workspace/models/VAE               VAE
/workspace/models/ControlNet        ControlNet
/workspace/models/ControlNet-Preprocessors  annotator และ CLIP Vision cache
/workspace/embeddings               Embeddings
```

จากนั้นกด refresh ใน A1111 หรือ restart container. ไม่ต้อง rebuild Docker image.

## Optional extensions

เปิดด้วย environment variable เช่น:

```env
EXT_ANIMATEDIFF=1
EXT_PROMPT_ALL_IN_ONE=1
EXT_WILDCARDS=1
EXT_REACTOR_SFW=1
```

รายการทั้งหมดอยู่ใน `runpod.env.example`. Optional extension จะถูก clone ลง volume ครั้งแรกและอาจติดตั้ง dependency ตอน A1111 เริ่ม ทำให้ startup ช้าขึ้น.

ReActor เดิมใน Colab ใช้ repository ที่ถูกปิดการเข้าถึงแล้ว โปรเจกต์นี้จึงเปลี่ยน optional target เป็น `sd-webui-reactor-sfw` ของผู้พัฒนารายเดิม.

## ทดสอบแบบไม่ดาวน์โหลดโมเดล

```bash
python3 scripts/validate_project.py
python3 -m py_compile scripts/*.py
bash -n docker/entrypoint.sh
```

ทดสอบรายการที่จะดาวน์โหลดแบบ dry run:

```bash
tmpdir="$(mktemp -d)"
ASSET_MANIFEST="$PWD/manifests/assets.json" \
EXTENSION_MANIFEST="$PWD/manifests/extensions.lock.json" \
OPTIONAL_INSTALLER="$PWD/scripts/install_extensions.py" \
IMAGE_EXTENSIONS="$tmpdir/image-extensions" \
OVERRIDES_FILE="$PWD/config/runtime-overrides.json" \
python3 scripts/bootstrap_workspace.py \
  --workspace "$tmpdir/workspace" \
  --profile lite \
  --preset sd15-v2 \
  --dry-run
```

เครื่อง workspace นี้ไม่มี Docker daemon จึงตรวจได้เฉพาะ static validation; ควร build image และทดสอบ GPU smoke test ก่อนนำไปใช้จริง.

## ความปลอดภัยและสิทธิ์ใช้งาน

- RunPod proxy URL เป็น public endpoint; ห้ามปิด authentication โดยไม่ตั้งใจ
- อย่าใส่รหัสผ่านจริงลง Git หรือ Docker image
- ไม่ควรเปิดหน้า Install Extension ให้ผู้ใช้อื่น เพราะ extension คือโค้ด Python
- A1111 ใช้ AGPL-3.0; หากแก้ไขและให้บุคคลอื่นใช้งานผ่านเครือข่าย ต้องตรวจหน้าที่เรื่อง source code
- Hugging Face repositories `zenityx/magmix` และ `zenityx/ZenityX_SD_Webui_Colab` ไม่ได้ประกาศ license ใน metadata ที่ตรวจล่าสุด โปรดตรวจสิทธิ์ของ checkpoint, LoRA และ asset แต่ละรายการก่อนให้บริการเชิงพาณิชย์
- อ่าน `THIRD_PARTY_NOTICES.md` ก่อนเปิด template เป็น public; license ของ repository นี้ไม่ได้ให้สิทธิ์ใช้งาน model weights ของบุคคลอื่นโดยอัตโนมัติ
