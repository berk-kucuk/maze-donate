"""Monochrome line glyphs for the chrome (title bar, banners, buttons).

Drawn here as tiny SVGs on a 24-unit grid with one stroke weight, so every
glyph matches and recolours cleanly; no icon theme is consulted, because a
user's Breeze/Papirus colours would break the black-and-white look.
"""
from __future__ import annotations

from functools import lru_cache

from PyQt6.QtCore import QByteArray, QRectF, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

_PATHS: dict[str, str] = {
    "heart": '<path d="M12 20s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 7.4a4.3 4.3 0 0 1 7.5 2.4C19.5 15.4 12 20 12 20Z"/>',
    "shield_ok": '<path d="M12 3 19 6v5.5c0 4.4-3 8-7 9.5-4-1.5-7-5.1-7-9.5V6Z"/><path d="m9 12 2 2 4-4"/>',
    "shield_bad": '<path d="M12 3 19 6v5.5c0 4.4-3 8-7 9.5-4-1.5-7-5.1-7-9.5V6Z"/><path d="M12 8.5v4.5M12 16h.01"/>',
    "point": '<path d="M5 12h13M13 7l5 5-5 5"/>',
    "check": '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    "refresh": '<path d="M19.5 10.5A7.5 7.5 0 0 0 6 7.2L4.5 9"/><path d="M4.5 4.5V9H9"/>'
               '<path d="M4.5 13.5A7.5 7.5 0 0 0 18 16.8l1.5-1.8"/><path d="M19.5 19.5V15H15"/>',
    "doc": '<path d="M14 3.5H7A2 2 0 0 0 5 5.5v13a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-10Z"/><path d="M14 3.5v5h5M8.5 13h7M8.5 16.5h5"/>',
    "external": '<path d="M14 4h6v6M20 4l-8.5 8.5"/><path d="M18 14v4.5a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 4 18.5v-11A1.5 1.5 0 0 1 5.5 6H10"/>',
    "copy": '<rect x="8.5" y="8.5" width="11.5" height="11.5" rx="2.2"/><path d="M15.5 8.5V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v7.5a2 2 0 0 0 2 2h2.5"/>',
    "wallet": '<path d="M18 7.5V6a2 2 0 0 0-2-2H6a2.5 2.5 0 0 0 0 5h13a1.5 1.5 0 0 1 1.5 1.5v8A1.5 1.5 0 0 1 19 20H6a2.5 2.5 0 0 1-2.5-2.5v-11"/><path d="M16.5 14.5h.01"/>',
    "win_min": '<path d="M6.5 12h11"/>',
    "win_max": '<rect x="6.5" y="6.5" width="11" height="11" rx="1"/>',
    "win_restore": '<rect x="5.5" y="8.5" width="10" height="10" rx="1"/><path d="M8.5 8.5V6.5a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1h-2"/>',
    "win_close": '<path d="m6.5 6.5 11 11M17.5 6.5l-11 11"/>',
}


@lru_cache(maxsize=128)
def glyph_pixmap(name: str, size: int, color: str = "#f2f2f4", dpr: float = 2.0) -> QPixmap:
    body = _PATHS[name]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
           f'stroke="{color}" stroke-width="1.7" stroke-linecap="round" '
           f'stroke-linejoin="round">{body}</svg>')
    px = int(size * dpr)
    pm = QPixmap(px, px)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    QSvgRenderer(QByteArray(svg.encode())).render(p, QRectF(0, 0, px, px))
    p.end()
    pm.setDevicePixelRatio(dpr)
    return pm


def glyph(name: str, size: int = 18, color: str = "#f2f2f4") -> QIcon:
    return QIcon(glyph_pixmap(name, size, color))
