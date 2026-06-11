"""
Stimulus — Start Screen
File location: STIMULUS/ui/startscreen.py
Assets expected at: STIMULUS/assets/
"""

import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QPixmap, QFont, QPainter,
    QLinearGradient, QRadialGradient, QColor
)

# ─── PATHS ──────────────────────────────────────────────────
# startscreen.py is inside /ui/, so assets is one level up
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_DIR  = os.path.join(BASE_DIR, "assets")
DATA_DIR   = os.path.join(BASE_DIR, "data")

BG_PATH    = os.path.join(ASSET_DIR, "background_room.png")
EVE_PATH   = os.path.join(ASSET_DIR, "eve_sitting.png")
LOGO_PATH  = os.path.join(ASSET_DIR, "title_logo.png")
SAVE_PATH  = os.path.join(DATA_DIR,  "save.json")

W, H = 900, 660


# ─── OVERLAY ────────────────────────────────────────────────
class Overlay(QWidget):
    """Vignette + bottom gradient for readability."""
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setGeometry(0, 0, W, H)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # Vignette
        vignette = QRadialGradient(W / 2, H / 2, W * 0.72)
        vignette.setColorAt(0, QColor(0, 0, 0, 0))
        vignette.setColorAt(1, QColor(0, 0, 0, 150))
        p.fillRect(0, 0, W, H, vignette)

        # Bottom dark band so buttons are readable
        bottom = QLinearGradient(0, H * 0.52, 0, H)
        bottom.setColorAt(0, QColor(0, 0, 0, 0))
        bottom.setColorAt(1, QColor(18, 8, 2, 200))
        p.fillRect(0, int(H * 0.52), W, H, bottom)
        p.end()


# ─── BUTTON ─────────────────────────────────────────────────
class StyledButton(QPushButton):
    def __init__(self, text, primary=True, parent=None):
        super().__init__(text, parent)
        self.primary = primary
        self.setCursor(Qt.PointingHandCursor)
        self._style(False)

    def _style(self, hovered):
        if self.primary:
            bg = "#A06040" if hovered else "#8B5030"
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {bg};
                    color: #FFF0D0;
                    border: 1.5px solid #C47040;
                    border-radius: 11px;
                    font-family: Georgia;
                    font-size: 15px;
                    letter-spacing: 1px;
                    padding: 0px;
                }}
            """)
        else:
            bg = "#3A2010" if hovered else "transparent"
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {bg};
                    color: #C4A070;
                    border: 1px solid #6B4020;
                    border-radius: 9px;
                    font-family: Georgia;
                    font-size: 12px;
                    letter-spacing: 1px;
                    padding: 0px;
                }}
            """)

    def enterEvent(self, e):
        self._style(True)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._style(False)
        super().leaveEvent(e)


# ─── START SCREEN ────────────────────────────────────────────
class StartScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stimulus")
        self.setFixedSize(W, H)
        self._build()
        self._fade_in()

    def _build(self):
        root = QWidget()
        self.setCentralWidget(root)
        root.setStyleSheet("background: #1C1208;")

        # ── Background ──────────────────────────────────────
        bg = QLabel(root)
        if os.path.exists(BG_PATH):
            pix = QPixmap(BG_PATH).scaled(
                W, H,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            # Crop to centre if image is wider/taller
            x_off = (pix.width()  - W) // 2
            y_off = (pix.height() - H) // 2
            bg.setPixmap(pix.copy(x_off, y_off, W, H))
        else:
            print(f"[!] background_room.png not found at {BG_PATH}")
            bg.setStyleSheet("background: #1C1208;")
        bg.setGeometry(0, 0, W, H)

        # ── Overlay ─────────────────────────────────────────
        Overlay(root)

        # # ── Eve ─────────────────────────────────────────────
        # if os.path.exists(EVE_PATH):
        #     eve = QLabel(root)
        #     eve_pix = QPixmap(EVE_PATH).scaled(
        #         200, 280,
        #         Qt.KeepAspectRatio,
        #         Qt.SmoothTransformation
        #     )
        #     eve.setPixmap(eve_pix)
        #     # Position Eve at the desk area — adjust x/y to taste
        #     eve.setGeometry(W // 2 - 100, H - 320, 200, 280)
        #     eve.setStyleSheet("background: transparent;")
        # else:
        #     print(f"[!] eve_sitting.png not found at {EVE_PATH}")

        # ── Title ───────────────────────────────────────────
        if os.path.exists(LOGO_PATH):
            logo = QLabel(root)
            logo_pix = QPixmap(LOGO_PATH).scaled(
                400, 120,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            logo.setPixmap(logo_pix)
            logo.setGeometry(W // 2 - 200, 38, 400, 120)
            logo.setStyleSheet("background: transparent;")
        else:
            print(f"[!] title_logo.png not found at {LOGO_PATH}")
            title = QLabel("Stimulus", root)
            title.setFont(QFont("Georgia", 52, 700))
            title.setAlignment(Qt.AlignCenter)
            title.setStyleSheet("color: #F0D590; background: transparent; letter-spacing: 6px;")
            title.setGeometry(W // 2 - 220, 38, 440, 110)

        # Subtitle
        sub = QLabel("a letter is waiting for you.", root)
        sub.setFont(QFont("Georgia", 13, -1, True))
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #C4A070; background: transparent;")
        sub.setGeometry(W // 2 - 200, 162, 400, 30)

        # ── Buttons ─────────────────────────────────────────
        self.start_btn = StyledButton("Begin Eve's Story", primary=True, parent=root)
        self.start_btn.setGeometry(W // 2 - 130, H - 148, 260, 52)
        self.start_btn.clicked.connect(self._on_start)

        self.cont_btn = StyledButton("Continue", primary=False, parent=root)
        self.cont_btn.setGeometry(W // 2 - 80, H - 82, 160, 38)
        self.cont_btn.clicked.connect(self._on_continue)
        self.cont_btn.setVisible(os.path.exists(SAVE_PATH))

        # Version tag
        ver = QLabel("v0.1  ·  Wren", root)
        ver.setFont(QFont("Georgia", 9))
        ver.setStyleSheet("color: #5A3418; background: transparent;")
        ver.setGeometry(W - 115, H - 22, 110, 18)

    # ── Fade in ─────────────────────────────────────────────
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

    # ── Button actions ───────────────────────────────────────
    def _on_start(self):
        print("New game started.")
        # Uncomment when letter screen is ready:
        # from ui.letter_screen import LetterScreen
        # self.next = LetterScreen()
        # self.next.show()
        # self.close()

    def _on_continue(self):
        print("Continuing saved game.")
        # Uncomment when letter screen is ready:
        # from ui.letter_screen import LetterScreen
        # self.next = LetterScreen(load_save=True)
        # self.next.show()
        # self.close()


# ─── RUN ────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    screen = StartScreen()
    screen.show()
    sys.exit(app.exec())