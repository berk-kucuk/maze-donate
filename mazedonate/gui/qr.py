"""QR codes, drawn from the module matrix with QPainter.

`qrcode` (python-qrcode, already in maze-python) only builds the matrix here;
no Pillow image is made. The code is dark on a white tile with the full quiet
zone, because that is what every phone wallet scans reliably — an inverted
code would match the black window better and fail on half the scanners.
"""
from __future__ import annotations

from functools import lru_cache

import qrcode
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import QLabel, QWidget


@lru_cache(maxsize=16)
def _matrix(data: str) -> tuple[tuple[bool, ...], ...]:
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=4)
    q.add_data(data)
    q.make(fit=True)
    return tuple(tuple(row) for row in q.get_matrix())


def qr_pixmap(data: str, size: int, dpr: float = 2.0) -> QPixmap:
    m = _matrix(data)
    n = len(m)
    px = int(size * dpr)
    pm = QPixmap(px, px)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    tile = QPainterPath()
    tile.addRoundedRect(QRectF(0, 0, px, px), 14 * dpr, 14 * dpr)
    p.fillPath(tile, QColor("#ffffff"))
    # Whole-pixel modules: fractional ones blur into grey seams on some scanners.
    cell = px // n
    off = (px - cell * n) // 2
    p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
    dark = QColor("#000000")
    for y, row in enumerate(m):
        for x, on in enumerate(row):
            if on:
                p.fillRect(off + x * cell, off + y * cell, cell, cell, dark)
    p.end()
    pm.setDevicePixelRatio(dpr)
    return pm


class QrLabel(QLabel):
    def __init__(self, data: str, size: int, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.set_data(data)

    def set_data(self, data: str) -> None:
        dpr = max(2.0, self.devicePixelRatioF())
        self.setPixmap(qr_pixmap(data, self.width(), dpr))
