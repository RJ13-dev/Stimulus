"""
Stimulus — Start Screen
File location: STIMULUS/ui/startscreen.py

Takes a `game` reference and calls back into it on button press.
Still runnable standalone (play button) thanks to the path bootstrap;
when run standalone with no game, the buttons just print.
"""

# ── Path bootstrap (project root is two folders up from ui/) ─────────────
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton
)
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import (
    QPixmap, QFont, QPainter, QPainterPath,
    QLinearGradient, QRadialGradient, QColor, QPen, QBrush
)

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_DIR  = os.path.join(BASE_DIR, "assets")
DATA_DIR   = os.path.join(BASE_DIR, "data")

BG_PATH    = os.path.join(ASSET_DIR, "background_room.png")
EVE_PATH   = os.path.join(ASSET_DIR, "eve_sitting.png")
LOGO_PATH  = os.path.join(ASSET_DIR, "title_logo.png")
SAVE_PATH  = os.path.join(DATA_DIR,  "save.json")

W, H = 960, 640


class Overlay(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setGeometry(0, 0, W, H)
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(60)

    def _tick(self):
        self._t += 0.06
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        vignette = QRadialGradient(W / 2, H / 2, W * 0.72)
        vignette.setColorAt(0, QColor(0, 0, 0, 0))
        vignette.setColorAt(0.7, QColor(10, 5, 0, 60))
        vignette.setColorAt(1, QColor(8, 4, 0, 165))
        p.fillRect(0, 0, W, H, vignette)
        glow = QRadialGradient(W / 2, 118, 360)
        glow.setColorAt(0, QColor(40, 26, 10, 150))
        glow.setColorAt(0.5, QColor(30, 18, 6, 80))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillRect(0, 0, W, 260, glow)
        shimmer = 0.5 + 0.5 * math.sin(self._t)
        lamp_alpha = int(40 + 35 * shimmer)
        lamp = QRadialGradient(118, 410, 130)
        lamp.setColorAt(0, QColor(255, 198, 110, lamp_alpha))
        lamp.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillRect(0, 280, 280, 280, lamp)
        bottom = QLinearGradient(0, H * 0.52, 0, H)
        bottom.setColorAt(0, QColor(0, 0, 0, 0))
        bottom.setColorAt(1, QColor(18, 8, 2, 205))
        p.fillRect(0, int(H * 0.52), W, H, bottom)
        p.end()


class StyledButton(QPushButton):
    def __init__(self, text, primary=True, parent=None):
        super().__init__(text, parent)
        self.primary = primary
        self._hovered = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(QFont("Georgia", 15 if primary else 12))

    def enterEvent(self, e):
        self._hovered = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hovered = False
        self.update()
        super().leaveEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(1.5, 1.5, self.width() - 3, self.height() - 3)
        radius = 12 if self.primary else 9
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        if self.primary:
            grad = QLinearGradient(0, rect.top(), 0, rect.bottom())
            if self._hovered:
                grad.setColorAt(0, QColor(178, 112, 72))
                grad.setColorAt(1, QColor(132, 76, 44))
            else:
                grad.setColorAt(0, QColor(150, 90, 56))
                grad.setColorAt(1, QColor(112, 62, 36))
            p.fillPath(path, QBrush(grad))
            p.setPen(QPen(QColor(255, 220, 170, 70), 1.5))
            inner = QRectF(rect.left() + 3, rect.top() + 3, rect.width() - 6, rect.height() - 6)
            ip = QPainterPath()
            ip.addRoundedRect(inner, radius - 3, radius - 3)
            p.drawPath(ip)
            p.setPen(QPen(QColor(196, 112, 64, 230), 1.5))
            p.drawPath(path)
            text_color = QColor(255, 240, 208)
        else:
            if self._hovered:
                p.fillPath(path, QColor(58, 32, 16, 200))
            else:
                p.fillPath(path, QColor(0, 0, 0, 0))
            p.setPen(QPen(QColor(107, 64, 32), 1))
            p.drawPath(path)
            text_color = QColor(196, 160, 112)
        p.setPen(text_color)
        p.setFont(self.font())
        p.drawText(self.rect(), Qt.AlignCenter, self.text())
        p.end()


class StartScreen(QMainWindow):
    def __init__(self, game=None):
        super().__init__()
        self.game = game             # the controller; may be None when standalone
        self.setWindowTitle("Stimulus")
        self.setFixedSize(W, H)
        self._build()
        self._fade_in()

    def _build(self):
        root = QWidget()
        self.setCentralWidget(root)
        root.setStyleSheet("background: #1C1208;")
        bg = QLabel(root)
        if os.path.exists(BG_PATH):
            pix = QPixmap(BG_PATH).scaled(W, H, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x_off = (pix.width() - W) // 2
            y_off = (pix.height() - H) // 2
            bg.setPixmap(pix.copy(x_off, y_off, W, H))
        else:
            print(f"[!] background_room.png not found at {BG_PATH}")
            bg.setStyleSheet("background: #1C1208;")
        bg.setGeometry(0, 0, W, H)
        Overlay(root)
        if os.path.exists(LOGO_PATH):
            logo = QLabel(root)
            logo_pix = QPixmap(LOGO_PATH).scaled(400, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo.setPixmap(logo_pix)
            logo.setGeometry(W // 2 - 200, 30, 400, 120)
            logo.setStyleSheet("background: transparent;")
        else:
            print(f"[!] title_logo.png not found at {LOGO_PATH}")
            title = QLabel("Stimulus", root)
            title.setFont(QFont("Georgia", 52, 700))
            title.setAlignment(Qt.AlignCenter)
            title.setStyleSheet("color: #F0D590; background: transparent; letter-spacing: 6px;")
            title.setGeometry(W // 2 - 220, 30, 440, 110)
        rule = QLabel(root)
        rule.setGeometry(W // 2 - 70, 172, 140, 1)
        rule.setStyleSheet("background: rgba(196, 160, 112, 110);")
        sub = QLabel("a letter is waiting for you.", root)
        sub.setFont(QFont("Georgia", 13, -1, True))
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #D8B888; background: transparent; letter-spacing: 1px;")
        sub.setGeometry(W // 2 - 200, 182, 400, 30)
        self.start_btn = StyledButton("Begin Eve's Story", primary=True, parent=root)
        self.start_btn.setGeometry(W // 2 - 130, H - 148, 260, 54)
        self.start_btn.clicked.connect(self._on_start)
        self.cont_btn = StyledButton("Continue", primary=False, parent=root)
        self.cont_btn.setGeometry(W // 2 - 80, H - 80, 160, 38)
        self.cont_btn.clicked.connect(self._on_continue)
        self.cont_btn.setVisible(os.path.exists(SAVE_PATH))
        ver = QLabel("v0.1  \u00b7  Wren", root)
        ver.setFont(QFont("Georgia", 9))
        ver.setStyleSheet("color: #6B4A28; background: transparent;")
        ver.setGeometry(W - 115, H - 22, 110, 18)

    def _fade_in(self):
        self.setWindowOpacity(0.0)
        self._opacity = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)
        self._timer.start(16)

    def _step(self):
        self._opacity += 0.025
        if self._opacity >= 1.0:
            self._opacity = 1.0
            self._timer.stop()
        self.setWindowOpacity(self._opacity)

    def _on_start(self):
        if self.game is not None:
            self.game.begin_story()   # controller decides what comes next
            self.close()
        else:
            print("New game started. (no game controller — run via maingame.py)")

    def _on_continue(self):
        if self.game is not None:
            self.game.continue_story()
            self.close()
        else:
            print("Continue. (no game controller — run via maingame.py)")


if __name__ == "__main__":
    # Standalone test: no game controller is passed.
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    screen = StartScreen()
    screen.show()
    sys.exit(app.exec())