"""Utility helpers for Netflame integration.

Shared helpers for generating SVG data URIs and related utilities.
"""
from __future__ import annotations

import base64
from typing import Optional


SVG_PATH = (
    "M12 2 C10.5 5 7 8 7 12 "
    "C7 16.4 9.6 20 12 20 "
    "C14.4 20 17 16.4 17 12 "
    "C17 9 14.8 6.5 13.5 4.5 "
    "C13.3 6.5 12.2 8 11 9.5 "
    "C10 11 10.5 13.5 12 15 "
    "C13.5 13.5 14 11 13 9 "
    "C14.8 10.5 16 12.5 16 14.5 "
    "C16 17 14.3 19 12 19 "
    "C9.7 19 8 17 8 14.5 "
    "C8 11 10.5 8 12 2Z"
)


def get_status_color(status: Optional[int]) -> str:
    """Return a color hex string for a given status.

    Mapping is:
    - 0 -> gray (#9e9e9e)
    - 1,2 -> orange (#ff9800)
    - 3 -> red (#ff0000)
    Any unknown -> gray
    """
    if status == 0:
        return "#9e9e9e"
    if status in (1, 2):
        return "#ff9800"
    if status == 3:
        return "#ff0000"
    return "#9e9e9e"


def status_svg_data_uri(status: Optional[int], size: int = 64) -> str:
    """Return a base64-encoded SVG data URI for a given status.

    The SVG uses the shared `SVG_PATH` and sets `fill` to the color mapped
    from the status. `size` controls the width/height of the resulting SVG.
    """
    color = get_status_color(status)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24">'
        f'<path d="{SVG_PATH}" fill="{color}"/>'
        f'</svg>'
    )
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"
