"""
FloorPlan Camera Nodes for ComfyUI
- FloorPlanCameraNode: Interactive 2D camera on floor plan, outputs prompt STRING
- MaterialRefNode: Chainable material reference accumulator
"""

import numpy as np
from PIL import Image
import base64
import io
import hashlib
import os
import folder_paths

# ─────────────────────────────────────────────────────────────
# Cache para preview images (evitar re-guardar en cada frame)
# ─────────────────────────────────────────────────────────────
_preview_cache = {}


def _tensor_to_pil(tensor):
    """ComfyUI IMAGE tensor [B,H,W,C] float32 → PIL Image"""
    i = 255.0 * tensor[0].cpu().numpy()
    return Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))


def _pil_to_base64(pil_img, fmt="PNG"):
    buf = io.BytesIO()
    pil_img.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _rotation_to_cardinal(degrees):
    """Map 0-360 degrees to cardinal/intercardinal direction."""
    dirs = [
        (0,    22.5,  "north"),
        (22.5, 67.5,  "northeast"),
        (67.5, 112.5, "east"),
        (112.5,157.5, "southeast"),
        (157.5,202.5, "south"),
        (202.5,247.5, "southwest"),
        (247.5,292.5, "west"),
        (292.5,337.5, "northwest"),
        (337.5,360.0, "north"),
    ]
    degrees = degrees % 360
    for lo, hi, name in dirs:
        if lo <= degrees < hi:
            return name
    return "north"


def _rotation_to_facing(degrees):
    """More natural description for interior views."""
    dirs = [
        (0,    22.5,  "towards the far wall"),
        (22.5, 67.5,  "towards the right corner"),
        (67.5, 112.5, "towards the right wall"),
        (112.5,157.5, "towards the near-right corner"),
        (157.5,202.5, "towards the entrance"),
        (202.5,247.5, "towards the near-left corner"),
        (247.5,292.5, "towards the left wall"),
        (292.5,337.5, "towards the far-left corner"),
        (337.5,360.0, "towards the far wall"),
    ]
    degrees = degrees % 360
    for lo, hi, name in dirs:
        if lo <= degrees < hi:
            return name
    return "towards the far wall"


def _position_to_description(cam_x, cam_y):
    """Normalized coords → spatial description."""
    h = "left side" if cam_x < 0.33 else ("center" if cam_x < 0.66 else "right side")
    v = "back" if cam_y < 0.33 else ("middle" if cam_y < 0.66 else "front")
    if h == "center" and v == "middle":
        return "center of the room"
    if h == "center":
        return f"{v} of the room"
    if v == "middle":
        return f"{h} of the room"
    return f"{v}-{h} of the room"


def _position_to_zone(cam_x, cam_y):
    """Simplified zone for prompt."""
    col = 0 if cam_x < 0.33 else (1 if cam_x < 0.66 else 2)
    row = 0 if cam_y < 0.33 else (1 if cam_y < 0.66 else 2)
    zones = {
        (0,0): "back-left",   (1,0): "back-center",   (2,0): "back-right",
        (0,1): "mid-left",    (1,1): "center",         (2,1): "mid-right",
        (0,2): "front-left",  (1,2): "front-center",   (2,2): "front-right",
    }
    return zones.get((col, row), "center")


# ─────────────────────────────────────────────────────────────
# MaterialRefNode
# ─────────────────────────────────────────────────────────────

class MaterialRefNode:
    """
    Chainable material reference node.
    Wraps an image + label into a MAT_STACK list.
    Connect multiple in series to build a stack of materials.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "label": ("STRING", {
                    "default": "floor",
                    "multiline": False,
                    "placeholder": "e.g. floor, wall, ceiling, furniture"
                }),
            },
            "optional": {
                "mat_stack": ("MAT_STACK",),
            }
        }

    RETURN_TYPES = ("MAT_STACK",)
    RETURN_NAMES = ("mat_stack",)
    FUNCTION = "process"
    CATEGORY = "FloorPlan"

    def process(self, image, label, mat_stack=None):
        pil = _tensor_to_pil(image)
        # Resize to small thumbnail for prompt context
        pil.thumbnail((256, 256), Image.LANCZOS)
        b64 = _pil_to_base64(pil)

        stack = list(mat_stack) if mat_stack else []
        stack.append({"label": label.strip(), "image_b64": b64})
        return (stack,)


# ─────────────────────────────────────────────────────────────
# FloorPlanCameraNode
# ─────────────────────────────────────────────────────────────

class FloorPlanCameraNode:
    """
    Interactive floor plan camera node.
    Displays floor plan with draggable camera + rotation control.
    Outputs a formatted prompt STRING for Qwen Image Edit or any text encoder.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_plan": ("IMAGE",),
                "cam_x": ("FLOAT", {
                    "default": 0.5, "min": 0.0, "max": 1.0, "step": 0.001
                }),
                "cam_y": ("FLOAT", {
                    "default": 0.5, "min": 0.0, "max": 1.0, "step": 0.001
                }),
                "cam_rotation": ("FLOAT", {
                    "default": 0.0, "min": 0.0, "max": 360.0, "step": 0.5
                }),
                "prompt_mode": (["interior_photo", "architectural_viz", "custom_prefix"],),
            },
            "optional": {
                "image_style": ("IMAGE",),
                "mat_stack": ("MAT_STACK",),
                "style_text": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Additional style description..."
                }),
                "custom_prefix": ("STRING", {
                    "default": "<sks>",
                    "multiline": False,
                    "placeholder": "Custom prompt prefix token"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("prompt", "camera_info")
    FUNCTION = "execute"
    CATEGORY = "FloorPlan"
    OUTPUT_NODE = False

    def execute(self, image_plan, cam_x, cam_y, cam_rotation,
                prompt_mode="interior_photo",
                image_style=None, mat_stack=None,
                style_text="", custom_prefix="<sks>"):

        # ── Build camera info string ──
        cardinal = _rotation_to_cardinal(cam_rotation)
        facing = _rotation_to_facing(cam_rotation)
        position = _position_to_description(cam_x, cam_y)
        zone = _position_to_zone(cam_x, cam_y)

        camera_info = (
            f"pos: ({cam_x:.2f}, {cam_y:.2f}) zone: {zone} | "
            f"rot: {cam_rotation:.1f}° ({cardinal}) | "
            f"facing: {facing}"
        )

        # ── Build materials context ──
        mat_context = ""
        if mat_stack:
            labels = [m["label"] for m in mat_stack]
            mat_context = f", featuring {', '.join(labels)} materials"

        # ── Build style context ──
        style_context = ""
        if style_text and style_text.strip():
            style_context = f", {style_text.strip()}"

        # ── Generate prompt based on mode ──
        if prompt_mode == "interior_photo":
            prompt = (
                f"interior photograph taken from the {position}, "
                f"camera facing {facing}, "
                f"eye-level perspective, "
                f"looking {cardinal}, "
                f"wide-angle lens, natural lighting, "
                f"architectural interior photography"
                f"{mat_context}{style_context}"
            )

        elif prompt_mode == "architectural_viz":
            prompt = (
                f"photorealistic architectural visualization, "
                f"interior view from {position}, "
                f"perspective looking {facing}, "
                f"camera direction {cardinal}, "
                f"professional rendering, ambient occlusion, "
                f"global illumination, high detail"
                f"{mat_context}{style_context}"
            )

        elif prompt_mode == "custom_prefix":
            prefix = custom_prefix.strip() if custom_prefix else "<sks>"
            prompt = (
                f"{prefix} "
                f"interior view from {zone}, "
                f"facing {cardinal}, "
                f"eye-level"
                f"{mat_context}{style_context}"
            )

        else:
            prompt = f"interior view from {position}, looking {cardinal}"

        # ── Save preview image for JS frontend ──
        pil_img = _tensor_to_pil(image_plan)

        # Hash para cache
        img_hash = hashlib.md5(
            pil_img.tobytes()[:4096]  # solo primeros bytes para speed
        ).hexdigest()[:12]

        temp_dir = folder_paths.get_temp_directory()
        filename = f"floorplan_preview_{img_hash}.png"
        filepath = os.path.join(temp_dir, filename)

        if not os.path.exists(filepath):
            # Resize for preview (max 1024px)
            preview = pil_img.copy()
            preview.thumbnail((1024, 1024), Image.LANCZOS)
            preview.save(filepath)

        return {
            "ui": {
                "images": [{
                    "filename": filename,
                    "subfolder": "",
                    "type": "temp"
                }]
            },
            "result": (prompt, camera_info)
        }

    @classmethod
    def IS_CHANGED(cls, image_plan, cam_x, cam_y, cam_rotation, **kwargs):
        """Force re-execution when camera position/rotation changes."""
        return f"{cam_x:.4f}_{cam_y:.4f}_{cam_rotation:.2f}"


# ─────────────────────────────────────────────────────────────
# Registration
# ─────────────────────────────────────────────────────────────

NODE_CLASS_MAPPINGS = {
    "FloorPlanCameraNode": FloorPlanCameraNode,
    "MaterialRefNode": MaterialRefNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FloorPlanCameraNode": "FloorPlan Camera 📐",
    "MaterialRefNode": "Material Reference 🧱",
}
