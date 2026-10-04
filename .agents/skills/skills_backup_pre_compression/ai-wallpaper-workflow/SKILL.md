---
name: ai-wallpaper-workflow
description: Step-by-step runbook for generating 3D Donghua and realistic AI character wallpapers using free tools (ControlNet OpenPose/Depth, IP-Adapter, ReActor, LiblibAI).
---

# AI Wallpaper & Character Generation Workflow

This guide details how to generate Chinese 3D Donghua (animation) characters, celebrity face-swaps, and high-resolution wallpapers using free and open-source generative AI tools.

---

## 1. Toolchain & Interfaces

* **Local (Free & Open Source):**
  * **ComfyUI:** Modular node-based UI offering maximum control over ControlNet, IP-Adapter, and upscaling pipelines.
  * **SD WebUI (Forge / AUTOMATIC1111):** Traditional web interface with easy extension management.
* **Cloud (Free & Low-Barrier):**
  * **[LiblibAI](https://www.liblib.art):** Primary Chinese AI platform hosting the latest Chinese 3D Donghua models and LoRAs, offering daily free generation points in-browser without local GPU requirements.
  * **[Tensor.art](https://tensor.art) / [SeaArt](https://seaart.ai):** Web-based Stable Diffusion generators with free daily tiers.
  * **Google Colab:** Free T4 GPU instances running WebUI or ComfyUI notebooks.

---

## 2. Checkpoints & LoRA Resources

* **Base Checkpoints:**
  * Realism: `MajicMix Realistic`, `ChilloutMix`, or `MoonMix`.
  * 3D Anime / Donghua: `Guoman3D`, `AnimeMix`, or fine-tuned SDXL/Flux checkpoints.
* **Character LoRAs:**
  * Search [Civitai](https://civitai.com) or [LiblibAI](https://www.liblib.art) for character names (e.g., *Medusa / Queen Medusa*, *Xiao Wu*, *Yun Yun*, *Angel Yan*).
  * Recommended LoRA weight: `0.6` to `0.85` (higher weights may burn the style or cause anatomy distortions).

---

## 3. Pose & Angle Guidance (ControlNet)

Avoid relying solely on text prompts for camera angles and complex postures.

* **OpenPose:**
  * Supply any source image or browser-posed stick figure.
  * ControlNet extracts the 18-point skeletal wireframe and locks the character into that exact posture.
* **Depth Map (Midas / ZoeDepth):**
  * Extracts foreground/background distance information.
  * Preserves 3D camera angles, cinematic perspectives, and prevents limb clipping.

---

## 4. Identity Consistency & Face-Swapping

* **IP-Adapter (Image Prompt Adapter):**
  * Input a clean portrait of the target person or character.
  * Extracts high-level face embeddings, rendering the same person across varied outfits, scenes, and lighting.
* **ReActor (InsightFace):**
  * 1-click face swap extension.
  * Applies the target face onto the generated character body while blending skin tones, lighting, and shadows.
  * Always pair with face restorers like **CodeFormer** (weight 0.6–0.8) or **GFPGAN** to eliminate blurriness.

---

## 5. 4K Wallpaper Upscaling Pipeline

To achieve true wallpaper sharpness:
1. **Initial Generation:** 512x768 (SD 1.5) or 832x1216 (SDXL).
2. **Hires. Fix / Latent Upscale:** Upscale 1.5x–2.0x with Denoising Strength `0.35`–`0.45` using `4x-UltraSharp` or `ESRGAN_4x`.
3. **Detail Enhancement:** Use **ADetailer** (After Detailer) with `face_yolov8n.pt` to detect and re-draw facial features at high resolution.
4. **Final Post-Process:** Tiled Diffusion / Ultimate SD Upscale for full 4K output without VRAM out-of-memory errors.
