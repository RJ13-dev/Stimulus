"""
Stimulus — Sequence Puzzle  (the Medium "put it in order" card)
File location: STIMULUS/puzzles/sequencegame.py

Drag the frosted tiles into the intended order and Verify. Mirrors the
logigrame endings exactly:
  * WIN  -> confetti + coin, "Yay — you won!", holds ~5s, awards coins,
            returns to the CARD SCREEN.
  * LOSS -> broken hearts, "Better luck next time", holds ~5s, returns to
            the CARD SCREEN (no coins). Loss happens when lives run out.
  * 3 lives: each wrong Verify costs a life. Wooden Exit returns anytime.

Data comes from a letter's MEDIUM card in letters.json, card["data"]:
    { "title": "...", "label": "<hint sentence>",
      "slots": ["Rough Sketch","Inking Lines","Adding Color"],
      "correctOrder": [0,1,2] }

Controller wiring (Game.launch_puzzle):
    from puzzles.sequencegame import SequenceGame
    self.puzzle_win = SequenceGame(data=med_card["data"],
                                   coins=med_card["coins"],
                                   game=self,
                                   return_cb=self.show_choices)
    self.puzzle_win.show()
    return
"""

import sys, math
import random as _random
from PySide6.QtCore import Qt, QMimeData, QRectF, QTimer, Signal
from PySide6.QtGui import (
    QDrag, QPainter, QPainterPath, QColor, QFont, QPen, QBrush,
    QLinearGradient, QRadialGradient
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel
)

MAX_LIVES = 3
DEFAULT_COINS = 50

P = {
    "bg":          QColor(42, 29, 16),
    "tile_top":    QColor(255, 250, 240),
    "tile_bot":    QColor(225, 212, 190),
    "accent":      QColor(196, 136, 78),
    "accent_deep": QColor(160, 106, 54),
    "correct":     QColor(110, 139, 61),
    "wrong":       QColor(194, 90, 69),
    "text_strong": QColor(48, 30, 14),
    "text_cream":  QColor(255, 233, 176),
    "text_dim":    QColor(216, 184, 136),
    "heart_on":    QColor(212, 132, 90),
    "heart_off":   QColor(90, 71, 51),
}

W, H = 820, 540

DEFAULT_DATA = {
    "title": "Thumbnail to Masterpiece",
    "slots": ["Rough Sketch", "Inking Lines", "Adding Color"],
    "correctOrder": [0, 1, 2],
    "label": "Lay down your basic shapes before committing to lines and color.",
}


# ── Frosted draggable tile ───────────────────────────────────────────────
class DraggableTile(QWidget):
    def __init__(self, text, original_index, parent=None):
        super().__init__(parent)
        self.text = text; self.original_index = original_index
        self._hover = False
        self.setFixedSize(160, 100)
        self.setCursor(Qt.OpenHandCursor)
        self.setAttribute(Qt.WA_Hover, True)

    def enterEvent(self, e): self._hover = True; self.update()
    def leaveEvent(self, e): self._hover = False; self.update()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(3, 3, self.width() - 6, self.height() - 6); radius = 16
        path = QPainterPath(); path.addRoundedRect(r, radius, radius)
        sh = QPainterPath(); sh.addRoundedRect(r.translated(0, 4), radius, radius)
        p.fillPath(sh, QColor(0, 0, 0, 70))
        glass = QLinearGradient(r.topLeft(), r.bottomLeft())
        a_top = 195 if self._hover else 150
        glass.setColorAt(0.0, QColor(P["tile_top"].red(), P["tile_top"].green(), P["tile_top"].blue(), a_top))
        glass.setColorAt(1.0, QColor(P["tile_bot"].red(), P["tile_bot"].green(), P["tile_bot"].blue(), a_top - 40))
        p.fillPath(path, QBrush(glass))
        p.save(); p.setClipPath(path)
        sheen = QLinearGradient(r.topLeft(), QRectF(r).adjusted(0, 0, 0, -r.height() * 0.6).bottomLeft())
        sheen.setColorAt(0.0, QColor(255, 255, 255, 120)); sheen.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.fillRect(r, QBrush(sheen)); p.restore()
        border = P["accent"] if self._hover else QColor(255, 246, 230, 140)
        p.setPen(QPen(border, 1.8)); p.drawPath(path)
        p.setPen(Qt.NoPen); p.setBrush(QColor(150, 110, 64, 120))
        for i in range(3):
            cx = r.center().x() - 8 + i * 8
            p.drawEllipse(QRectF(cx - 2, r.top() + 12, 4, 4))
        p.setPen(P["text_strong"]); p.setFont(QFont("Georgia", 12, QFont.Bold))
        tr = QRectF(r.left() + 10, r.top() + 22, r.width() - 20, r.height() - 30)
        p.drawText(tr, Qt.AlignCenter | Qt.TextWordWrap, self.text)
        p.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setCursor(Qt.ClosedHandCursor)
            mime = QMimeData(); mime.setText(str(self.original_index))
            drag = QDrag(self); drag.setMimeData(mime)
            drag.setPixmap(self.grab()); drag.setHotSpot(event.position().toPoint())
            drag.exec(Qt.MoveAction)
            self.setCursor(Qt.OpenHandCursor)


# ── Drop zone ────────────────────────────────────────────────────────────
class SequenceDropZone(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setSpacing(16); self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setAlignment(Qt.AlignCenter)
        self.tiles = []; self._locked = False

    def load_sequence(self, slots):
        for t in self.tiles: t.deleteLater()
        self.tiles.clear()
        temp = [DraggableTile(text, idx) for idx, text in enumerate(slots)]
        if len(temp) > 1:
            order = list(range(len(temp)))
            while True:
                _random.shuffle(temp)
                if [t.original_index for t in temp] != order: break
        for t in temp:
            self.tiles.append(t); self.main_layout.addWidget(t)

    def dragEnterEvent(self, e):
        if e.mimeData().hasText(): e.acceptProposedAction()
    def dragMoveEvent(self, e):
        if e.mimeData().hasText(): e.acceptProposedAction()

    def dropEvent(self, e):
        if self._locked: return
        src = e.source()
        if not isinstance(src, DraggableTile): return
        pos = self.mapFromGlobal(self.cursor().pos())
        for i, tile in enumerate(self.tiles):
            if tile is not src and tile.geometry().contains(pos):
                si = self.tiles.index(src)
                self.tiles[si], self.tiles[i] = self.tiles[i], self.tiles[si]
                self._reflow(); e.acceptProposedAction(); return

    def _reflow(self):
        for t in self.tiles: self.main_layout.removeWidget(t)
        for t in self.tiles: self.main_layout.addWidget(t)

    def current_sequence(self):
        return [t.original_index for t in self.tiles]

    def lock(self):
        self._locked = True
        for t in self.tiles:
            t._hover = False; t.setCursor(Qt.ArrowCursor); t.update()


# ── Wooden button ────────────────────────────────────────────────────────
class WoodenButton(QWidget):
    clicked = Signal()

    def __init__(self, text, width=300, parent=None):
        super().__init__(parent)
        self.text = text; self._hover = False; self._pressed = False
        self.setFixedSize(width, 56)
        self.setCursor(Qt.PointingHandCursor); self.setAttribute(Qt.WA_Hover, True)

    def setText(self, t): self.text = t; self.update()
    def enterEvent(self, e): self._hover = True; self.update()
    def leaveEvent(self, e): self._hover = False; self.update()
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton: self._pressed = True; self.update()
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self._pressed:
            self._pressed = False; self.update()
            if self.rect().contains(e.position().toPoint()): self.clicked.emit()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        sink = 2 if self._pressed else 0
        r = QRectF(3, 3 + sink, self.width() - 6, self.height() - 6 - 2)
        radius = r.height() / 2
        sh = QPainterPath(); sh.addRoundedRect(r.translated(0, 4 - sink), radius, radius)
        p.fillPath(sh, QColor(0, 0, 0, 80))
        outer = QPainterPath(); outer.addRoundedRect(r, radius, radius)
        p.fillPath(outer, QColor(66, 40, 22))
        face = r.adjusted(4, 4, -4, -4)
        fp = QPainterPath(); fp.addRoundedRect(face, face.height() / 2, face.height() / 2)
        grad = QLinearGradient(face.topLeft(), face.bottomLeft())
        light = 14 if self._hover else 0
        grad.setColorAt(0.0, QColor(184, 130, 78).lighter(100 + light))
        grad.setColorAt(0.5, QColor(150, 99, 55).lighter(100 + light))
        grad.setColorAt(1.0, QColor(110, 70, 38).lighter(100 + light))
        p.fillPath(fp, QBrush(grad))
        p.setPen(QPen(QColor(214, 168, 112, 150), 1.4)); p.drawPath(fp)
        p.setPen(QColor(0, 0, 0, 110)); p.setFont(QFont("Georgia", 14, QFont.Bold))
        p.drawText(self.rect().translated(0, sink - 1), Qt.AlignCenter, self.text)
        p.setPen(P["text_cream"]); p.drawText(self.rect().translated(0, sink), Qt.AlignCenter, self.text)
        p.end()


# ── End overlay (identical behaviour to logigrame) ───────────────────────
class EndOverlay(QWidget):
    CONFETTI_COLORS = [
        QColor(196, 136, 78), QColor(214, 158, 48), QColor(110, 139, 61),
        QColor(212, 132, 90), QColor(255, 226, 140), QColor(160, 106, 54),
        QColor(255, 246, 224),
    ]

    def __init__(self, won, coins, parent=None):
        super().__init__(parent)
        self.won = won; self.coins = coins
        self._t = 0.0; self._secs_left = 5
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._pieces = []; self._spawn()
        self._timer = QTimer(self); self._timer.timeout.connect(self._tick); self._timer.start(33)
        self._count = QTimer(self); self._count.timeout.connect(self._tick_count); self._count.start(1000)

    def _spawn(self):
        w = self.parent().width() if self.parent() else W
        h = self.parent().height() if self.parent() else H
        n = 140 if self.won else 36
        for _ in range(n):
            self._pieces.append({
                "x": _random.uniform(0, w), "y": _random.uniform(-h * 0.6, 0),
                "vx": _random.uniform(-1.2, 1.2),
                "vy": _random.uniform(2.6, 5.2) if self.won else _random.uniform(1.4, 2.8),
                "size": _random.uniform(6, 12) if self.won else _random.uniform(16, 26),
                "spin": _random.uniform(-0.3, 0.3) if self.won else _random.uniform(-0.12, 0.12),
                "angle": _random.uniform(0, math.tau),
                "color": _random.choice(self.CONFETTI_COLORS),
            })

    def _tick(self):
        self._t += 0.05; wh = self.height() or H
        grav = 0.04 if self.won else 0.015
        for p in self._pieces:
            p["x"] += p["vx"]; p["y"] += p["vy"]; p["vy"] += grav; p["angle"] += p["spin"]
            if p["y"] > wh + 30:
                p["y"] = _random.uniform(-60, -10)
                p["x"] = _random.uniform(0, self.width() or W)
                p["vy"] = _random.uniform(2.6, 5.2) if self.won else _random.uniform(1.4, 2.8)
        self.update()

    def _tick_count(self):
        self._secs_left = max(0, self._secs_left - 1); self.update()

    def _draw_broken_heart(self, p, size, color):
        s = size; p.setBrush(color); p.setPen(Qt.NoPen)
        path = QPainterPath()
        path.moveTo(0, s * 0.32)
        path.cubicTo(-s * 0.1, s * 0.05, -s * 0.5, s * 0.05, -s * 0.5, -s * 0.18)
        path.cubicTo(-s * 0.5, -s * 0.42, -s * 0.18, -s * 0.46, 0, -s * 0.22)
        path.lineTo(-s * 0.06, -s * 0.05); path.lineTo(s * 0.05, s * 0.06)
        path.lineTo(-s * 0.04, s * 0.16); path.closeSubpath(); p.drawPath(path)
        path2 = QPainterPath()
        path2.moveTo(s * 0.04, s * 0.34)
        path2.cubicTo(s * 0.14, s * 0.07, s * 0.54, s * 0.07, s * 0.54, -s * 0.16)
        path2.cubicTo(s * 0.54, -s * 0.40, s * 0.22, -s * 0.44, s * 0.04, -s * 0.20)
        path2.lineTo(s * 0.12, -s * 0.05); path2.lineTo(s * 0.01, s * 0.06)
        path2.lineTo(s * 0.10, s * 0.18); path2.closeSubpath(); p.drawPath(path2)

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(14, 8, 3, 185))
        for piece in self._pieces:
            p.save(); p.translate(piece["x"], piece["y"]); p.rotate(math.degrees(piece["angle"]))
            if self.won:
                p.setPen(Qt.NoPen); p.setBrush(piece["color"]); s = piece["size"]
                p.drawRoundedRect(QRectF(-s / 2, -s / 3, s, s * 0.66), 2, 2)
            else:
                self._draw_broken_heart(p, piece["size"], QColor(178, 74, 60, 220))
            p.restore()
        cw, ch = 470, 250
        r = QRectF((w - cw) / 2, (h - ch) / 2, cw, ch)
        path = QPainterPath(); path.addRoundedRect(r, 22, 22)
        glass = QLinearGradient(r.topLeft(), r.bottomLeft())
        glass.setColorAt(0.0, QColor(255, 250, 240, 245)); glass.setColorAt(1.0, QColor(232, 218, 194, 240))
        p.fillPath(path, QBrush(glass))
        edge = QColor(196, 136, 78, 230) if self.won else QColor(178, 100, 80, 230)
        p.setPen(QPen(edge, 2)); p.drawPath(path)
        if self.won: self._paint_win(p, r)
        else: self._paint_loss(p, r)
        p.end()

    def _paint_win(self, p, r):
        glow_a = int(60 + 40 * (0.5 + 0.5 * math.sin(self._t)))
        glow = QRadialGradient(r.center().x(), r.top() + 82, 120)
        glow.setColorAt(0.0, QColor(255, 198, 110, glow_a)); glow.setColorAt(1.0, QColor(255, 198, 110, 0))
        p.fillRect(r, QBrush(glow))
        bob = math.sin(self._t * 2.0) * 4; cd = 64
        coin = QRectF(r.center().x() - cd / 2, r.top() + 48 + bob, cd, cd)
        cg = QRadialGradient(coin.center(), cd / 2)
        cg.setColorAt(0.0, QColor(255, 232, 150)); cg.setColorAt(1.0, QColor(214, 158, 48))
        p.setBrush(QBrush(cg)); p.setPen(QPen(QColor(150, 100, 24), 2.5)); p.drawEllipse(coin)
        p.setFont(QFont("Georgia", 26, QFont.Bold)); p.setPen(QColor(140, 92, 20)); p.drawText(coin, Qt.AlignCenter, "C")
        p.setPen(QColor(54, 34, 14)); p.setFont(QFont("Georgia", 22, QFont.Bold))
        p.drawText(QRectF(r.left(), r.top() + 124, r.width(), 36), Qt.AlignCenter, "Yay — you won!")
        p.setPen(QColor(160, 106, 54)); p.setFont(QFont("Georgia", 15, QFont.Bold))
        p.drawText(QRectF(r.left(), r.top() + 160, r.width(), 28), Qt.AlignCenter, f"+{self.coins} coins")
        p.setPen(QColor(110, 78, 44)); p.setFont(QFont("Georgia", 11, -1, True))
        msg = "Enjoy a little shopping…" if self._secs_left > 1 else "Back to your cards…"
        p.drawText(QRectF(r.left(), r.bottom() - 42, r.width(), 24), Qt.AlignCenter, msg)

    def _paint_loss(self, p, r):
        p.save(); p.translate(r.center().x(), r.top() + 70)
        self._draw_broken_heart(p, 58, QColor(178, 74, 60, 235)); p.restore()
        p.setPen(QColor(120, 52, 40)); p.setFont(QFont("Georgia", 21, QFont.Bold))
        p.drawText(QRectF(r.left(), r.top() + 118, r.width(), 34), Qt.AlignCenter, "Better luck next time")
        p.setPen(QColor(110, 78, 44)); p.setFont(QFont("Georgia", 12))
        p.drawText(QRectF(r.left(), r.top() + 154, r.width(), 26), Qt.AlignCenter,
                   "Give it another try and earn some coins.")
        p.setPen(QColor(150, 110, 70)); p.setFont(QFont("Georgia", 11, -1, True))
        msg = "Heading back…" if self._secs_left <= 1 else "Back to your cards soon…"
        p.drawText(QRectF(r.left(), r.bottom() - 42, r.width(), 24), Qt.AlignCenter, msg)


# ── Main window ──────────────────────────────────────────────────────────
class SequenceGame(QMainWindow):
    completed = Signal(int)

    def __init__(self, data=None, coins=DEFAULT_COINS, game=None, return_cb=None):
        super().__init__()
        self.data = data or DEFAULT_DATA
        self.coins_award = int(coins)
        self.game = game
        self.return_cb = return_cb
        self.lives = MAX_LIVES
        self.game_over = False
        self._finished = False
        self.setWindowTitle("Stimulus — In Order")
        self.setFixedSize(W, H)
        self._build()

    def _build(self):
        root = QWidget(); self.setCentralWidget(root)
        root.setObjectName("root")
        root.setStyleSheet(f"#root {{ background: {P['bg'].name()}; }}")
        lay = QVBoxLayout(root); lay.setContentsMargins(40, 26, 40, 28); lay.setSpacing(6)

        # top row: title + hearts + exit
        top = QHBoxLayout()
        title = QLabel(self.data.get("title", "In Order"))
        title.setFont(QFont("Georgia", 22, QFont.Bold))
        title.setStyleSheet(f"color: {P['accent'].name()}; letter-spacing: 1px;")
        top.addWidget(title); top.addStretch()
        self.heart_labels = []
        for _ in range(MAX_LIVES):
            h = QLabel("\u2665"); h.setStyleSheet(f"font-size:20px; color:{P['heart_on'].name()};")
            top.addWidget(h); self.heart_labels.append(h)
        self.exit_btn = WoodenButton("Exit", width=120)
        self.exit_btn.clicked.connect(lambda: self._finish(won=False, award=False))
        top.addSpacing(12); top.addWidget(self.exit_btn)
        lay.addLayout(top)

        hint = QLabel(self.data.get("label", ""))
        hint.setAlignment(Qt.AlignCenter); hint.setWordWrap(True)
        hint.setFont(QFont("Georgia", 12, -1, True))
        hint.setStyleSheet(f"color: {P['text_dim'].name()}; margin-bottom: 6px;")
        lay.addWidget(hint)

        lay.addStretch(1)
        self.zone = SequenceDropZone(root)
        self.zone.load_sequence(self.data["slots"])
        lay.addWidget(self.zone, alignment=Qt.AlignCenter)
        lay.addStretch(1)

        self.status = QLabel("Drag the tiles into the order that feels right.")
        self.status.setAlignment(Qt.AlignCenter); self.status.setFont(QFont("Georgia", 11))
        self.status.setStyleSheet(f"color: {P['text_dim'].name()};")
        lay.addWidget(self.status)

        self.verify_btn = WoodenButton(f"Verify  ·  +{self.coins_award} coins", width=320)
        self.verify_btn.clicked.connect(self._check)
        lay.addWidget(self.verify_btn, alignment=Qt.AlignCenter)

    def _check(self):
        if self.game_over: return
        if self.zone.current_sequence() == self.data["correctOrder"]:
            self.zone.lock()
            self.status.setText("That's the one. Nicely ordered.")
            self.status.setStyleSheet(f"color: {P['correct'].name()}; font-weight: bold;")
            QTimer.singleShot(350, self._win_celebrate)
        else:
            self.lives -= 1
            idx = MAX_LIVES - self.lives - 1
            if 0 <= idx < len(self.heart_labels):
                self.heart_labels[idx].setStyleSheet(f"font-size:20px; color:{P['heart_off'].name()};")
            if self.lives <= 0:
                self.status.setText("Out of tries.")
                self.status.setStyleSheet(f"color: {P['wrong'].name()};")
                self.zone.lock()
                QTimer.singleShot(700, self._show_loss_overlay)
            else:
                msg = "Not quite in order yet — try rearranging."
                if self.lives == 1: msg += "  ⚠ Last try!"
                self.status.setText(msg)
                self.status.setStyleSheet(f"color: {P['accent'].name()};")

    def _win_celebrate(self):
        self.game_over = True
        self._overlay = EndOverlay(won=True, coins=self.coins_award, parent=self)
        self._overlay.setGeometry(0, 0, self.width(), self.height())
        self._overlay.show(); self._overlay.raise_()
        QTimer.singleShot(5000, lambda: self._finish(won=True, award=True))

    def _show_loss_overlay(self):
        self.game_over = True
        self._overlay = EndOverlay(won=False, coins=0, parent=self)
        self._overlay.setGeometry(0, 0, self.width(), self.height())
        self._overlay.show(); self._overlay.raise_()
        QTimer.singleShot(5000, lambda: self._finish(won=False, award=False))

    def _finish(self, won: bool, award: bool):
        if self._finished: return
        self._finished = True; self.game_over = True
        coins = self.coins_award if award else 0
        if coins and self.game is not None:
            if hasattr(self.game, "award_coins"):
                self.game.award_coins(coins)
            elif getattr(self.game, "eve", None) is not None and hasattr(self.game.eve, "earn_coins"):
                self.game.eve.earn_coins(coins)
        if self.return_cb is not None:
            self.return_cb()
        elif self.game is not None and hasattr(self.game, "show_choices"):
            self.game.show_choices()
        self.completed.emit(coins)
        self.close()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = SequenceGame()   # standalone uses DEFAULT_DATA
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()