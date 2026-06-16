"""
Stimulus — Sequence Puzzle  (the "put it in order" card)
File location: STIMULUS/puzzles/sequencegame.py

A cozy drag-and-drop ordering puzzle, reskinned into the Stimulus world:
warm lamplit wood, frosted-glass tiles, Georgia serif, bevelled wooden
button. Drag the tiles left/right into the intended order and verify.

Wired for the controller like the other puzzles:
  * exposes a `completed = Signal(int)` that emits coins on a correct solve,
    so Game.launch_puzzle can connect it and advance the story.
  * runnable standalone for visual testing.

Data: pass a dict shaped like a letter's ordering card, or use the default.
"""

import sys, random
from PySide6.QtCore import Qt, QMimeData, QRectF, QPropertyAnimation, QEasingCurve, QPoint, Signal
from PySide6.QtGui import (
    QDrag, QPixmap, QPainter, QPainterPath, QColor, QFont, QPen, QBrush,
    QLinearGradient, QRadialGradient
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel
)

# ── Stimulus palette (shared with logigrame / the lamplit world) ─────────
P = {
    "bg":          QColor(42, 29, 16),     # deep warm wood
    "bg_header":   QColor(31, 20, 10),
    "tile_top":    QColor(255, 250, 240),  # frosted glass tops
    "tile_bot":    QColor(225, 212, 190),
    "tile_hi":     QColor(255, 255, 255),
    "accent":      QColor(196, 136, 78),   # warm amber/brass
    "accent_deep": QColor(160, 106, 54),
    "correct":     QColor(110, 139, 61),   # mossy green
    "text_strong": QColor(48, 30, 14),
    "text_cream":  QColor(255, 233, 176),
    "text_dim":    QColor(216, 184, 136),
}

W, H = 760, 480


# ── Default data (mirrors a letter's ordering-card shape) ────────────────
DEFAULT_DATA = {
    "title": "A Slow Morning",
    "slots": ["Open the window", "Brew the tea", "Sit and watch the light"],
    "correctOrder": [0, 1, 2],
    "label": "Some mornings are best taken one small step at a time.",
    "coins": 8,
}


# ─────────────────────────────────────────────────────────────────────────
#  Frosted glass draggable tile
# ─────────────────────────────────────────────────────────────────────────
class DraggableTile(QWidget):
    def __init__(self, text, original_index, parent=None):
        super().__init__(parent)
        self.text = text
        self.original_index = original_index
        self._hover = False
        self._dragging = False
        self.setFixedSize(150, 96)
        self.setCursor(Qt.OpenHandCursor)
        self.setAttribute(Qt.WA_Hover, True)

    def enterEvent(self, e):
        self._hover = True; self.update()

    def leaveEvent(self, e):
        self._hover = False; self.update()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(3, 3, self.width() - 6, self.height() - 6)
        radius = 16
        path = QPainterPath(); path.addRoundedRect(r, radius, radius)

        # soft shadow
        sh = QPainterPath(); sh.addRoundedRect(r.translated(0, 4), radius, radius)
        p.fillPath(sh, QColor(0, 0, 0, 70))

        # frosted body
        glass = QLinearGradient(r.topLeft(), r.bottomLeft())
        a_top = 190 if self._hover else 150
        glass.setColorAt(0.0, QColor(P["tile_top"].red(), P["tile_top"].green(), P["tile_top"].blue(), a_top))
        glass.setColorAt(1.0, QColor(P["tile_bot"].red(), P["tile_bot"].green(), P["tile_bot"].blue(), a_top - 40))
        p.fillPath(path, QBrush(glass))

        # top sheen
        p.save(); p.setClipPath(path)
        sheen = QLinearGradient(r.topLeft(), QRectF(r).adjusted(0, 0, 0, -r.height() * 0.6).bottomLeft())
        sheen.setColorAt(0.0, QColor(255, 255, 255, 120))
        sheen.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.fillRect(r, QBrush(sheen))
        p.restore()

        # border, amber on hover
        border = P["accent"] if self._hover else QColor(255, 246, 230, 140)
        p.setPen(QPen(border, 1.8)); p.drawPath(path)

        # grip dots (a little drag affordance)
        p.setPen(Qt.NoPen); p.setBrush(QColor(150, 110, 64, 120))
        for i in range(3):
            cx = r.center().x() - 8 + i * 8
            p.drawEllipse(QRectF(cx - 2, r.top() + 12, 4, 4))

        # label
        p.setPen(P["text_strong"])
        p.setFont(QFont("Georgia", 12, QFont.Bold))
        tr = QRectF(r.left() + 10, r.top() + 22, r.width() - 20, r.height() - 30)
        p.drawText(tr, Qt.AlignCenter | Qt.TextWordWrap, self.text)
        p.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setCursor(Qt.ClosedHandCursor)
            mime = QMimeData()
            mime.setText(str(self.original_index))
            drag = QDrag(self)
            drag.setMimeData(mime)
            # drag preview = a snapshot of the tile
            pm = self.grab()
            drag.setPixmap(pm)
            drag.setHotSpot(event.position().toPoint())
            drag.exec(Qt.MoveAction)
            self.setCursor(Qt.OpenHandCursor)


# ─────────────────────────────────────────────────────────────────────────
#  Drop zone — reorders tiles by swapping on drop
# ─────────────────────────────────────────────────────────────────────────
class SequenceDropZone(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setSpacing(16)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setAlignment(Qt.AlignCenter)
        self.tiles = []
        self._locked = False

    def load_sequence(self, slots):
        for t in self.tiles:
            t.deleteLater()
        self.tiles.clear()
        temp = [DraggableTile(text, idx) for idx, text in enumerate(slots)]
        # shuffle until it's not already solved (so there's always something to do)
        if len(temp) > 1:
            order = list(range(len(temp)))
            while True:
                random.shuffle(temp)
                if [t.original_index for t in temp] != order:
                    break
        for t in temp:
            self.tiles.append(t)
            self.main_layout.addWidget(t)

    def dragEnterEvent(self, e):
        if e.mimeData().hasText():
            e.acceptProposedAction()

    def dragMoveEvent(self, e):
        if e.mimeData().hasText():
            e.acceptProposedAction()

    def dropEvent(self, e):
        if self._locked:
            return
        src = e.source()
        if not isinstance(src, DraggableTile):
            return
        pos = self.mapFromGlobal(self.cursor().pos())
        for i, tile in enumerate(self.tiles):
            if tile is not src and tile.geometry().contains(pos):
                si = self.tiles.index(src)
                self.tiles[si], self.tiles[i] = self.tiles[i], self.tiles[si]
                self._reflow()
                e.acceptProposedAction()
                return

    def _reflow(self):
        for t in self.tiles:
            self.main_layout.removeWidget(t)
        for t in self.tiles:
            self.main_layout.addWidget(t)

    def current_sequence(self):
        return [t.original_index for t in self.tiles]

    def flash_correct(self):
        self._locked = True
        for t in self.tiles:
            t._hover = False
            t.update()


# ─────────────────────────────────────────────────────────────────────────
#  Bevelled wooden button (Stimulus style)
# ─────────────────────────────────────────────────────────────────────────
class WoodenButton(QWidget):
    clicked = Signal()

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text
        self._hover = False
        self._pressed = False
        self.setFixedSize(300, 58)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)

    def setText(self, t):
        self.text = t; self.update()

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
        p.setPen(QColor(0, 0, 0, 110))
        p.setFont(QFont("Georgia", 14, QFont.Bold))
        p.drawText(self.rect().translated(0, sink - 1), Qt.AlignCenter, self.text)
        p.setPen(P["text_cream"])
        p.drawText(self.rect().translated(0, sink), Qt.AlignCenter, self.text)
        p.end()


# ─────────────────────────────────────────────────────────────────────────
#  Main puzzle window
# ─────────────────────────────────────────────────────────────────────────
class SequenceGame(QMainWindow):
    completed = Signal(int)   # emits coins on a correct solve

    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self.data = data or DEFAULT_DATA
        self.coins = int(self.data.get("coins", 8))
        self.setWindowTitle("Stimulus — In Order")
        self.setFixedSize(W, H)
        self._build()

    def _build(self):
        root = QWidget(); self.setCentralWidget(root)
        root.setObjectName("root")
        root.setStyleSheet(f"#root {{ background: {P['bg'].name()}; }}")
        lay = QVBoxLayout(root)
        lay.setContentsMargins(40, 30, 40, 30)
        lay.setSpacing(6)

        title = QLabel(self.data["title"])
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Georgia", 24, QFont.Bold))
        title.setStyleSheet(f"color: {P['accent'].name()}; letter-spacing: 1px;")
        lay.addWidget(title)

        hint = QLabel(self.data.get("label", ""))
        hint.setAlignment(Qt.AlignCenter)
        hint.setWordWrap(True)
        hint.setFont(QFont("Georgia", 12, -1, True))
        hint.setStyleSheet(f"color: {P['text_dim'].name()}; margin-bottom: 6px;")
        lay.addWidget(hint)

        lay.addStretch(1)

        self.zone = SequenceDropZone(root)
        self.zone.load_sequence(self.data["slots"])
        lay.addWidget(self.zone, alignment=Qt.AlignCenter)

        lay.addStretch(1)

        self.status = QLabel("Drag the tiles into the order that feels right.")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setFont(QFont("Georgia", 11))
        self.status.setStyleSheet(f"color: {P['text_dim'].name()};")
        lay.addWidget(self.status)

        self.verify_btn = WoodenButton(f"Verify  ·  +{self.coins} coins")
        self.verify_btn.clicked.connect(self._check)
        lay.addWidget(self.verify_btn, alignment=Qt.AlignCenter)

    def _check(self):
        if self.zone.current_sequence() == self.data["correctOrder"]:
            self.zone.flash_correct()
            self.status.setText("That's the one. Nicely ordered.")
            self.status.setStyleSheet(f"color: {P['correct'].name()}; font-weight: bold;")
            self.verify_btn.setText("Done ✦")
            # advance the story after a beat
            from PySide6.QtCore import QTimer
            QTimer.singleShot(900, lambda: (self.completed.emit(self.coins), self.close()))
        else:
            self.status.setText("Not quite in order yet — try rearranging.")
            self.status.setStyleSheet(f"color: {P['accent'].name()};")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = SequenceGame()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()