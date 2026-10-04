---
name: ai-wallpaper-workflow
description: Fast production runbook for 3D Donghua and realistic AI character wallpapers via ControlNet, IP-Adapter, ReActor, and LiblibAI.
---

# AI Wallpaper & Character Workflow (Compressed)

**1. INTERFACES & RUNTIMES:**
- [LOCAL]: ComfyUI (modular node graph) | SD WebUI Forge (low VRAM, fast swap).
- [CLOUD-FREE]: LiblibAI (liblib.art, daily free points, native Donghua LoRAs) | Tensor.art | Colab T4.
- [BAN]: NO pure CPU generation for upscaling.

**2. MODEL STACK & LORAS:**
- [CHECKPOINTS]: `MajicMix Realistic` (photo/hybrid) | `Guoman3D` / `ChilloutMix` (3D Donghua).
- [LORAS]: Civitai/LiblibAI character LoRAs (Medusa, Xiao Wu, Yun Yun). Weight: `0.6-0.85`.
- [BAN]: NO LoRA weight >0.9 (prevents style burn/anatomy deformities).

**3. POSE & CAMERA CONTROL (ControlNet):**
- [BAN]: NO text-only prompt guessing for camera angles or dynamic poses.
- [OPENPOSE]: 18-point skeletal wireframe from source image. Locks posture/tilt.
- [DEPTH]: ZoeDepth / Midas preprocessor. Locks 3D lens distance, perspective, eliminates clipping.

**4. FACE CONSISTENCY & SWAP:**
- [IP-ADAPTER]: Single portrait reference -> image embedding -> cross-scene identity retention.
- [REACTOR]: InsightFace `inswapper_128` 1-click swap onto generated body.
- [RESTORER]: CodeFormer (weight: `0.6-0.8`) or GFPGAN mandatory on swapped faces.

**5. 4K WALLPAPER UPSCALE PIPELINE:**
- Step 1 (Base): 512x768 (SD1.5) or 832x1216 (SDXL).
- Step 2 (Latent): Hires. fix 1.5-2.0x, Denoise `0.35-0.42`, Scaler `4x-UltraSharp` / `ESRGAN_4x`.
- Step 3 (Detail): ADetailer with `face_yolov8n.pt` for in-generation face redraw.
- Step 4 (4K): Tiled Diffusion / Ultimate SD Upscale (prevents CUDA OOM).
