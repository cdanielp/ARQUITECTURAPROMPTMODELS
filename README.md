# ComfyUI FloorPlan Camera 📐

Interactive 2D camera placement on architectural floor plans for ComfyUI. Drag a camera over your floor plan, point it where you want, and get a formatted prompt string ready for **Qwen Image Edit 2511** or any text-to-image pipeline.

![ComfyUI](https://img.shields.io/badge/ComfyUI-Custom_Node-green)
![License](https://img.shields.io/badge/license-MIT-blue)

---

## Features

- **Interactive Canvas** — Floor plan displayed inside the node with drag-and-drop camera
- **Camera Placement** — Click anywhere on the plan to place the camera, drag to reposition
- **Rotation Control** — Yellow handle to aim the camera direction with real-time FOV cone preview
- **3 Prompt Modes** — `interior_photo`, `architectural_viz`, `custom_prefix` (compatible with `<sks>` token)
- **Material References** — Chain multiple `Material Reference 🧱` nodes to include material context in prompts
- **Style Text** — Optional free-text style description appended to the prompt
- **Live Info Bar** — Coordinates, angle, and cardinal direction displayed in real-time
- **Workflow Persistence** — Camera position and rotation saved/restored with the workflow JSON

---

## Installation

### Option 1: ComfyUI Manager

Search for **FloorPlan Camera** in ComfyUI Manager and install.

### Option 2: Manual

```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/PromptModelsStudio/comfyui-floorplan-camera.git
```

Restart ComfyUI. No additional dependencies required (uses Pillow and NumPy already included in ComfyUI).

---

## Nodes

### FloorPlan Camera 📐

Main node. Displays an interactive canvas with your floor plan and a draggable camera.

| Input | Type | Description |
|-------|------|-------------|
| `image_plan` | IMAGE | Your 2D floor plan image |
| `image_style` | IMAGE | Optional style reference image |
| `mat_stack` | MAT_STACK | Optional material stack from Material Reference nodes |
| `style_text` | STRING | Optional additional style description |
| `custom_prefix` | STRING | Custom token prefix (default `<sks>`) |
| `prompt_mode` | COMBO | `interior_photo` · `architectural_viz` · `custom_prefix` |

| Output | Type | Description |
|--------|------|-------------|
| `prompt` | STRING | Formatted prompt for image generation |
| `camera_info` | STRING | Debug info: position, zone, rotation, cardinal |

**Canvas Controls:**

| Action | Effect |
|--------|--------|
| Click on canvas | Place camera at that position |
| Drag green circle | Move camera |
| Drag yellow handle | Rotate camera direction |

### Material Reference 🧱

Chainable node. Connect multiple in series to build a stack of material references.

| Input | Type | Description |
|-------|------|-------------|
| `image` | IMAGE | Material reference photo |
| `label` | STRING | Material name (e.g. `floor`, `wall`, `ceiling`) |
| `mat_stack` | MAT_STACK | Optional incoming stack from previous node |

| Output | Type | Description |
|--------|------|-------------|
| `mat_stack` | MAT_STACK | Accumulated material stack |

---

## Prompt Modes

### `interior_photo`
```
interior photograph taken from the back-left side of the room,
camera facing towards the right corner, eye-level perspective,
looking northeast, wide-angle lens, natural lighting,
architectural interior photography
```

### `architectural_viz`
```
photorealistic architectural visualization,
interior view from center of the room,
perspective looking towards the entrance,
camera direction south, professional rendering,
ambient occlusion, global illumination, high detail
```

### `custom_prefix`
```
<sks> interior view from center, facing south, eye-level
```

---

## Workflow

Basic connection:

```
[LoadImage] ──IMAGE──→ [FloorPlan Camera 📐] ──prompt──→ [Qwen Image Edit 2511]
                                                          ──image──→
```

With materials:

```
[LoadImage: floor tile] → [Material Reference 🧱 "floor"]
                                     ↓ mat_stack
[LoadImage: wall paint] → [Material Reference 🧱 "wall"]
                                     ↓ mat_stack
                          [FloorPlan Camera 📐] → prompt → [Qwen Image Edit]
```

The `prompt` output is a plain STRING, compatible with:
- Qwen Image Edit 2511 (`cc56276d` subgraph node)
- TextEncodeQwenImageEditPlus
- Any CLIP text encoder
- ShowText for debugging

---

## Compatibility

- **ComfyUI** 0.3.x+ (LiteGraph canvas API)
- **ComfyUI Frontend** Vue or Legacy
- Works alongside `comfyui-qwenmultiangle` — different use case (3D object angles vs 2D floor plan interior views)

---

## File Structure

```
comfyui-floorplan-camera/
├── __init__.py              # Node registration + WEB_DIRECTORY
├── nodes.py                 # FloorPlanCameraNode + MaterialRefNode
├── js/
│   └── floorplan_camera.js  # Interactive canvas frontend
├── pyproject.toml           # Comfy Registry metadata
├── LICENSE
└── README.md
```

---

## Credits

Developed by [Prompt Models Studio](https://promptmodels.studio) — AI education and tooling for the Spanish-speaking community.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
