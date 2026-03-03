"""
ComfyUI FloorPlan Camera — Architectural Visualization Suite
Interactive 2D camera placement + architectural prompt enrichment nodes.
"""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
from .architectural_nodes import (
    ARCH_NODE_CLASS_MAPPINGS,
    ARCH_NODE_DISPLAY_NAME_MAPPINGS,
)

# Merge all node registrations
NODE_CLASS_MAPPINGS.update(ARCH_NODE_CLASS_MAPPINGS)
NODE_DISPLAY_NAME_MAPPINGS.update(ARCH_NODE_DISPLAY_NAME_MAPPINGS)

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
