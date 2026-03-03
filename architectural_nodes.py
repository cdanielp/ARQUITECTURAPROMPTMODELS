"""
architectural_nodes.py — Nodos deterministas de arquitectura para ComfyUI
==========================================================================
Nodos puros de texto (sin VLM, sin API) que enriquecen prompts arquitectónicos.

4 nodos:
  - LensAndCameraPresetNode    → contexto fotográfico (lente, altura, composición)
  - LightingIntentNode         → estrategia de iluminación
  - ArchNegativePromptNode     → negativos específicos por tipo de espacio
  - ShotPresetsNode            → posiciones predefinidas de cámara

Autor: Prompt Models Studio | cdanielp
"""


# ─────────────────────────────────────────────────────────────
# DATOS — Lens & Camera
# ─────────────────────────────────────────────────────────────

LENS_PRESETS = {
    "architectural_neutral": {
        "label": "Architectural Neutral (24mm)",
        "focal": 24,
        "height": 1.2,
        "prompt": (
            "shot with 24mm wide-angle lens, camera height 1.2m, "
            "corrected vertical lines, architectural photography, "
            "balanced perspective, no distortion"
        ),
    },
    "real_estate_wide": {
        "label": "Real Estate Wide (16mm)",
        "focal": 16,
        "height": 1.1,
        "prompt": (
            "shot with 16mm ultra-wide lens, camera height 1.1m, "
            "real estate photography, spacious feel, "
            "maximized visible area, bright and open"
        ),
    },
    "editorial": {
        "label": "Editorial (35mm)",
        "focal": 35,
        "height": 1.3,
        "prompt": (
            "shot with 35mm lens, camera height 1.3m, "
            "editorial architectural photography, "
            "cinematic composition, shallow depth of field, "
            "magazine quality, curated styling"
        ),
    },
    "hero_shot": {
        "label": "Hero Shot (28mm)",
        "focal": 28,
        "height": 0.9,
        "prompt": (
            "shot with 28mm lens, low camera height 0.9m, "
            "dramatic hero perspective, looking slightly upward, "
            "emphasizing volume and ceiling height, "
            "architectural grandeur"
        ),
    },
    "detail_close": {
        "label": "Detail Close-up (50mm)",
        "focal": 50,
        "height": 1.2,
        "prompt": (
            "shot with 50mm lens, camera height 1.2m, "
            "close-up detail shot, shallow depth of field, "
            "focusing on material textures and craftsmanship, "
            "bokeh background"
        ),
    },
    "birds_eye": {
        "label": "Bird's Eye (24mm overhead)",
        "focal": 24,
        "height": 2.8,
        "prompt": (
            "shot with 24mm lens, elevated camera position 2.8m, "
            "bird's eye perspective, looking downward, "
            "showing floor layout and furniture arrangement, "
            "architectural plan view feel"
        ),
    },
}

# Room-specific lens adjustments
LENS_ROOM_HINTS = {
    "bathroom": "compact space, avoid extreme distortion, keep proportions natural",
    "kitchen": "capture countertops and appliances, show workspace depth",
    "living_room": "emphasize volume and natural light, show full seating area",
    "bedroom": "intimate framing, warm perspective, focus on bed and headboard",
    "dining_room": "center on table, show place settings and lighting fixture",
    "hallway": "use perspective depth, leading lines toward end of corridor",
    "office": "clean lines, organized workspace, monitor and desk visible",
    "exterior": "include context, sky, landscaping, full facade visible",
    "general": "balanced architectural framing",
}


# ─────────────────────────────────────────────────────────────
# DATOS — Lighting
# ─────────────────────────────────────────────────────────────

LIGHTING_PRESETS = {
    "day_soft": {
        "label": "Soft Daylight",
        "prompt": (
            "soft diffused natural daylight, warm color temperature 5500K, "
            "gentle shadows, ambient bounce light from walls, "
            "bright and airy atmosphere, no harsh direct sun"
        ),
    },
    "golden_hour": {
        "label": "Golden Hour",
        "prompt": (
            "golden hour warm sunlight streaming through windows, "
            "long dramatic shadows, warm orange tones 3200K, "
            "volumetric light rays, romantic atmosphere, "
            "highlights on surfaces"
        ),
    },
    "overcast": {
        "label": "Overcast / Cloudy",
        "prompt": (
            "overcast diffused daylight, even illumination, "
            "neutral color temperature 6500K, minimal shadows, "
            "soft ambient light, no direct sunlight, "
            "calm and serene atmosphere"
        ),
    },
    "night_warm": {
        "label": "Night — Warm Artificial",
        "prompt": (
            "nighttime interior with warm artificial lighting, "
            "recessed downlights and accent lamps, "
            "warm color temperature 2700K, cozy ambiance, "
            "pools of light creating depth, "
            "dark windows reflecting interior"
        ),
    },
    "night_cool": {
        "label": "Night — Cool Modern",
        "prompt": (
            "nighttime interior with cool modern lighting, "
            "LED strip lights and indirect illumination, "
            "neutral white 4000K, contemporary atmosphere, "
            "clean crisp shadows, architectural lighting design"
        ),
    },
    "mixed": {
        "label": "Mixed Natural + Artificial",
        "prompt": (
            "mixed natural and artificial lighting, "
            "daylight from windows combined with interior lamps, "
            "balanced exposure, realistic dual light sources, "
            "natural shadows with fill from artificial fixtures"
        ),
    },
    "dramatic": {
        "label": "Dramatic / Moody",
        "prompt": (
            "dramatic directional lighting, strong contrast, "
            "deep shadows and bright highlights, "
            "single dominant light source, chiaroscuro effect, "
            "moody cinematic atmosphere, editorial lighting"
        ),
    },
}

LIGHTING_ROOM_HINTS = {
    "bathroom": "even diffused light, avoid harsh shadows on tiles, emphasize clean surfaces",
    "kitchen": "task lighting on countertops, under-cabinet lights, functional brightness",
    "living_room": "layered lighting, ambient plus accent, emphasize natural light entry",
    "bedroom": "soft intimate lighting, warm tones, bedside accent lights",
    "dining_room": "pendant light over table as focal, dimmed ambient, intimate dinner setting",
    "hallway": "wall-wash lighting, even corridor illumination, guiding perspective",
    "office": "bright functional lighting, minimal glare on screens, neutral white",
    "exterior": "natural sky light, landscape lighting accents, facade wash lights",
    "general": "balanced architectural lighting",
}


# ─────────────────────────────────────────────────────────────
# DATOS — Negative Prompts
# ─────────────────────────────────────────────────────────────

NEGATIVE_BASE = (
    "blurry, low quality, distorted geometry, warped walls, "
    "floating objects, impossible architecture, "
    "plastic looking surfaces, oversaturated colors, "
    "text, watermark, logo, signature, "
    "duplicate furniture, merged objects, "
    "incorrect perspective, broken lines, "
    "unrealistic proportions, toy-like scale"
)

NEGATIVE_BY_ROOM = {
    "bathroom": (
        "dirty, stained tiles, mold, cracked mirror, "
        "oversized bathroom, impossible plumbing, "
        "misaligned tiles, wet floor puddles, "
        "toilet in wrong position, shower without enclosure"
    ),
    "kitchen": (
        "dirty dishes, food waste, cluttered counters, "
        "misaligned cabinets, floating appliances, "
        "impossible countertop spans, merged sink and stove, "
        "cabinet doors at wrong angles, unrealistic backsplash"
    ),
    "living_room": (
        "overcrowded furniture, floating cushions, "
        "walls at wrong angles, impossible ceiling height, "
        "merged sofa and wall, duplicate TV screens, "
        "unrealistic window placement, curtains through walls"
    ),
    "bedroom": (
        "bed floating off floor, merged headboard and wall, "
        "impossible closet depth, duplicate nightstands, "
        "pillow through headboard, unrealistic bed size, "
        "window behind solid wall, broken wardrobe geometry"
    ),
    "dining_room": (
        "floating chairs, table through wall, "
        "duplicate light fixtures, merged table and floor, "
        "impossible chair arrangement, plates floating, "
        "unrealistic table proportions"
    ),
    "hallway": (
        "impossible corridor length, doors through walls, "
        "merged door frames, inconsistent floor pattern, "
        "hallway wider than room, broken perspective lines"
    ),
    "office": (
        "floating monitors, merged desk and wall, "
        "duplicate keyboards, impossible cable routing, "
        "chair through desk, unrealistic screen content"
    ),
    "exterior": (
        "floating building, impossible structural cantilever, "
        "trees through walls, merged building and ground, "
        "unrealistic sky, building at wrong scale, "
        "impossible window arrangement, vegetation through structure"
    ),
    "general": (
        "deformed furniture, impossible room geometry, "
        "merged objects, floating items, broken perspective"
    ),
}

NEGATIVE_BY_ENGINE = {
    "qwen_edit": (
        "artifacts from inpainting, seam lines, "
        "color banding at edit boundaries, "
        "resolution mismatch, ghosting from source image"
    ),
    "flux": (
        "flat lighting, posterization, "
        "anatomy errors if people present, "
        "text artifacts embedded in image"
    ),
    "sdxl": (
        "overcooked details, deep-fried look, "
        "plastic skin if people present, "
        "VAE color shift, orange tint"
    ),
    "general": "",
}


# ─────────────────────────────────────────────────────────────
# DATOS — Shot Presets
# ─────────────────────────────────────────────────────────────

SHOT_PRESETS = {
    "living_room": {
        "desde_acceso": {
            "label": "Sala → Desde acceso",
            "cam_x": 0.5, "cam_y": 0.85, "cam_rotation": 0.0,
            "description": "Vista clásica entrando a la sala",
        },
        "hacia_ventana": {
            "label": "Sala → Hacia ventana",
            "cam_x": 0.4, "cam_y": 0.6, "cam_rotation": 0.0,
            "description": "Vista hacia la luz natural",
        },
        "esquina_diagonal": {
            "label": "Sala → Esquina diagonal",
            "cam_x": 0.15, "cam_y": 0.8, "cam_rotation": 35.0,
            "description": "Diagonal mostrando profundidad",
        },
        "hacia_comedor": {
            "label": "Sala → Hacia comedor",
            "cam_x": 0.3, "cam_y": 0.5, "cam_rotation": 90.0,
            "description": "Vista de sala-comedor integrado",
        },
    },
    "kitchen": {
        "hacia_isla": {
            "label": "Cocina → Hacia isla",
            "cam_x": 0.5, "cam_y": 0.8, "cam_rotation": 0.0,
            "description": "Vista frontal de la isla o barra",
        },
        "desde_barra": {
            "label": "Cocina → Desde barra",
            "cam_x": 0.5, "cam_y": 0.2, "cam_rotation": 180.0,
            "description": "Vista de cocina desde la barra",
        },
        "esquina_trabajo": {
            "label": "Cocina → Zona de trabajo",
            "cam_x": 0.2, "cam_y": 0.7, "cam_rotation": 20.0,
            "description": "Mostrando área de preparación",
        },
    },
    "bedroom": {
        "hacia_cabecera": {
            "label": "Recámara → Hacia cabecera",
            "cam_x": 0.5, "cam_y": 0.8, "cam_rotation": 0.0,
            "description": "Vista clásica hacia la cama",
        },
        "desde_cama": {
            "label": "Recámara → Desde cama",
            "cam_x": 0.5, "cam_y": 0.2, "cam_rotation": 180.0,
            "description": "Vista desde la cabecera",
        },
        "hacia_closet": {
            "label": "Recámara → Hacia closet",
            "cam_x": 0.3, "cam_y": 0.5, "cam_rotation": 270.0,
            "description": "Vista hacia el área de closet",
        },
    },
    "bathroom": {
        "hacia_lavabo": {
            "label": "Baño → Hacia lavabo/espejo",
            "cam_x": 0.5, "cam_y": 0.7, "cam_rotation": 0.0,
            "description": "Vista frontal del mueble de baño",
        },
        "hacia_regadera": {
            "label": "Baño → Hacia regadera",
            "cam_x": 0.5, "cam_y": 0.3, "cam_rotation": 180.0,
            "description": "Vista hacia la zona húmeda",
        },
        "general": {
            "label": "Baño → Vista general",
            "cam_x": 0.2, "cam_y": 0.8, "cam_rotation": 25.0,
            "description": "Vista diagonal mostrando todo el baño",
        },
    },
    "dining_room": {
        "hacia_mesa": {
            "label": "Comedor → Hacia mesa",
            "cam_x": 0.5, "cam_y": 0.8, "cam_rotation": 0.0,
            "description": "Vista frontal de la mesa",
        },
        "desde_cabecera": {
            "label": "Comedor → Desde cabecera mesa",
            "cam_x": 0.5, "cam_y": 0.3, "cam_rotation": 180.0,
            "description": "Perspectiva de comensal principal",
        },
    },
    "exterior": {
        "fachada_frontal": {
            "label": "Exterior → Fachada frontal",
            "cam_x": 0.5, "cam_y": 0.9, "cam_rotation": 0.0,
            "description": "Vista frontal de fachada",
        },
        "tres_cuartos": {
            "label": "Exterior → Vista 3/4",
            "cam_x": 0.2, "cam_y": 0.85, "cam_rotation": 30.0,
            "description": "Ángulo 3/4 clásico de arquitectura",
        },
        "jardin": {
            "label": "Exterior → Desde jardín",
            "cam_x": 0.5, "cam_y": 0.1, "cam_rotation": 180.0,
            "description": "Vista posterior desde el jardín",
        },
    },
}


# ─────────────────────────────────────────────────────────────
# NODO 1: LensAndCameraPresetNode
# ─────────────────────────────────────────────────────────────

class LensAndCameraPresetNode:
    """Genera contexto fotográfico: tipo de lente, altura, composición."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "preset": (list(LENS_PRESETS.keys()), {
                    "default": "architectural_neutral",
                }),
                "room_type": (list(LENS_ROOM_HINTS.keys()), {
                    "default": "general",
                }),
            },
        }

    RETURN_TYPES = ("STRING", "FLOAT", "INT")
    RETURN_NAMES = ("lens_prompt", "cam_height", "focal_mm")
    FUNCTION = "generate"
    CATEGORY = "FloorPlan/Architecture"

    def generate(self, preset, room_type):
        data = LENS_PRESETS[preset]
        room_hint = LENS_ROOM_HINTS.get(room_type, LENS_ROOM_HINTS["general"])
        prompt = f"{data['prompt']}, {room_hint}"
        return (prompt, data["height"], data["focal"])


# ─────────────────────────────────────────────────────────────
# NODO 2: LightingIntentNode
# ─────────────────────────────────────────────────────────────

class LightingIntentNode:
    """Define estrategia de iluminación para el render."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mood": (list(LIGHTING_PRESETS.keys()), {
                    "default": "day_soft",
                }),
                "room_type": (list(LIGHTING_ROOM_HINTS.keys()), {
                    "default": "general",
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("lighting_prompt",)
    FUNCTION = "generate"
    CATEGORY = "FloorPlan/Architecture"

    def generate(self, mood, room_type):
        data = LIGHTING_PRESETS[mood]
        room_hint = LIGHTING_ROOM_HINTS.get(room_type, LIGHTING_ROOM_HINTS["general"])
        prompt = f"{data['prompt']}, {room_hint}"
        return (prompt,)


# ─────────────────────────────────────────────────────────────
# NODO 3: ArchNegativePromptNode
# ─────────────────────────────────────────────────────────────

class ArchNegativePromptNode:
    """Genera prompts negativos específicos para renders arquitectónicos."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "room_type": (list(NEGATIVE_BY_ROOM.keys()), {
                    "default": "general",
                }),
                "render_engine": (list(NEGATIVE_BY_ENGINE.keys()), {
                    "default": "qwen_edit",
                }),
            },
            "optional": {
                "extra_negative": ("STRING", {
                    "default": "",
                    "multiline": False,
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("negative_prompt",)
    FUNCTION = "generate"
    CATEGORY = "FloorPlan/Architecture"

    def generate(self, room_type, render_engine, extra_negative=""):
        parts = [NEGATIVE_BASE]
        room_neg = NEGATIVE_BY_ROOM.get(room_type, "")
        if room_neg:
            parts.append(room_neg)
        engine_neg = NEGATIVE_BY_ENGINE.get(render_engine, "")
        if engine_neg:
            parts.append(engine_neg)
        if extra_negative and extra_negative.strip():
            parts.append(extra_negative.strip())
        return (", ".join(parts),)


# ─────────────────────────────────────────────────────────────
# NODO 4: ShotPresetsNode
# ─────────────────────────────────────────────────────────────

class ShotPresetsNode:
    """Posiciones predefinidas de cámara por tipo de espacio."""

    @classmethod
    def INPUT_TYPES(cls):
        # Build flat list of all shot labels
        all_shots = []
        for room, shots in SHOT_PRESETS.items():
            for shot_key, shot_data in shots.items():
                all_shots.append(shot_data["label"])
        return {
            "required": {
                "shot": (all_shots, {
                    "default": all_shots[0],
                }),
            },
        }

    RETURN_TYPES = ("FLOAT", "FLOAT", "FLOAT", "STRING", "STRING")
    RETURN_NAMES = ("cam_x", "cam_y", "cam_rotation", "room_type", "description")
    FUNCTION = "get_preset"
    CATEGORY = "FloorPlan/Architecture"

    def get_preset(self, shot):
        for room_type, shots in SHOT_PRESETS.items():
            for shot_key, shot_data in shots.items():
                if shot_data["label"] == shot:
                    return (
                        shot_data["cam_x"],
                        shot_data["cam_y"],
                        shot_data["cam_rotation"],
                        room_type,
                        shot_data["description"],
                    )
        # Fallback
        return (0.5, 0.5, 0.0, "general", "Default center position")


# ─────────────────────────────────────────────────────────────
# NODO 5: PromptCombinerNode (utilidad)
# ─────────────────────────────────────────────────────────────

class ArchPromptCombinerNode:
    """
    Combina el prompt base de FloorPlan Camera con los prompts
    de Lens, Lighting y opcionalmente VLM response.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "camera_prompt": ("STRING", {
                    "multiline": True, "forceInput": True,
                }),
            },
            "optional": {
                "lens_prompt": ("STRING", {
                    "multiline": True, "forceInput": True,
                }),
                "lighting_prompt": ("STRING", {
                    "multiline": True, "forceInput": True,
                }),
                "vlm_description": ("STRING", {
                    "multiline": True, "forceInput": True,
                }),
                "style_text": ("STRING", {
                    "default": "",
                    "multiline": False,
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("combined_prompt",)
    FUNCTION = "combine"
    CATEGORY = "FloorPlan/Architecture"

    def combine(self, camera_prompt, lens_prompt="", lighting_prompt="",
                vlm_description="", style_text=""):
        parts = []

        # If VLM gave us a real description, use it as the base
        if vlm_description and vlm_description.strip():
            parts.append(vlm_description.strip())
            # Still add camera angles from the original prompt
            parts.append(camera_prompt)
        else:
            parts.append(camera_prompt)

        if lens_prompt and lens_prompt.strip():
            parts.append(lens_prompt.strip())

        if lighting_prompt and lighting_prompt.strip():
            parts.append(lighting_prompt.strip())

        if style_text and style_text.strip():
            parts.append(style_text.strip())

        return (", ".join(parts),)


# ─────────────────────────────────────────────────────────────
# Registros
# ─────────────────────────────────────────────────────────────

ARCH_NODE_CLASS_MAPPINGS = {
    "LensAndCameraPresetNode": LensAndCameraPresetNode,
    "LightingIntentNode": LightingIntentNode,
    "ArchNegativePromptNode": ArchNegativePromptNode,
    "ShotPresetsNode": ShotPresetsNode,
    "ArchPromptCombinerNode": ArchPromptCombinerNode,
}

ARCH_NODE_DISPLAY_NAME_MAPPINGS = {
    "LensAndCameraPresetNode": "Lens & Camera Preset 📷",
    "LightingIntentNode": "Lighting Intent 💡",
    "ArchNegativePromptNode": "Arch Negative Prompt 🚫",
    "ShotPresetsNode": "Shot Presets 🎯",
    "ArchPromptCombinerNode": "Arch Prompt Combiner 🔗",
}
