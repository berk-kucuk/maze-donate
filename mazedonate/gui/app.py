"""Entry point. Single instance per user, like the other Maze apps."""
from __future__ import annotations

import os
import sys

from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import QApplication

from mazedonate.gui.i18n import set_language
from mazedonate.gui.icons import app_logo
from mazedonate.gui.theme import stylesheet
from mazedonate.gui.window import MainWindow

_RUNTIME_DIR = os.environ.get("XDG_RUNTIME_DIR", "")
_SINGLETON = (os.path.join(_RUNTIME_DIR, "maze-donate-singleton")
              if _RUNTIME_DIR and os.path.isdir(_RUNTIME_DIR)
              else f"maze-donate-singleton-{os.getuid()}")


def _activate_running_instance() -> bool:
    sock = QLocalSocket()
    sock.connectToServer(_SINGLETON)
    if sock.waitForConnected(300):
        sock.write(b"show")
        sock.flush()
        sock.waitForBytesWritten(300)
        sock.disconnectFromServer()
        return True
    return False


def run() -> int:
    for arg in sys.argv[1:]:
        if arg.startswith("--lang="):
            set_language(arg.split("=", 1)[1])

    app = QApplication(sys.argv)
    app.setApplicationName("Maze Donate")
    app.setApplicationDisplayName("Maze Donate")
    app.setOrganizationName("maze")
    app.setDesktopFileName("maze-donate")
    app.setWindowIcon(app_logo())

    if _activate_running_instance():
        return 0
    QLocalServer.removeServer(_SINGLETON)
    singleton = QLocalServer()
    singleton.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
    singleton.listen(_SINGLETON)

    app.setStyleSheet(stylesheet())
    window = MainWindow()

    def _raise() -> None:
        conn = singleton.nextPendingConnection()
        if conn is not None:
            conn.disconnectFromServer()
        window.showNormal()
        window.raise_()
        window.activateWindow()
    singleton.newConnection.connect(_raise)

    window.show()
    return app.exec()
