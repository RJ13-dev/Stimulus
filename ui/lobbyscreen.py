"""
Stimulus — Lobby / Home Screen
File location: STIMULUS/ui/lobbyscreen.py

The attic lobby. Shows Eve sitting in her room with:
  * a top-right wooden coin badge (coins fetched live from Eve)
  * two carved wooden plaque buttons at the bottom:
        Shop          -> opens shop.py        (ShopScreen)
        Get My Letter -> opens letterscreen.py (LetterScreen)

Matches the conventions of startscreen.py: path bootstrap, optional `game`
controller, runnable standalone for visual testing.

Background asset:  STIMULUS/assets/lobby.png
"""

# ── Path bootstrap (project root is two folders up from ui/) ─────────────
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, Signal
from PySide6.QtGui import (
    QPixmap, QFont, QPainter, QPainterPath, QLinearGradient,
    QRadialGradient, QColor, QPen, QBrush
)

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_DIR = os.path.join(BASE_DIR, "assets")
BG_PATH   = os.path.join(ASSET_DIR, "lobby.png")

# lobby.png is wide (≈1.9:1). Use a matching 16:9-ish window.
W, H = 1100, 620


# ─────────────────────────────────────────────────────────────────────────
#  Wooden plaque button  (carved, bevelled, with icon slot + engraved text)
# ─────────────────────────────────────────────────────────────────────────
class WoodenButton(QWidget):
    clicked = Signal()

    def __init__(self, text, icon="", parent=None):
        super().__init__(parent)
        self.text = text
        self.icon = icon
        self._pressed = False
        self._hover = False
        self.setMinimumSize(280, 96)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)

    def enterEvent(self, e):
        self._hover = True; self.update()

    def leaveEvent(self, e):
        self._hover = False; self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._pressed = True; self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self._pressed:
            self._pressed = False; self.update()
            if self.rect().contains(e.position().toPoint()):
                self.clicked.emit()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        w, h = self.width(), self.height()
        sink = 3 if self._pressed else 0
        r = QRectF(8, 8 + sink, w - 16, h - 16 - 3)
        radius = h * 0.30

        # drop shadow
        shadow = QPainterPath()
        shadow.addRoundedRect(r.translated(0, 5 - sink), radius, radius)
        p.fillPath(shadow, QColor(0, 0, 0, 90))

        # dark carved rim
        outer = QPainterPath()
        outer.addRoundedRect(r, radius, radius)
        p.fillPath(outer, QColor(66, 40, 22))

        # wood face
        face = r.adjusted(5, 5, -5, -5)
        face_path = QPainterPath()
        face_path.addRoundedRect(face, radius - 4, radius - 4)
        lighten = 16 if self._hover else 0
        grad = QLinearGradient(face.topLeft(), face.bottomLeft())
        grad.setColorAt(0.0, QColor(184, 130, 78).lighter(100 + lighten))
        grad.setColorAt(0.5, QColor(150, 99, 55).lighter(100 + lighten))
        grad.setColorAt(1.0, QColor(110, 70, 38).lighter(100 + lighten))
        p.fillPath(face_path, QBrush(grad))

        p.save()
        p.setClipPath(face_path)
        # top bevel highlight
        hi = QLinearGradient(face.topLeft(), QPointF(face.left(), face.top() + face.height() * 0.4))
        hi.setColorAt(0.0, QColor(214, 168, 112, 150))
        hi.setColorAt(1.0, QColor(214, 168, 112, 0))
        p.fillRect(face, QBrush(hi))
        # bottom shade
        lo = QLinearGradient(QPointF(face.left(), face.bottom() - face.height() * 0.4), face.bottomLeft())
        lo.setColorAt(0.0, QColor(0, 0, 0, 0))
        lo.setColorAt(1.0, QColor(0, 0, 0, 95))
        p.fillRect(face, QBrush(lo))
        # grain
        p.setPen(QPen(QColor(92, 58, 32, 60), 1.2))
        for i in range(6):
            y = face.top() + face.height() * (i + 1) / 7
            path = QPainterPath()
            path.moveTo(face.left() + 6, y)
            steps = 22
            for s in range(1, steps + 1):
                x = face.left() + 6 + (face.width() - 12) * s / steps
                path.lineTo(x, y + math.sin(s * 0.6 + i * 1.3) * 1.6)
            p.drawPath(path)
        p.restore()

        # corner bolts
        for bx, by in [(face.left() + 16, face.top() + 16),
                       (face.right() - 16, face.top() + 16),
                       (face.left() + 16, face.bottom() - 16),
                       (face.right() - 16, face.bottom() - 16)]:
            self._bolt(p, bx, by)

        # icon recess + glyph
        text_left = face.left() + 30
        if self.icon:
            d = face.height() * 0.5
            ir = QRectF(face.left() + 24, face.center().y() - d / 2, d, d)
            g = QRadialGradient(ir.center(), ir.width() / 2)
            g.setColorAt(0.0, QColor(120, 78, 44))
            g.setColorAt(1.0, QColor(70, 44, 24))
            p.setPen(QPen(QColor(40, 24, 12), 2))
            p.setBrush(QBrush(g))
            p.drawEllipse(ir)
            f = QFont(); f.setPointSizeF(d * 0.55)
            p.setFont(f)
            p.setPen(QColor(60, 38, 20))
            p.drawText(ir, Qt.AlignCenter, self.icon)
            text_left = ir.right() + 16

        # engraved text
        font = QFont("Georgia"); font.setPointSizeF(face.height() * 0.25); font.setBold(True)
        p.setFont(font)
        tr = QRectF(text_left, face.top(), face.right() - text_left - 14, face.height())
        p.setPen(QColor(0, 0, 0, 120))
        p.drawText(tr.translated(-1.2, -1.2), Qt.AlignVCenter | Qt.AlignLeft, self.text)
        p.setPen(QColor(255, 245, 225, 90))
        p.drawText(tr.translated(1.2, 1.2), Qt.AlignVCenter | Qt.AlignLeft, self.text)
        p.setPen(QColor(248, 238, 220))
        p.drawText(tr, Qt.AlignVCenter | Qt.AlignLeft, self.text)
        p.end()

    def _bolt(self, p, cx, cy):
        d = 7
        g = QRadialGradient(QPointF(cx - 1, cy - 1), d)
        g.setColorAt(0.0, QColor(120, 80, 48))
        g.setColorAt(1.0, QColor(60, 36, 18))
        p.setPen(Qt.NoPen); p.setBrush(QBrush(g))
        p.drawEllipse(QRectF(cx - d / 2, cy - d / 2, d, d))
        p.setPen(QPen(QColor(40, 24, 12), 1))
        p.drawLine(QPointF(cx - 2, cy), QPointF(cx + 2, cy))


# ─────────────────────────────────────────────────────────────────────────
#  Coin badge  (small wooden plaque, top-right, shows live coin count)
# ─────────────────────────────────────────────────────────────────────────
class CoinBadge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._coins = 0
        self.setFixedSize(190, 60)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def set_coins(self, value: int):
        self._coins = int(value)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        r = QRectF(2, 2, self.width() - 4, self.height() - 4)
        radius = 16

        shadow = QPainterPath()
        shadow.addRoundedRect(r.translated(0, 4), radius, radius)
        p.fillPath(shadow, QColor(0, 0, 0, 90))

        outer = QPainterPath(); outer.addRoundedRect(r, radius, radius)
        p.fillPath(outer, QColor(66, 40, 22))

        face = r.adjusted(4, 4, -4, -4)
        fp = QPainterPath(); fp.addRoundedRect(face, radius - 3, radius - 3)
        grad = QLinearGradient(face.topLeft(), face.bottomLeft())
        grad.setColorAt(0.0, QColor(176, 122, 72))
        grad.setColorAt(1.0, QColor(120, 78, 44))
        p.fillPath(fp, QBrush(grad))
        p.setPen(QPen(QColor(214, 168, 112, 160), 1.5))
        p.drawPath(fp)

        # coin disc
        cd = 30
        cx = face.left() + 14
        cy = face.center().y() - cd / 2
        coin_rect = QRectF(cx, cy, cd, cd)
        cg = QRadialGradient(coin_rect.center(), cd / 2)
        cg.setColorAt(0.0, QColor(255, 226, 140))
        cg.setColorAt(1.0, QColor(214, 158, 48))
        p.setBrush(QBrush(cg))
        p.setPen(QPen(QColor(150, 100, 24), 2))
        p.drawEllipse(coin_rect)
        cf = QFont("Georgia", 13, QFont.Bold)
        p.setFont(cf)
        p.setPen(QColor(140, 92, 20))
        p.drawText(coin_rect, Qt.AlignCenter, "C")

        # count
        tf = QFont("Georgia", 17, QFont.Bold)
        p.setFont(tf)
        tr = QRectF(coin_rect.right() + 8, face.top(),
                    face.right() - coin_rect.right() - 14, face.height())
        p.setPen(QColor(0, 0, 0, 110))
        p.drawText(tr.translated(1, 1), Qt.AlignVCenter | Qt.AlignLeft, f"{self._coins:,}")
        p.setPen(QColor(255, 246, 224))
        p.drawText(tr, Qt.AlignVCenter | Qt.AlignLeft, f"{self._coins:,}")
        p.end()


# ─────────────────────────────────────────────────────────────────────────
#  Soft lamplight overlay (matches startscreen mood)
# ─────────────────────────────────────────────────────────────────────────
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
        vignette.setColorAt(0.72, QColor(10, 5, 0, 50))
        vignette.setColorAt(1, QColor(8, 4, 0, 150))
        p.fillRect(0, 0, W, H, vignette)
        # gentle lamp shimmer from the hanging bulb (top-centre)
        shimmer = 0.5 + 0.5 * math.sin(self._t)
        lamp_alpha = int(30 + 26 * shimmer)
        lamp = QRadialGradient(W / 2, 70, 280)
        lamp.setColorAt(0, QColor(255, 198, 110, lamp_alpha))
        lamp.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillRect(0, 0, W, 320, lamp)
        bottom = QLinearGradient(0, H * 0.58, 0, H)
        bottom.setColorAt(0, QColor(0, 0, 0, 0))
        bottom.setColorAt(1, QColor(18, 8, 2, 180))
        p.fillRect(0, int(H * 0.58), W, H, bottom)
        p.end()


# ─────────────────────────────────────────────────────────────────────────
#  Lobby screen
# ─────────────────────────────────────────────────────────────────────────
class LobbyScreen(QMainWindow):
    def __init__(self, game=None):
        super().__init__()
        self.game = game
        self.setWindowTitle("Stimulus — Wren")
        self.setFixedSize(W, H)
        self.shop_win = None
        self.letter_win = None
        self._build()
        self.refresh_coins()

    # ---- UI ----
    def _build(self):
        root = QWidget()
        self.setCentralWidget(root)
        root.setStyleSheet("background: #1C1208;")

        # background
        bg = QLabel(root)
        if os.path.exists(BG_PATH):
            pix = QPixmap(BG_PATH).scaled(W, H, Qt.KeepAspectRatioByExpanding,
                                          Qt.SmoothTransformation)
            x_off = max(0, (pix.width() - W) // 2)
            y_off = max(0, (pix.height() - H) // 2)
            bg.setPixmap(pix.copy(x_off, y_off, W, H))
        else:
            print(f"[!] lobby.png not found at {BG_PATH}")
            bg.setStyleSheet("background: #2A1D10;")
        bg.setGeometry(0, 0, W, H)

        Overlay(root)

        # coin badge (top-right)
        self.coin_badge = CoinBadge(root)
        self.coin_badge.move(W - self.coin_badge.width() - 24, 22)
        self.coin_badge.raise_()

        # buttons (bottom-left / bottom-right)
        self.shop_btn = WoodenButton("Shop", icon="🧺", parent=root)
        self.shop_btn.setFixedSize(300, 100)
        self.shop_btn.move(40, H - 130)
        self.shop_btn.clicked.connect(self._on_shop)
        self.shop_btn.raise_()

        self.letter_btn = WoodenButton("Get My Letter", icon="✉️", parent=root)
        self.letter_btn.setFixedSize(340, 100)
        self.letter_btn.move(W - 340 - 40, H - 130)
        self.letter_btn.clicked.connect(self._on_letter)
        self.letter_btn.raise_()

    # ---- coins from Eve ----
    def _eve_coins(self) -> int:
        """Read the live coin total from the Game's Eve, defensively."""
        eve = getattr(self.game, "eve", None) if self.game else None
        if eve is None:
            return 0
        # eve.py stores the live total in `coins` (set in __init__)
        return int(getattr(eve, "coins", 0) or 0)

    def refresh_coins(self):
        """Call this whenever coins may have changed (e.g. after returning
        from the shop or finishing a puzzle)."""
        self.coin_badge.set_coins(self._eve_coins())

    # ---- routing ----
    def _on_shop(self):
        """Open shop.py. Refresh coins when the shop closes (spending)."""
        try:
            from ui.shop import ShopScreen
        except Exception as e:
            print(f"[lobby] shop screen not available yet ({e}).")
            return

        # Pass the game so the shop can spend Eve's coins.
        self.shop_win = ShopScreen(game=self.game)
        # If the shop emits a `closed` signal, refresh the badge on return.
        if hasattr(self.shop_win, "closed"):
            self.shop_win.closed.connect(self.refresh_coins)
        self.shop_win.show()

    def _on_letter(self):
        """Open letterscreen.py for the current letter."""
        # Preferred path: let the controller drive the story.
        if self.game is not None and hasattr(self.game, "show_current_letter"):
            self.game.show_current_letter()
            self.close()
            return

        # Standalone fallback: open LetterScreen directly with letter 0 (if any).
        from ui.letterscreen import LetterScreen
        letter = None
        letters = getattr(self.game, "letters", None) if self.game else None
        if letters:
            idx = getattr(self.game, "current_index", 0)
            letter = letters[idx] if idx < len(letters) else letters[0]
        self.letter_win = LetterScreen(game=self.game, letter=letter)
        self.letter_win.show()
        self.close()


if __name__ == "__main__":
    # Standalone visual test. Builds a throwaway Eve so the badge has a value.
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    class _FakeGame:
        def __init__(self):
            try:
                from eve import Eve
                self.eve = Eve(10000)
            except Exception:
                class _E: coins = 10000
                self.eve = _E()
            self.letters = []
            self.current_index = 0

    screen = LobbyScreen(game=_FakeGame())
    screen.show()
    sys.exit(app.exec())