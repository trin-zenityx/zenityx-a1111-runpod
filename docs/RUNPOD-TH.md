<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/zenityx-logo-dark.png">
    <source media="(prefers-color-scheme: light)" srcset="assets/zenityx-logo-light.png">
    <img alt="ZenityX" src="assets/zenityx-logo-light.png" width="360">
  </picture>
</p>

# คู่มือเปิด ZenityX AUTOMATIC1111 บน RunPod

คู่มือนี้สำหรับผู้ที่ต้องการใช้ Stable Diffusion แบบหน้าตา AUTOMATIC1111 (A1111)
โดยไม่ต้องติดตั้ง CUDA, Python หรือโมเดลเองบนเครื่อง. ผู้ใช้แต่ละคนจะสร้าง Pod
แยกของตัวเองบนบัญชี RunPod ของตนเอง จึงไม่แชร์ prompt, การตั้งค่า, โมเดล
หรือผลลัพธ์กับผู้ใช้อื่น.

> คู่มือนี้จัดทำโดย **ZenityX** จาก workflow เดิมบน Google Colab สู่ GPU Cloud
> สำหรับผู้เรียน ครีเอเตอร์ และผู้ที่ต้องการทดลอง Generative AI ด้วย workspace
> ส่วนตัวของตนเอง.

Public templates หลักใช้โหมด **No Login** สำหรับงานอายุสั้น. URL ของ RunPod
proxy เข้าถึงได้จากอินเทอร์เน็ตระหว่างที่ Pod ทำงาน จึงไม่ควรแชร์ลิงก์และควร
Stop/Terminate ทันทีเมื่อใช้เสร็จ. A1111 API และ insecure extension access ยังปิด.

> RunPod คิดเงินตามเวลาที่ GPU และพื้นที่เก็บข้อมูลถูกจัดสรร. ดูราคาจริงบนหน้า
> Deploy ก่อนกดยืนยันทุกครั้ง เพราะชนิด GPU, จำนวนเครื่องว่าง และราคาเปลี่ยนได้.

## 1. เลือกชุดที่ต้องการ

### Full SD1.5 + ControlNet — แนะนำ

[เปิดหน้า Deploy Full บน RunPod](https://console.runpod.io/deploy?template=kdtnt1n8is)

เหมาะกับผู้ที่ต้องการใช้งานครบแบบ Colab เดิม:

- AUTOMATIC1111 `v1.10.1`
- Magmix v8, VAE และ upscaler
- ControlNet `v1.1.455`
- ControlNet 1.1 SD1.5 fp16 ครบ 14 ตัว
- ControlNet++ 5 ตัว, QR Monster
- IP-Adapter 3 ตัว และ CLIP-H image encoder
- ADetailer และ preset ภาษาไทย
- ดาวน์โหลด asset ครั้งแรกประมาณ `21.4 GiB`

แนะนำ GPU ที่มี VRAM `24 GB` เพื่อให้ใช้ ControlNet, ADetailer และ upscale
ได้สะดวก. GPU 16 GB ใช้ SD1.5 งานพื้นฐานได้ แต่ต้องลด resolution, batch size
หรือจำนวน ControlNet เมื่อหน่วยความจำไม่พอ.

### Lite — ทดลองระบบเร็วและประหยัดพื้นที่

[เปิดหน้า Deploy Lite บน RunPod](https://console.runpod.io/deploy?template=2zoj4oile9)

มี A1111, Magmix v8, VAE, upscaler, ADetailer, ControlNet extension และ preset
แต่ไม่ดาวน์โหลด ControlNet weights ชุดเต็ม. ดาวน์โหลด asset ครั้งแรกประมาณ
`5.3 GiB`. แนะนำ GPU VRAM `12 GB` ขึ้นไป.

## 2. เตรียมบัญชี RunPod

1. ไปที่ [RunPod](https://www.runpod.io/) และสร้างบัญชี.
2. ยืนยันอีเมลและเปิด Two-Factor Authentication (2FA).
3. เติมเครดิตให้เพียงพอสำหรับ GPU ที่จะเลือก. RunPod จะแสดงราคาต่อชั่วโมงก่อน
   Deploy และต้องมีเครดิตขั้นต่ำตามเงื่อนไขของระบบ.
4. อย่าแจก API key, รหัสผ่าน RunPod หรือ Container Logs ให้ผู้อื่น.

## 3. เลือกวิธีเก็บข้อมูลก่อน Deploy

ข้อมูลของชุดนี้อยู่ใต้ `/workspace` ได้แก่ config, checkpoint, LoRA, VAE,
ControlNet, cache และ outputs.

### ทางเลือก A: Volume Disk ที่มากับ template

เหมาะกับการทดลองหรือใช้งานช่วงสั้น:

- Full ให้ Volume Disk `50 GB`.
- Lite ให้ Volume Disk `30 GB`.
- ข้อมูลใน `/workspace` อยู่ต่อเมื่อกด Stop แล้ว Start Pod เดิม.
- ข้อมูลทั้งหมดถูกลบเมื่อกด Terminate.
- แม้ Stop แล้ว RunPod ยังคิดค่าพื้นที่ Volume Disk.

### ทางเลือก B: Network Volume

เหมาะกับผู้ที่ต้องการลบ Pod เพื่อหยุดค่า GPU แล้วนำโมเดลและผลงานไปใช้กับ
Pod ใหม่ภายหลัง:

1. เปิดเมนู **Storage > Network Volumes** ใน RunPod.
2. สร้าง Network Volume ใน datacenter ที่มี GPU ที่ต้องการ.
3. แนะนำ `50–100 GB` สำหรับ Full; ถ้าจะเพิ่ม checkpoint/LoRA จำนวนมากให้ใช้
   `100 GB` ขึ้นไป.
4. ในหน้า Deploy ให้เลือก Network Volume นี้ก่อนสร้าง Pod.
5. ตรวจว่า mount path เป็น `/workspace`.

Network Volume มีค่าใช้จ่ายต่อเนื่องแม้ไม่มี Pod. การแนบ Network Volume จะใช้
volume นั้นแทน Volume Disk ของ template และต้องเลือก datacenter ที่เข้ากัน.

## 4. Deploy Pod

1. กดลิงก์ Full หรือ Lite ในหัวข้อ 1. ถ้ายังไม่ได้เข้าสู่ระบบ RunPod ให้ login
   แล้วเปิดลิงก์อีกครั้ง.
2. ตรวจชื่อ template:
   - `ZenityX A1111 Full SD15 ControlNet - No Login`
   - `ZenityX A1111 Lite - No Login`
3. เลือก **GPU Cloud** และ NVIDIA GPU ที่มี VRAM ตามคำแนะนำ.
4. สำหรับการทดลองทั่วไปเลือก **On-Demand** เพื่อไม่ผูกสัญญาระยะยาว.
5. เลือก GPU Count เท่ากับ `1`. A1111 instance นี้ไม่ได้ออกแบบให้กระจายงาน
   หนึ่งหน้า UI ไปหลาย GPU.
6. เลือก storage ให้ครบ:
   - ถ้ายังไม่มี Network Volume ให้เปลี่ยนตัวกรองด้านบนจาก **Network volume**
     เป็น **Volume disk** แล้วใช้ขนาดที่ template กำหนด.
   - ถ้าต้องการเก็บข้อมูลข้าม Pod ให้เลือก Network Volume จากหัวข้อ 3.
   - ถ้าปุ่ม Deploy เป็นสีเทาและขึ้น `No network volume has been selected` แปลว่า
     หน้าเว็บอยู่โหมด Network volume แต่ยังไม่ได้เลือก volume; ให้เลือก volume
     หรือสลับกลับเป็น Volume disk.
7. ตรวจราคาต่อชั่วโมงและขนาด storage อีกครั้ง.
8. กด **Deploy On-Demand**.

ค่าที่ template จัดให้แล้ว ไม่ต้องแก้:

| รายการ | ค่า |
| --- | --- |
| Container image | `ghcr.io/trin-zenityx/zenityx-a1111-runpod:0.1.7` แบบตรึง digest |
| HTTP port | `7860` |
| Volume mount | `/workspace` |
| WebUI authentication | ปิด (No Login) |
| A1111 API | ปิด |
| UI language | ไทย |

อย่าเพิ่ม Container Start Command หรือ Docker Entrypoint เอง เพราะจะทับคำสั่ง
เริ่มต้นที่อยู่ใน Docker image.

## 5. รอการติดตั้งครั้งแรก

1. เปิดหน้า **Pods** แล้วกดขยาย Pod ที่เพิ่งสร้าง.
2. เปิดแท็บ **Logs > Container Logs**.
3. ครั้งแรกระบบจะ pull Docker image และดาวน์โหลดโมเดลลง `/workspace`.
   ระยะเวลาขึ้นกับความเร็ว host และจำนวน asset. ระหว่างนี้ลิงก์ WebUI อาจขึ้น
   `502`, `404` หรือยังไม่ Ready ซึ่งถือว่าปกติ.
4. รอจนเห็นข้อความ:

   ```text
   [zenityx] WARNING: WebUI authentication is disabled; the RunPod proxy URL is public.
   [zenityx] Starting A1111 on port 7860
   ```

ไม่จำเป็นต้องเปิด Web Terminal เพื่อใช้งานปกติ.

### ผลทดสอบ Cold Start ของ Full template

ทดสอบจริงวันที่ 22 กรกฎาคม 2026 ด้วย Full No Login template บน Community
Cloud, RTX 3090 24 GB, Volume Disk ใหม่ และไม่มี cache ใน `/workspace`:

| เหตุการณ์ | เวลาหลัง Deploy |
| --- | ---: |
| เริ่ม Deploy | `00:00` |
| เริ่มแตก Docker image layer | `01:53` |
| เตรียม asset 21.4 GiB และ workspace เสร็จ | `09:43` |
| A1111 เปิด port 7860 | `09:57` |
| ตรวจพบหน้า No Login ผ่าน HTTPS proxy | `10:11` |
| สร้างภาพ Magmix 512 × 768 พร้อม ADetailer | `4.9 วินาที` |

ตัวเลขนี้เป็นผลจากหนึ่ง cold start ไม่ใช่ SLA. Host ที่มี image cache, ความเร็ว
เครือข่าย, datacenter และ GPU ที่เลือกอาจทำให้เร็วหรือช้ากว่านี้. รอบทดสอบเปิด Pod
รวม `12:51` นาทีแล้ว Terminate; ราคา compute ที่ API แจ้งคือ `$0.22/ชั่วโมง`
และหน้า Console แสดงรวมประมาณ `$0.23/ชั่วโมง`.

### วิธีลดเวลารอและค่าใช้จ่าย

1. ถ้าต้องการทดสอบ A1111 ก่อน ให้ใช้ Lite ซึ่งดาวน์โหลดประมาณ `5.3 GiB` แทน
   Full `21.4 GiB`; Lite ไม่มี ControlNet weights ชุดเต็ม.
2. ถ้าใช้ซ้ำหลายครั้ง ให้เก็บ `/workspace` บน Network Volume หรือ Stop Pod เดิม.
   รอบถัดไปจะตรวจไฟล์เดิมแล้วข้ามการดาวน์โหลด แต่ยังมีค่า storage ระหว่างที่ไม่ใช้.
3. เลือก GPU/datacenter ที่มีเครื่องพร้อมและตรวจราคาในหน้า Deploy. GPU แพงกว่า
   ไม่ได้ทำให้ช่วง pull image และดาวน์โหลดโมเดลเร็วขึ้นเสมอไป.
4. อย่าเปิด optional extensions ที่ยังไม่ใช้ เพราะการติดตั้ง dependency เพิ่มทำให้
   startup ครั้งแรกช้าลง.
5. สำหรับผู้ดูแล image งานปรับปรุงลำดับถัดไปคือทำ runtime image ให้เล็กลงและทดลอง
   ดาวน์โหลด asset หลายไฟล์พร้อมกัน. ต้อง benchmark ก่อนปล่อยจริง เพราะการยัด
   model 21.4 GiB ทั้งหมดเข้า Docker image อาจทำให้ cold pull ช้ากว่าเดิม.

RunPod Cached Models เป็นคุณสมบัติของ Serverless endpoint ไม่ใช่ Pod ที่เปิด
A1111 UI จึงใช้ลด cold start ของ template นี้โดยตรงไม่ได้.

## 6. เปิด A1111

1. เปิดแท็บ **Connect** ของ Pod.
2. ในส่วน **HTTP Services** กดลิงก์ port `7860`.
3. RunPod จะเปิด URL รูปแบบ
   `https://POD_ID-7860.proxy.runpod.net`.
4. หน้า A1111 จะเปิดโดยไม่ถาม username/password.
5. ถ้า browser แสดงหน้าเก่าหรือ ControlNet ยังไม่ขึ้น ให้ hard refresh:
   - macOS: `Command + Shift + R`
   - Windows/Linux: `Ctrl + Shift + R`

## 7. ตรวจว่าระบบพร้อม

หลังเปิดหน้า WebUI ให้ตรวจดังนี้:

1. ด้านบนเลือก checkpoint `magmix_v80.safetensors`.
2. เปิดแท็บ `txt2img` และเลื่อนลงด้านล่าง.
3. Full ต้องเห็นแผง `ControlNet v1.1.455` พร้อม Unit 0–2.
4. เมื่อเปิด ControlNet ต้องเห็นประเภทอย่างน้อย Canny, Depth และ IP-Adapter.
5. ทดลองสร้างภาพ SD1.5 ที่ `512 × 512`, batch size `1` ก่อน.
6. ค่อยเพิ่ม resolution, Hires. fix, ADetailer หรือ ControlNet ทีละอย่างเพื่อดู
   การใช้ VRAM.

## 8. ตำแหน่งไฟล์สำคัญ

| ประเภท | ตำแหน่งใน Pod |
| --- | --- |
| Checkpoint | `/workspace/models/Stable-diffusion` |
| LoRA | `/workspace/models/Lora` |
| VAE | `/workspace/models/VAE` |
| ControlNet | `/workspace/models/ControlNet` |
| ControlNet preprocessors | `/workspace/models/ControlNet-Preprocessors` |
| Embeddings | `/workspace/embeddings` |
| A1111 config/extensions | `/workspace/a1111` |
| ผลลัพธ์ | `/workspace/outputs` |
| WebUI login (เมื่อเปิด auth เอง) | `/workspace/config/gradio-auth.txt` |

หลังเพิ่ม checkpoint, LoRA หรือ VAE ให้กดปุ่ม refresh ข้างรายการโมเดลใน A1111
หรือ restart Pod. โมเดลที่เพิ่มเองต้องมีสิทธิ์ใช้งานที่เหมาะสม.

## 9. เปิดรหัสผ่านและค่าขั้นสูง

ค่าเริ่มต้นเป็น No Login ตามรูปแบบงาน Pod อายุสั้น. หากต้องการเปิด authentication
ให้ตั้ง `WEBUI_AUTH=1`, สร้าง **RunPod Secret** และอ้าง secret ใน environment
variable `WEBUI_PASSWORD`; อย่าใส่รหัสจริงไว้ใน template ที่จะแชร์.

Environment variables ที่ใช้บ่อย:

| ตัวแปร | ค่า/ความหมาย |
| --- | --- |
| `ZENITYX_PROFILE` | `lite` หรือ `colab` |
| `ZENITYX_CONFIG_PRESET` | ค่าเริ่มต้นคือ `sd15-v2-thai` |
| `WEBUI_USERNAME` | ใช้เมื่อเปิด auth; ค่าแนะนำ `zenityx` |
| `WEBUI_AUTH` | `0` คือ No Login, `1` คือเปิด authentication |
| `ENABLE_API` | ค่า public template คือ `0` |
| `FORCE_PRESET` | ใช้ `1` ครั้งเดียวเมื่อต้องการรีเซ็ต config แล้วคืนเป็น `0` |

การแก้ environment ของ Pod ที่กำลังทำงานอาจทำให้ container reset. เก็บไฟล์ที่
ต้องการไว้ใน `/workspace` ก่อนแก้ทุกครั้ง.

## 10. หยุดค่าใช้จ่ายให้ถูกวิธี

### Stop

- ปล่อย GPU คืนและหยุดค่า compute.
- Volume Disk ใน `/workspace` ยังอยู่เพื่อ Start Pod เดิมภายหลัง.
- ยังมีค่า storage ต่อเนื่อง; Volume Disk ที่หยุดมีอัตราสูงกว่าตอน Pod ทำงานตาม
  ตารางราคาปัจจุบันของ RunPod.

### Terminate

- ลบ Pod และ Volume Disk ของ Pod แบบถาวร.
- หยุดทั้งค่า GPU และค่า local Volume Disk ของ Pod นั้น.
- Network Volume ไม่ถูกลบและยังคิดค่า storage แยกต่างหาก.

ถ้าทดลองเสร็จและไม่ต้องเก็บ `/workspace`:

1. ดาวน์โหลดภาพหรือไฟล์ที่ต้องการจาก A1111.
2. กด **Stop** และยืนยัน.
3. กด **Terminate** (ไอคอนถังขยะ) และยืนยันอีกครั้ง.
4. ตรวจหน้า Pods ว่าไม่มี Pod ค้าง.
5. ตรวจหน้า Network Volumes และ Billing ถ้าเป้าหมายคือต้องการให้ค่าใช้จ่ายเหลือ
   ศูนย์จริง.

ราคาพื้นที่ตามเอกสาร RunPod ณ วันที่อัปเดตคู่มือนี้:

- Container disk: `$0.10/GB/เดือน` เฉพาะตอน Pod ทำงาน.
- Volume disk: `$0.10/GB/เดือน` ตอนทำงาน และ `$0.20/GB/เดือน` ตอนหยุด.
- Network volume ต่ำกว่า 1 TB: `$0.07/GB/เดือน` และคิดต่อแม้ไม่มี Pod.

ตรวจราคาล่าสุดที่ [RunPod Pod pricing](https://docs.runpod.io/pods/pricing).

## 11. แก้ปัญหาที่พบบ่อย

### HTTP 502 / WebUI ยังเปิดไม่ได้

เปิด Container Logs. ถ้ายังดาวน์โหลด asset หรือยังไม่เห็น `Starting A1111 on
port 7860` ให้รอ. Full ต้องดาวน์โหลดมากกว่า Lite อย่างชัดเจน.

### ต้องการเปิด username/password

ตั้ง `WEBUI_AUTH=1`, `WEBUI_USERNAME` และ `WEBUI_PASSWORD` ผ่าน RunPod Secret
แล้ว restart container. รหัสจะถูกเก็บใน `/workspace/config/gradio-auth.txt`.

### ไม่เห็น ControlNet

ตรวจว่าใช้ Full template และ image รุ่น `0.1.7` แบบตรึง digest, รอ startup ให้
เสร็จ แล้ว hard refresh. Lite มี extension แต่ไม่มี weights ชุดเต็ม. ใน Full
ต้องเห็น `ControlNet v1.1.455` ทั้ง `txt2img` และ `img2img`.

### CUDA out of memory

ลด batch size เป็น `1`, ลดขนาดภาพ, ปิด Hires. fix, ลดจำนวน ControlNet Unit,
ปิด ADetailer ชั่วคราว หรือเปลี่ยนไปใช้ GPU ที่มี VRAM มากขึ้น.

### Start Pod เดิมแล้วไม่มี GPU

เมื่อ Stop แล้ว GPU เดิมถูกปล่อยคืน. หากชนิดนั้นไม่มีเครื่องว่าง RunPod อาจ Start
ไม่ได้ ให้รอหรือ Deploy Pod ใหม่ด้วย GPU ชนิดอื่น. ถ้าต้องย้ายข้อมูลระหว่าง Pod
ควรใช้ Network Volume.

### Disk เต็ม

ลบ output/cache ที่ไม่ใช้หรือเพิ่มขนาด volume. Volume Disk เพิ่มได้แต่ลดไม่ได้.
สำรองข้อมูลก่อนแก้ Pod configuration.

## 12. ความปลอดภัยและสิทธิ์ใช้งาน

- URL จาก RunPod proxy เข้าถึงได้จากอินเทอร์เน็ต. No Login เหมาะเฉพาะงานอายุสั้น;
  อย่าแชร์ URL และให้ Stop/Terminate ทันทีเมื่อใช้เสร็จ.
- อย่าเปิด `--enable-insecure-extension-access` หรือ API โดยไม่เข้าใจความเสี่ยง.
- Extension ของ A1111 คือ Python code; ติดตั้งเฉพาะแหล่งที่เชื่อถือได้.
- Docker image นี้เป็น community template ไม่ใช่ template ที่ RunPod รับรองหรือ
  ดูแลอย่างเป็นทางการ.
- License ของ source repository ไม่ได้ให้สิทธิ์ใช้งาน checkpoint, LoRA, VAE หรือ
  model weights ของบุคคลอื่นโดยอัตโนมัติ. ตรวจ license ก่อนใช้เชิงพาณิชย์.

Source และรายการ third-party notices:

- [GitHub repository](https://github.com/trin-zenityx/zenityx-a1111-runpod)
- [Release v0.1.7](https://github.com/trin-zenityx/zenityx-a1111-runpod/releases/tag/v0.1.7)
- [Third-party notices](../THIRD_PARTY_NOTICES.md)
- [RunPod: Manage Pods](https://docs.runpod.io/pods/manage-pods)
- [RunPod: Storage options](https://docs.runpod.io/pods/storage/types)

หากพบปัญหา ให้เปิด issue โดยแนบชื่อ GPU, template Full/Lite, image tag,
ช่วง log ที่ไม่มีรหัสผ่าน/API key และขั้นตอนที่ทำให้เกิดปัญหา.

## 13. เรียนรู้และต่อยอดกับ ZenityX

ชุด RunPod นี้เป็นส่วนหนึ่งของแนวทางที่ ZenityX ใช้ช่วยให้ผู้เรียนเริ่มจาก
workflow ที่คุ้นเคย แล้วต่อยอดไปสู่การสร้างผลงาน Generative AI บน Cloud:

- [ZenityX Studio](https://studio.zenityx.com) — แพลตฟอร์มสร้างภาพ วิดีโอ
  อวตาร และเสียงด้วย AI ในที่เดียว
- [YouTube @ZenityXAI](https://www.youtube.com/@ZenityXAI) — บทเรียน แนวทาง
  การใช้งาน และ workflow จาก ZenityX
- [GitHub ของโปรเจกต์](https://github.com/trin-zenityx/zenityx-a1111-runpod) —
  source code, release และช่องทางแจ้งปัญหา

โลโก้และชื่อ ZenityX ใช้เพื่อระบุผู้จัดทำและผู้ดูแลโปรเจกต์ ส่วน AUTOMATIC1111,
RunPod และโมเดลต่าง ๆ เป็นโครงการหรือบริการของเจ้าของแต่ละราย.
