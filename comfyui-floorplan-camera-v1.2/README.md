# ComfyUI FloorPlan Camera 📐

Interactive 2D camera placement on architectural floor plans for ComfyUI. Drag a camera over your floor plan, point it where you want, and get a formatted prompt string ready for Qwen Image Edit 2511 or any text-to-image pipeline.

![ComfyUI](https://img.shields.io/badge/ComfyUI-Custom_Node-blue)
![license MIT](https://img.shields.io/badge/license-MIT-green)

## Nodes (7 total)

### Core Nodes

| Node | Category | Description |
|------|----------|-------------|
| **FloorPlan Camera 📐** | FloorPlan | Interactive canvas — drag camera, rotate direction, outputs prompt |
| **Material Reference 🧱** | FloorPlan | Chain material images with labels into prompts |

### Architecture Nodes (deterministic, no API needed)

| Node | Category | Description |
|------|----------|-------------|
| **Lens & Camera Preset 📷** | FloorPlan/Architecture | Photographic context: focal length, height, composition style |
| **Lighting Intent 💡** | FloorPlan/Architecture | Lighting strategy: daylight, golden hour, night, dramatic |
| **Arch Negative Prompt 🚫** | FloorPlan/Architecture | Room-specific + engine-specific negative prompts |
| **Shot Presets 🎯** | FloorPlan/Architecture | Predefined camera positions by room type |
| **Arch Prompt Combiner 🔗** | FloorPlan/Architecture | Merges camera + lens + lighting + VLM into final prompt |

## Installation

### Option 1: ComfyUI Manager
Search for **FloorPlan Camera** in ComfyUI Manager and install.

### Option 2: Manual
```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/cdanielp/ARQUITECTURAPROMPTMODELS.git
# Restart ComfyUI
```

## Quick Start

### Minimal (3 nodes)
```
LoadImage → FloorPlan Camera 📐 → [your text encoder]
```

### Full Architecture Pipeline (7 nodes)
```
LoadImage ──→ FloorPlan Camera 📐 ──→ Arch Prompt Combiner 🔗 ──→ Qwen Image Edit
                                            ↑           ↑
Shot Presets 🎯 ──cam_x,y,rot──→            │           │
Lens & Camera Preset 📷 ────────────────────┘           │
Lighting Intent 💡 ─────────────────────────────────────┘

Arch Negative Prompt 🚫 ──→ [negative input]
```

### With VLM Analysis (add Gemini or any VLM)
```
LoadImage ──→ FloorPlan Camera 📐
         └──→ GoogleAI TextVision 🧠 ──vlm_description──→ Arch Prompt Combiner 🔗
```

## Node Details

### FloorPlan Camera 📐

**Inputs:**
- `image_plan` (IMAGE) — your floor plan
- `cam_x`, `cam_y`, `cam_rotation` (hidden, set via canvas)
- `prompt_mode` — interior_photo / architectural_viz / custom_prefix
- `style_text` — optional style description
- `custom_prefix` — prefix for custom mode (default: `<sks>`)

**Outputs:**
- `prompt` (STRING) — formatted prompt
- `camera_info` (STRING) — debug info

**Canvas interaction:**
- Click anywhere → teleport camera
- Drag green circle → move camera
- Drag yellow handle → rotate direction
- Info bar shows coordinates + angle + cardinal

### Lens & Camera Preset 📷

6 presets: `architectural_neutral` (24mm), `real_estate_wide` (16mm), `editorial` (35mm), `hero_shot` (28mm low), `detail_close` (50mm), `birds_eye` (24mm overhead).

Room-specific hints for: bathroom, kitchen, living_room, bedroom, dining_room, hallway, office, exterior.

### Lighting Intent 💡

7 presets: `day_soft`, `golden_hour`, `overcast`, `night_warm`, `night_cool`, `mixed`, `dramatic`.

Each combines with room-specific lighting notes.

### Arch Negative Prompt 🚫

Generates negative prompts combining:
- Base architectural negatives (distortion, floating objects, etc.)
- Room-specific negatives (kitchen: misaligned cabinets, bathroom: cracked tiles, etc.)
- Engine-specific negatives (qwen_edit, flux, sdxl)

### Shot Presets 🎯

Predefined camera positions for: living_room (4 shots), kitchen (3), bedroom (3), bathroom (3), dining_room (2), exterior (3).

Outputs `cam_x`, `cam_y`, `cam_rotation` + `room_type` + `description`.

### Arch Prompt Combiner 🔗

Merges all prompt sources into one. When `vlm_description` is connected, uses VLM analysis as the base instead of generic descriptions.

## Workflows

Two example workflows included:

1. **01_deterministic_full.json** — All architecture nodes without VLM
2. **02_with_gemini_vlm.json** — Full pipeline with Gemini analysis (requires [COMFYUI_PROMPTMODELS](https://github.com/cdanielp/COMFYUI_PROMPTMODELS))

## Compatibility

- ComfyUI 0.3.x+
- Works with Qwen Image Edit 2511, Flux, SDXL, or any text encoder
- Google AI nodes optional (for VLM workflow)

## License

MIT — Prompt Models Studio | cdanielp
