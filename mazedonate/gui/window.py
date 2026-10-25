"""Main window: the donate page, built only from a verified signed file.

Frameless with its own 50px title bar, like Maze Store, Maze Guard and Maze
Cloak: the header drags the window (startSystemMove, so it works on Wayland),
double-click maximises, and the edges resize it.

If the signed file does not verify, no card is built at all — the page says
why and points to the website. There is no "show anyway".
"""
from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import QEvent, QObject, QSize, QTimer, Qt, QUrl
from PyQt6.QtGui import QCursor, QDesktopServices, QKeySequence, QShortcut
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PyQt6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow,
                             QPushButton, QScrollArea, QVBoxLayout, QWidget)

from mazedonate import __version__
from mazedonate.core import addresses
from mazedonate.core.addresses import Signed, VerifyError
from mazedonate.gui.flow import FlowLayout
from mazedonate.gui.glass import GlassBackground, GlassFrame
from mazedonate.gui.glyphs import glyph, glyph_pixmap
from mazedonate.gui.i18n import t
from mazedonate.gui.icons import app_logo, logo_pixmap
from mazedonate.gui.pill import Pill
from mazedonate.gui.qr import QrLabel

_RESIZE_MARGIN = 6
_CONTENT_W = 1000


def label(text: str, name: str, wrap: bool = False) -> QLabel:
    lb = QLabel(text)
    lb.setObjectName(name)
    lb.setWordWrap(wrap)
    return lb


def _grouped(addr: str) -> str:
    """Groups of four, so two copies can be compared at a glance."""
    return " ".join(addr[i:i + 4] for i in range(0, len(addr), 4))


def _why(e: VerifyError) -> str:
    key = f"why_{e.reason}"
    text = t(key)
    return e.reason if text == key else text


class TitleBar(QWidget):
    """Draggable header. startSystemMove() is what makes this work on Wayland."""

    def __init__(self, window: QMainWindow):
        super().__init__(objectName="header")
        self._window = window
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self._window.windowHandle()
            if handle:
                handle.startSystemMove()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._window.showNormal() if self._window.isMaximized() else self._window.showMaximized()
        super().mouseDoubleClickEvent(event)


class WindowButton(QPushButton):
    """─ □ ✕ as drawn glyphs; the close button inverts to black on white."""

    def __init__(self, kind: str, tooltip: str):
        super().__init__(objectName="win_close" if kind == "win_close" else "win_btn")
        self._kind = kind
        self.setToolTip(tooltip)
        self.setIconSize(QSize(16, 16))
        self._paint(False)

    def set_kind(self, kind: str) -> None:
        self._kind = kind
        self._paint(self.underMouse())

    def _paint(self, hover: bool) -> None:
        colour = "#000000" if hover and self._kind == "win_close" else (
            "#f2f2f4" if hover else "#9a9aa0")
        self.setIcon(glyph(self._kind, 16, colour))

    def enterEvent(self, ev) -> None:
        self._paint(True)
        super().enterEvent(ev)

    def leaveEvent(self, ev) -> None:
        self._paint(False)
        super().leaveEvent(ev)


class _EdgeResizer(QObject):
    """Resize a frameless window from its edges (see Maze Store)."""

    def __init__(self, window: QMainWindow):
        super().__init__(window)
        self._w = window
        self._cursor_set = False

    def _edges(self, gpos) -> Qt.Edge:
        if self._w.isMaximized() or self._w.isFullScreen():
            return Qt.Edge(0)
        r = self._w.frameGeometry()
        m = _RESIZE_MARGIN
        e = Qt.Edge(0)
        if gpos.x() - r.left() < m:
            e |= Qt.Edge.LeftEdge
        if r.right() - gpos.x() < m:
            e |= Qt.Edge.RightEdge
        if gpos.y() - r.top() < m:
            e |= Qt.Edge.TopEdge
        if r.bottom() - gpos.y() < m:
            e |= Qt.Edge.BottomEdge
        return e

    @staticmethod
    def _shape(e: Qt.Edge) -> Qt.CursorShape | None:
        L, R, T, B = Qt.Edge.LeftEdge, Qt.Edge.RightEdge, Qt.Edge.TopEdge, Qt.Edge.BottomEdge
        if e in (L | T, R | B):
            return Qt.CursorShape.SizeFDiagCursor
        if e in (R | T, L | B):
            return Qt.CursorShape.SizeBDiagCursor
        if e & (L | R):
            return Qt.CursorShape.SizeHorCursor
        if e & (T | B):
            return Qt.CursorShape.SizeVerCursor
        return None

    def eventFilter(self, obj, ev) -> bool:
        t_ = ev.type()
        if t_ not in (QEvent.Type.MouseMove, QEvent.Type.MouseButtonPress, QEvent.Type.HoverMove):
            return False
        if not isinstance(obj, QWidget) or obj.window() is not self._w:
            return False
        gpos = QCursor.pos()
        edges = self._edges(gpos)
        shape = self._shape(edges)
        if t_ == QEvent.Type.MouseButtonPress and shape is not None \
                and ev.button() == Qt.MouseButton.LeftButton:
            handle = self._w.windowHandle()
            if handle and handle.startSystemResize(edges):
                return True
        if shape is not None:
            if not self._cursor_set:
                QApplication.setOverrideCursor(shape)
                self._cursor_set = True
            else:
                QApplication.changeOverrideCursor(shape)
        elif self._cursor_set:
            QApplication.restoreOverrideCursor()
            self._cursor_set = False
        return False


class CopyButton(QPushButton):
    """Copies a fixed value and says so for two seconds."""

    def __init__(self, text: str, value: str, primary: bool = True):
        super().__init__(text, objectName="get" if primary else "secondary")
        self._text = text
        self._value = value
        self._primary = primary
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setIconSize(QSize(15, 15))
        self._set_icon("copy")
        self._reset = QTimer(self, singleShot=True, interval=2000)
        self._reset.timeout.connect(self._restore)
        self.clicked.connect(self._copy)

    def _set_icon(self, name: str) -> None:
        self.setIcon(glyph(name, 15, "#000000" if self._primary else "#f2f2f4"))

    def _copy(self) -> None:
        QApplication.clipboard().setText(self._value)
        if self._text:
            self.setText(t("btn_copied"))
        self._set_icon("check")
        self._reset.start()

    def _restore(self) -> None:
        self.setText(self._text)
        self._set_icon("copy")


class DonateCard(GlassFrame):
    def __init__(self, title: str, pill: tuple[str, str], note: str, qr_data: str,
                 shown: str, copy_text: str, copy_value: str,
                 open_text: str, open_url: str, open_icon: str):
        super().__init__(radius=18)
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 18, 20, 20)
        v.setSpacing(12)

        head = QHBoxLayout()
        head.setSpacing(10)
        head.addWidget(label(title, "card_title"))
        head.addStretch(1)
        head.addWidget(Pill(pill[0], pill[1]))
        v.addLayout(head)
        v.addWidget(label(note, "tagline", wrap=True))

        qr = QrLabel(qr_data, 196)
        qr.setToolTip(qr_data)
        v.addWidget(qr, 0, Qt.AlignmentFlag.AlignHCenter)

        addr = label(shown, "address", wrap=True)
        # Not selectable: a drag-select would copy the spaces between the
        # groups. The button copies the exact signed value.
        addr.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        v.addWidget(addr)
        v.addStretch(1)

        # Stacked, full width: side by side, the German and Turkish labels
        # do not fit in a 300px card.
        row = QVBoxLayout()
        row.setSpacing(8)
        row.addWidget(CopyButton(copy_text, copy_value))
        opener = QPushButton(open_text, objectName="secondary")
        opener.setIcon(glyph(open_icon, 15))
        opener.setIconSize(QSize(15, 15))
        opener.setCursor(Qt.CursorShape.PointingHandCursor)
        opener.setToolTip(open_url)
        opener.clicked.connect(lambda: _open(open_url, self))
        row.addWidget(opener)
        v.addLayout(row)


def _open(url: str, parent: QWidget) -> None:
    if not QDesktopServices.openUrl(QUrl(url)):
        scheme = url.split(":", 1)[0]
        win = parent.window()
        if isinstance(win, MainWindow):
            win.flash(t("wallet_fail", scheme=scheme))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Maze Donate")
        self.setWindowIcon(app_logo())
        self.resize(1080, 860)
        self.setMinimumSize(820, 560)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setMouseTracking(True)
        self._resizer = _EdgeResizer(self)
        QApplication.instance().installEventFilter(self._resizer)

        self._net = QNetworkAccessManager(self)
        self._reply: QNetworkReply | None = None
        self._signed: Signed | None = None
        self._error: VerifyError | None = None
        self._show_signed = False

        self._build_chrome()
        self._load()
        QShortcut(QKeySequence("Ctrl+Q"), self, activated=self.close)

    # ── chrome ─────────────────────────────────────────────────────────────
    def _build_chrome(self) -> None:
        root = GlassBackground()
        v = QVBoxLayout(root)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        header = TitleBar(self)
        header.setFixedHeight(50)
        h = QHBoxLayout(header)
        h.setContentsMargins(16, 0, 0, 0)
        h.setSpacing(10)
        logo = QLabel()
        logo.setPixmap(logo_pixmap(28))
        h.addWidget(logo)
        h.addWidget(label("MAZE DONATE", "wordmark"))
        h.addStretch(1)
        sep = QFrame(objectName="vline")
        sep.setFixedSize(1, 22)
        h.addWidget(sep)
        self._max_btn = WindowButton("win_max", t("tip_maximize"))
        self._max_btn.clicked.connect(
            lambda: self.showNormal() if self.isMaximized() else self.showMaximized())
        mn = WindowButton("win_min", t("tip_minimize"))
        mn.clicked.connect(self.showMinimized)
        cl = WindowButton("win_close", t("tip_close"))
        cl.clicked.connect(self.close)
        for b in (mn, self._max_btn, cl):
            h.addWidget(b)
        v.addWidget(header)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.viewport().setAutoFillBackground(False)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        v.addWidget(self._scroll, 1)

        footer = QWidget(objectName="footer")
        footer.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        footer.setFixedHeight(30)
        fh = QHBoxLayout(footer)
        fh.setContentsMargins(22, 0, 22, 0)
        self._status = label("", "statusbar")
        fh.addWidget(self._status)
        fh.addStretch(1)
        fh.addWidget(label(f"Maze Donate {__version__}", "statusbar"))
        v.addWidget(footer)

        self.setCentralWidget(root)
        self._flash_timer = QTimer(self, singleShot=True, interval=9000)
        self._flash_timer.timeout.connect(self._update_status)

    def changeEvent(self, ev) -> None:
        if ev.type() == QEvent.Type.WindowStateChange:
            self._max_btn.set_kind("win_restore" if self.isMaximized() else "win_max")
        super().changeEvent(ev)

    # ── data ───────────────────────────────────────────────────────────────
    def _load(self) -> None:
        try:
            self._signed, self._error = addresses.load(), None
        except VerifyError as e:
            self._signed, self._error = None, e
        self._render()

    def flash(self, text: str) -> None:
        self._status.setText(text)
        self._flash_timer.start()

    def _update_status(self) -> None:
        s = self._signed
        if s is None:
            self._status.setText("")
        elif s.source == "updated":
            mtime = datetime.fromtimestamp(addresses.USER_COPY.stat().st_mtime) \
                if addresses.USER_COPY.exists() else None
            self._status.setText(t("src_updated", date=mtime.strftime("%Y-%m-%d") if mtime else "?"))
        else:
            self._status.setText(t("src_bundled"))

    # ── page ───────────────────────────────────────────────────────────────
    def _render(self) -> None:
        y = self._scroll.verticalScrollBar().value()
        page = QWidget()
        outer = QHBoxLayout(page)
        outer.setContentsMargins(24, 24, 24, 28)
        outer.addStretch(1)
        col = QWidget()
        col.setMaximumWidth(_CONTENT_W)
        v = QVBoxLayout(col)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(16)
        outer.addWidget(col, 100)
        outer.addStretch(1)

        v.addWidget(self._hero())
        v.addWidget(self._banner())
        if self._signed is not None:
            cards = QWidget()
            flow = FlowLayout(cards, spacing=16, min_item_width=300)
            for c in self._cards(self._signed):
                flow.addWidget(c)
            v.addWidget(cards)
            tip = label(t("paste_check"), "meta", wrap=True)
            v.addWidget(tip)
            v.addWidget(self._verify_panel(self._signed))
        v.addSpacing(4)
        thanks = label(t("thanks"), "h2_sub")
        thanks.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        v.addWidget(thanks)
        v.addStretch(1)

        self._scroll.setWidget(page)
        QTimer.singleShot(0, lambda: self._scroll.verticalScrollBar().setValue(y))
        self._update_status()

    def _hero(self) -> QFrame:
        hero = GlassFrame(radius=22, tint="#ffffff", strength=1.2)
        h = QHBoxLayout(hero)
        h.setContentsMargins(30, 28, 30, 28)
        h.setSpacing(28)
        txt = QVBoxLayout()
        txt.setSpacing(10)
        txt.addWidget(label(t("eyebrow"), "eyebrow"))
        txt.addWidget(label(t("hero_title"), "hero_title", wrap=True))
        txt.addWidget(label(t("hero_sub"), "hero_sub", wrap=True))
        txt.addSpacing(4)
        for key in ("point_1", "point_2", "point_3"):
            row = QHBoxLayout()
            row.setSpacing(10)
            ic = QLabel()
            ic.setPixmap(glyph_pixmap("point", 15, "#9a9aa0"))
            ic.setFixedWidth(16)
            row.addWidget(ic, 0, Qt.AlignmentFlag.AlignTop)
            row.addWidget(label(t(key), "point", wrap=True), 1)
            txt.addLayout(row)
        txt.addSpacing(2)
        txt.addWidget(label(t("costs"), "meta", wrap=True))
        h.addLayout(txt, 1)
        mark = QLabel()
        mark.setPixmap(logo_pixmap(128))
        h.addWidget(mark, 0, Qt.AlignmentFlag.AlignTop)
        return hero

    def _banner(self) -> QFrame:
        s = self._signed
        ok = s is not None
        box = GlassFrame(radius=16)
        h = QHBoxLayout(box)
        h.setContentsMargins(18, 14, 18, 14)
        h.setSpacing(14)
        ic = QLabel()
        ic.setPixmap(glyph_pixmap("shield_ok" if ok else "shield_bad", 28))
        h.addWidget(ic, 0, Qt.AlignmentFlag.AlignTop)
        txt = QVBoxLayout()
        txt.setSpacing(3)
        txt.addWidget(label(t("ok_title" if ok else "bad_title"), "banner_title"))
        if ok:
            body = t("ok_body", date=s.date or datetime.fromtimestamp(s.sig_time).strftime("%Y-%m-%d"))
            if s.source == "updated":
                body += " " + t("ok_updated")
        else:
            body = t("bad_body", why=_why(self._error))
        txt.addWidget(label(body, "tagline", wrap=True))
        txt.addSpacing(6)
        txt.addWidget(label(t("lbl_key"), "section"))
        fpr = label(addresses.pretty_fingerprint(), "fpr")
        fpr.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        txt.addWidget(fpr)
        h.addLayout(txt, 1)

        btns = QVBoxLayout()
        btns.setSpacing(8)
        if ok:
            self._check_btn = QPushButton(t("btn_check"), objectName="secondary")
            self._check_btn.setIcon(glyph("refresh", 15))
            self._check_btn.setIconSize(QSize(15, 15))
            self._check_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._check_btn.setToolTip(t("check_privacy"))
            self._check_btn.clicked.connect(self._check_remote)
            btns.addWidget(self._check_btn)
        web = QPushButton(t("website"), objectName="ghost")
        web.setIcon(glyph("external", 15, "#bdbdc2"))
        web.setIconSize(QSize(15, 15))
        web.setCursor(Qt.CursorShape.PointingHandCursor)
        web.setToolTip(addresses.WEBSITE_URL)
        web.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(addresses.WEBSITE_URL)))
        btns.addWidget(web)
        btns.addStretch(1)
        h.addLayout(btns)
        return box

    def _cards(self, s: Signed) -> list[DonateCard]:
        sponsors_short = s.sponsors_url.removeprefix("https://")
        return [
            DonateCard("Monero (XMR)", (t("pill_signed"), "update"), t("xmr_note"),
                       f"monero:{s.xmr}", _grouped(s.xmr), t("btn_copy"), s.xmr,
                       t("btn_wallet"), f"monero:{s.xmr}", "wallet"),
            DonateCard("Bitcoin (BTC)", (t("pill_signed"), "update"), t("btc_note"),
                       f"bitcoin:{s.btc}", _grouped(s.btc), t("btn_copy"), s.btc,
                       t("btn_wallet"), f"bitcoin:{s.btc}", "wallet"),
            DonateCard("GitHub Sponsors",
                       (t("pill_signed"), "update") if s.sponsors else (t("pill_card"), "chip"),
                       t("sponsors_note"), s.sponsors_url, sponsors_short,
                       t("btn_copy_link"), s.sponsors_url,
                       t("btn_sponsors"), s.sponsors_url, "external"),
        ]

    def _verify_panel(self, s: Signed) -> QFrame:
        box = GlassFrame(radius=16)
        v = QVBoxLayout(box)
        v.setContentsMargins(20, 16, 20, 18)
        v.setSpacing(10)
        head = QHBoxLayout()
        head.addWidget(label(t("verify_title"), "section"))
        head.addStretch(1)
        toggle = QPushButton(t("btn_hide_signed" if self._show_signed else "btn_show_signed"),
                             objectName="ghost")
        toggle.setIcon(glyph("doc", 15, "#bdbdc2"))
        toggle.setIconSize(QSize(15, 15))
        toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle.clicked.connect(self._toggle_signed)
        head.addWidget(toggle)
        v.addLayout(head)

        def cmd_block(title: str, lines: list[str]) -> None:
            v.addWidget(label(title, "meta", wrap=True))
            row = QHBoxLayout()
            row.setSpacing(8)
            text = "\n".join(lines)
            c = label("\n".join("$ " + ln for ln in lines), "command", wrap=True)
            c.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            row.addWidget(c, 1)
            copy = CopyButton("", text, primary=False)
            copy.setToolTip(t("btn_copy_cmd"))
            row.addWidget(copy, 0, Qt.AlignmentFlag.AlignTop)
            v.addLayout(row)

        cmd_block(t("verify_maze"), [
            f"curl -O {addresses.REMOTE_URL}",
            f"gpgv --keyring {addresses.KEYRING} maze-donate.txt.asc",
        ])
        cmd_block(t("verify_other"), [
            f"curl -O {addresses.REMOTE_URL}",
            f"curl -O {addresses.KEY_URL}",
            "gpg --import mazelinux.gpg",
            f"gpg --fingerprint {addresses.FINGERPRINT}",
            "gpg --verify maze-donate.txt.asc",
        ])

        if self._show_signed:
            signed = label(s.text.strip(), "signed", wrap=False)
            signed.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            sc = QScrollArea()
            sc.setWidget(signed)
            sc.setWidgetResizable(True)
            sc.setFrameShape(QFrame.Shape.NoFrame)
            sc.setFixedHeight(min(signed.sizeHint().height() + 4, 420))
            v.addWidget(sc)
            row = QHBoxLayout()
            row.addStretch(1)
            row.addWidget(CopyButton(t("btn_copy_signed"), s.text, primary=False))
            v.addLayout(row)
        return box

    def _toggle_signed(self) -> None:
        self._show_signed = not self._show_signed
        self._render()

    # ── "Check for new addresses" ──────────────────────────────────────────
    def _check_remote(self) -> None:
        if self._reply is not None:
            return
        self._check_btn.setEnabled(False)
        self._check_btn.setText(t("btn_checking"))
        req = QNetworkRequest(QUrl(addresses.REMOTE_URL))
        req.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
                         QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy)
        req.setTransferTimeout(20_000)
        req.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader, f"maze-donate/{__version__}")
        self._reply = self._net.get(req)

        def _progress(received: int, _total: int) -> None:
            if received > addresses.MAX_BYTES and self._reply is not None:
                self._reply.abort()
        self._reply.downloadProgress.connect(_progress)
        self._reply.finished.connect(self._on_fetched)

    def _on_fetched(self) -> None:
        reply, self._reply = self._reply, None
        if reply is None:
            return
        reply.deleteLater()
        if reply.error() != QNetworkReply.NetworkError.NoError:
            self._done(t("check_fail", why=t("check_net")))
            return
        data = bytes(reply.readAll())
        try:
            self._signed, changed = addresses.accept_update(data, self._signed)
        except VerifyError as e:
            self._done(t("check_fail", why=_why(e)))
            return
        except OSError as e:
            self._done(t("check_fail", why=e.strerror or str(e)))
            return
        if changed:
            self._render()
        self._done(t("check_new" if changed else "check_none"))

    def _done(self, message: str) -> None:
        if self._signed is not None and hasattr(self, "_check_btn"):
            try:
                self._check_btn.setEnabled(True)
                self._check_btn.setText(t("btn_check"))
            except RuntimeError:
                pass  # the page was rebuilt; the new button is already fresh
        self.flash(message)
