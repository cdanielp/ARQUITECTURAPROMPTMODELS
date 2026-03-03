"""
ComfyUI FloorPlan Camera Node
Interactive 2D camera placement on architectural floor plans.
Outputs formatted prompt strings for image generation.
"""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
