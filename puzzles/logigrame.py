"""
Logigrame — Skincare/Themed Logic Grid  (data-driven)
==============================================
A single fixed logic-grid puzzle in the Stimulus cozy/lamplit world.

Data comes from a letter's BIG card in letters.json, under card["data"]:
    {
      "subtitle":  "Art Studio Setup",
      "subjects":  ["Leo","Chloe","Zane"],
      "attributes":["Medium Focus","Surface Choice","Core Tool"],
      "options":   { "<attr>": [v1,v2,v3], ... },
      "solution":  { '("Leo", "Medium Focus")': "Charcoal", ... },  # STRING keys
      "clues":     [ ["🎨","Clue","..."], ... ]
    }

Note: JSON can't use tuple keys, so solution keys are strings like
'("Leo", "Medium Focus")'. We parse them back into (subj, attr) tuples.

Endings:
  * WIN  -> confetti + coin, "Yay — you won!", holds ~5s, awards coins,
            returns to the CARD SCREEN.
  * LOSS -> reveals answer, broken hearts, "Better luck next time / try the
            sequence game", holds ~5s, returns to the CARD SCREEN (no coins).
3 lives. Wooden Exit button returns to the card screen at any time.

Controller wiring (in Game.launch_puzzle):
    from puzzles.logigrame import MainWindow
    self.puzzle_win = MainWindow(data=big_card["data"],
                                 coins=big_card["coins"],
                                 game=self,
                                 return_cb=self.show_choices)
    self.puzzle_win.show()
    return
"""

import sys, ast, math
import random as _random
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame,
    QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
)
from PySide6.QtCore import Qt, QTimer, QRectF, Signal
from PySide6.QtGui import (
    QPainter, QPainterPath, QColor, QFont, QPen, QBrush, QLinearGradient,
    QRadialGradient
)

MAX_LIVES = 3
DEFAULT_COINS = 50

# ── Palette ──────────────────────────────────────────────────────────────
P = {
    "bg":           "#2A1D10",
    "bg_card":      "#F7EEDD",
    "bg_panel":     "#EFE2CB",
    "bg_header":    "#1F140A",
    "border":       "#D8C3A0",
    "border_dark":  "#B89A6E",
    "cell_idle":    "#FBF4E6",
    "cell_active":  "#FFF1D6",
    "cell_correct": "#E8F1DC",
    "cell_wrong":   "#F6E0D2",
    "cell_reveal":  "#FBEFD6",
    "pill_idle":    "#FBF4E6",
    "pill_hover":   "#FCE9C9",
    "pill_used_bg": "#EBE2D4",
    "pill_used_fg": "#A8977F",
    "accent":       "#C4884E",
    "accent_deep":  "#A06A36",
    "correct":      "#6E8B3D",
    "wrong":        "#C25A45",
    "text_strong":  "#2C2014",
    "text_body":    "#5A4733",
    "text_dim":     "#9A856A",
    "text_white":   "#FFF6E4",
    "heart_on":     "#D4845A",
    "heart_off":    "#5A4733",
    "divider":      "#E2D3B6",
}

# ── Fallback data (used only when run standalone with no data passed) ─────
DEFAULT_DATA = {
    "subtitle": "Art Studio Setup",
    "subjects": ["Leo", "Chloe", "Zane"],
    "attributes": ["Medium Focus", "Surface Choice", "Core Tool"],
    "options": {
        "Medium Focus":   ["Oil Paint", "Charcoal", "Watercolors"],
        "Surface Choice": ["Stretched Linen", "Toned Paper", "Cold-Press Sheet"],
        "Core Tool":      ["Bristle Brush", "Blending Stump", "Sable Round"],
    },
    "solution": {
        '("Leo", "Medium Focus")': "Charcoal",
        '("Leo", "Surface Choice")': "Toned Paper",
        '("Leo", "Core Tool")': "Sable Round",
        '("Chloe", "Medium Focus")': "Oil Paint",
        '("Chloe", "Surface Choice")': "Stretched Linen",
        '("Chloe", "Core Tool")': "Bristle Brush",
        '("Zane", "Medium Focus")': "Watercolors",
        '("Zane", "Surface Choice")': "Cold-Press Sheet",
        '("Zane", "Core Tool")': "Blending Stump",
    },
    "clues": [
        ["\U0001f3a8", "Clue", "Chloe's primary focus is working with Oil Paint."],
        ["\U0001f4dc", "Clue", "The Charcoal setup requires a Toned Paper backing."],
        ["\u270f\ufe0f", "Clue", "Zane requests a Cold-Press Sheet for his project."],
        ["\U0001f58c\ufe0f", "Clue", "The Oil Paint medium is strictly paired with a Bristle Brush."],
    ],
}


def parse_solution(raw: dict) -> dict:
    """Turn string keys '("Leo", "Medium Focus")' into ('Leo','Medium Focus')."""
    out = {}
    for k, v in raw.items():
        if isinstance(k, tuple):
            out[k] = v
        else:
            out[ast.literal_eval(k)] = v
    return out


# ── Stylesheet ───────────────────────────────────────────────────────────
SS = f"""
QMainWindow, QWidget#root {{ background: {P['bg']}; }}
QLabel {{ background: transparent; color: {P['text_body']}; }}
QFrame#header {{ background: {P['bg_header']}; border-bottom: 1px solid {P['accent_deep']}; }}
QFrame#grid_card, QFrame#side_panel {{
    background: {P['bg_card']}; border: 1px solid {P['border']}; border-radius: 14px;
}}
QFrame#clue_card {{ background: {P['bg_card']}; border: 1px solid {P['border']}; border-radius: 12px; }}
QFrame#clue_row {{ background: {P['bg_panel']}; border: 1px solid {P['border']}; border-radius: 8px; }}
QPushButton#pill {{
    background: {P['pill_idle']}; color: {P['text_strong']};
    border: 1.5px solid {P['border_dark']}; border-radius: 14px;
    padding: 6px 14px; font-size: 12px; text-align: center;
}}
QPushButton#pill:hover {{ background: {P['pill_hover']}; border-color: {P['accent']}; color: {P['accent_deep']}; }}
QPushButton#pill:disabled {{ background: {P['pill_used_bg']}; color: {P['pill_used_fg']}; border-color: {P['border']}; }}
"""


# ── Wooden Exit button ───────────────────────────────────────────────────
class WoodenButton(QWidget):
    clicked = Signal()

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text
        self._hover = False; self._pressed = False
        self.setFixedSize(150, 44)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)

    def enterEvent(self, e): self._hover = True; self.update()
    def leaveEvent(self, e): self._hover = False; self.update()

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
        sh = QPainterPath(); sh.addRoundedRect(r.translated(0, 3 - sink), radius, radius)
        p.fillPath(sh, QColor(0, 0, 0, 80))
        outer = QPainterPath(); outer.addRoundedRect(r, radius, radius)
        p.fillPath(outer, QColor(66, 40, 22))
        face = r.adjusted(3, 3, -3, -3)
        fp = QPainterPath(); fp.addRoundedRect(face, face.height() / 2, face.height() / 2)
        grad = QLinearGradient(face.topLeft(), face.bottomLeft())
        light = 14 if self._hover else 0
        grad.setColorAt(0.0, QColor(184, 130, 78).lighter(100 + light))
        grad.setColorAt(0.5, QColor(150, 99, 55).lighter(100 + light))
        grad.setColorAt(1.0, QColor(110, 70, 38).lighter(100 + light))
        p.fillPath(fp, QBrush(grad))
        p.setPen(QPen(QColor(214, 168, 112, 150), 1.3)); p.drawPath(fp)
        p.setPen(QColor(0, 0, 0, 110)); p.setFont(QFont("Georgia", 12, QFont.Bold))
        p.drawText(self.rect().translated(0, sink - 1), Qt.AlignCenter, self.text)
        p.setPen(QColor(255, 246, 228))
        p.drawText(self.rect().translated(0, sink), Qt.AlignCenter, self.text)
        p.end()


# ── End overlay (win = confetti, loss = broken hearts) ───────────────────
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
        w = self.parent().width() if self.parent() else 940
        h = self.parent().height() if self.parent() else 660
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
        self._t += 0.05
        wh = self.height() or 660
        grav = 0.04 if self.won else 0.015
        for p in self._pieces:
            p["x"] += p["vx"]; p["y"] += p["vy"]; p["vy"] += grav; p["angle"] += p["spin"]
            if p["y"] > wh + 30:
                p["y"] = _random.uniform(-60, -10)
                p["x"] = _random.uniform(0, self.width() or 940)
                p["vy"] = _random.uniform(2.6, 5.2) if self.won else _random.uniform(1.4, 2.8)
        self.update()

    def _tick_count(self):
        self._secs_left = max(0, self._secs_left - 1); self.update()

    def _draw_broken_heart(self, p, size, color):
        s = size
        p.setBrush(color); p.setPen(Qt.NoPen)
        path = QPainterPath()
        path.moveTo(0, s * 0.32)
        path.cubicTo(-s * 0.1, s * 0.05, -s * 0.5, s * 0.05, -s * 0.5, -s * 0.18)
        path.cubicTo(-s * 0.5, -s * 0.42, -s * 0.18, -s * 0.46, 0, -s * 0.22)
        path.lineTo(-s * 0.06, -s * 0.05); path.lineTo(s * 0.05, s * 0.06)
        path.lineTo(-s * 0.04, s * 0.16); path.closeSubpath()
        p.drawPath(path)
        path2 = QPainterPath()
        path2.moveTo(s * 0.04, s * 0.34)
        path2.cubicTo(s * 0.14, s * 0.07, s * 0.54, s * 0.07, s * 0.54, -s * 0.16)
        path2.cubicTo(s * 0.54, -s * 0.40, s * 0.22, -s * 0.44, s * 0.04, -s * 0.20)
        path2.lineTo(s * 0.12, -s * 0.05); path2.lineTo(s * 0.01, s * 0.06)
        path2.lineTo(s * 0.10, s * 0.18); path2.closeSubpath()
        p.drawPath(path2)

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
        bob = math.sin(self._t * 2.0) * 4
        cd = 64; coin = QRectF(r.center().x() - cd / 2, r.top() + 48 + bob, cd, cd)
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
                   "Try the sequence game and earn some coins.")
        p.setPen(QColor(150, 110, 70)); p.setFont(QFont("Georgia", 11, -1, True))
        msg = "Heading back…" if self._secs_left <= 1 else "Back to your cards soon…"
        p.drawText(QRectF(r.left(), r.bottom() - 42, r.width(), 24), Qt.AlignCenter, msg)


# ── Choice Panel ─────────────────────────────────────────────────────────
class ChoicePanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("side_panel"); self.setFixedWidth(210)
        self._lay = QVBoxLayout(self); self._lay.setContentsMargins(16, 20, 16, 20); self._lay.setSpacing(12)
        self._title = QLabel("SELECT CELL"); self._title.setWordWrap(True); self._title.setAlignment(Qt.AlignCenter)
        self._title.setStyleSheet(f"font-size:11px; font-weight:bold; color:{P['text_dim']}; letter-spacing:1px;")
        self._lay.addWidget(self._title)
        self._desc = QLabel("Click an empty slot on the grid to choose a value.")
        self._desc.setWordWrap(True); self._desc.setAlignment(Qt.AlignCenter)
        self._desc.setStyleSheet(f"font-size:11px; color:{P['text_dim']};")
        self._lay.addWidget(self._desc)
        self._btn_container = QWidget(); self._btn_lay = QVBoxLayout(self._btn_container)
        self._btn_lay.setContentsMargins(0, 10, 0, 0); self._btn_lay.setSpacing(8)
        self._lay.addWidget(self._btn_container); self._lay.addStretch()
        self._btn_container.setVisible(False); self._on_pick = None

    def show_choices(self, subj, attr, options, used, on_pick):
        self._on_pick = on_pick
        self._title.setText(f"{subj.upper()}\n({attr.upper()})")
        self._title.setStyleSheet(f"font-size:12px; font-weight:bold; color:{P['accent_deep']};")
        self._desc.setText("Select the correct value:")
        while self._btn_lay.count():
            it = self._btn_lay.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        for val in options:
            btn = QPushButton(val); btn.setObjectName("pill"); btn.setFixedHeight(36); btn.setCursor(Qt.PointingHandCursor)
            if val in used: btn.setDisabled(True)
            else: btn.clicked.connect(lambda _, v=val, s=subj, a=attr: self._on_pick(s, a, v))
            self._btn_lay.addWidget(btn)
        self._btn_container.setVisible(True)

    def clear_panel(self):
        self._title.setText("SELECT CELL")
        self._title.setStyleSheet(f"font-size:11px; font-weight:bold; color:{P['text_dim']}; letter-spacing:1px;")
        self._desc.setText("Click an empty slot on the grid to choose a value.")
        self._btn_container.setVisible(False)


# ── Cell Widget ──────────────────────────────────────────────────────────
class CellWidget(QFrame):
    STATES = {
        "idle":    (P["cell_idle"],    P["border"],      P["text_dim"],    "1px"),
        "active":  (P["cell_active"],  P["accent"],      P["accent_deep"], "2px"),
        "correct": (P["cell_correct"], P["correct"],     P["correct"],     "2px"),
        "wrong":   (P["cell_wrong"],   P["wrong"],       P["wrong"],       "2px"),
        "reveal":  (P["cell_reveal"],  P["accent"],      P["text_body"],   "1px"),
    }

    def __init__(self, subj, attr, on_clicked, parent=None):
        super().__init__(parent)
        self.subj = subj; self.attr = attr; self._on_clicked = on_clicked; self._state = "idle"
        self.setFixedSize(152, 64); self.setCursor(Qt.PointingHandCursor)
        lay = QVBoxLayout(self); lay.setContentsMargins(6, 4, 6, 4)
        self.lbl = QLabel("", self); self.lbl.setAlignment(Qt.AlignCenter); self.lbl.setWordWrap(True)
        lay.addWidget(self.lbl, alignment=Qt.AlignCenter); self._apply("idle")

    def _apply(self, state):
        self._state = state; bg, border, fg, bw = self.STATES[state]
        bold = "bold" if state in ("correct", "reveal", "active") else "normal"
        size = "11px" if state in ("correct", "reveal") else "10px"
        self.setStyleSheet(f"QFrame {{ background:{bg}; border:{bw} solid {border}; border-radius:8px; }}")
        self.lbl.setStyleSheet(f"color:{fg}; font-size:{size}; font-weight:{bold};")

    def set_value(self, text, state): self.lbl.setText(text); self._apply(state)
    def select_cell(self):
        if self._state in ("idle", "active"): self._apply("active")
    def deselect_cell(self):
        if self._state == "active": self._apply("idle")
    def flash_wrong(self, bad_val):
        self.lbl.setText(bad_val); self._apply("wrong")
        QTimer.singleShot(850, lambda: self.set_value("", "idle"))
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton: self._on_clicked(self)


# ── Main puzzle window ───────────────────────────────────────────────────
class MainWindow(QMainWindow):
    completed = Signal(int)

    def __init__(self, data=None, coins=DEFAULT_COINS, game=None, return_cb=None):
        super().__init__()
        self.game = game
        self.return_cb = return_cb
        self.coins_award = int(coins)
        self.setWindowTitle("Logigrame")
        self.setFixedSize(940, 660)
        self.setStyleSheet(SS)

        d = data or DEFAULT_DATA
        self.subtitle   = d.get("subtitle", "")
        self.subjects   = d["subjects"]
        self.attributes = d["attributes"]
        self.options    = d["options"]
        self.solution   = parse_solution(d["solution"])
        self.clues      = d["clues"]

        self.filled = {}
        self.lives = MAX_LIVES
        self.game_over = False
        self.active_cell = None
        self._finished = False

        self.choice_panel = ChoicePanel(self)
        self._build_ui()

    def _build_ui(self):
        root = QWidget(); root.setObjectName("root"); self.setCentralWidget(root)
        root_lay = QVBoxLayout(root); root_lay.setContentsMargins(0, 0, 0, 0); root_lay.setSpacing(0)
        root_lay.addWidget(self._make_header())
        workspace = QHBoxLayout(); workspace.setContentsMargins(28, 20, 28, 24); workspace.setSpacing(20)
        left = QVBoxLayout(); left.setSpacing(16)
        left.addWidget(self._make_grid_card())
        self.status_lbl = QLabel("Read the clues, then click an empty slot to fill it in.")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet(f"font-size:12px; color:{P['text_dim']};")
        left.addWidget(self.status_lbl)
        left.addWidget(self._make_clues_card())
        workspace.addLayout(left, stretch=1)
        workspace.addWidget(self.choice_panel)
        root_lay.addLayout(workspace)

    def _make_header(self):
        hdr = QFrame(); hdr.setObjectName("header"); hdr.setFixedHeight(62)
        lay = QHBoxLayout(hdr); lay.setContentsMargins(24, 0, 20, 0)
        title = QLabel("LOGIGRAME")
        title.setStyleSheet(f"font-size:20px; font-weight:bold; color:{P['accent']}; letter-spacing:2px;")
        lay.addWidget(title)
        sub = QLabel(self.subtitle); sub.setStyleSheet(f"font-size:11px; color:{P['text_dim']};")
        lay.addWidget(sub); lay.addStretch()
        self.heart_labels = []
        for _ in range(MAX_LIVES):
            h = QLabel("\u2665"); h.setStyleSheet(f"font-size:20px; color:{P['heart_on']};")
            lay.addWidget(h); self.heart_labels.append(h)
        self.exit_btn = WoodenButton("Exit")
        self.exit_btn.clicked.connect(lambda: self._finish(won=False, award=False))
        lay.addSpacing(14); lay.addWidget(self.exit_btn)
        return hdr

    def _make_grid_card(self):
        card = QFrame(); card.setObjectName("grid_card")
        lay = QVBoxLayout(card); lay.setContentsMargins(20, 16, 20, 20); lay.setSpacing(10)
        sec = QLabel("\u25b8  PROFILES")
        sec.setStyleSheet(f"font-size:10px; font-weight:bold; color:{P['text_dim']}; letter-spacing:1px;")
        lay.addWidget(sec)
        grid = QGridLayout(); grid.setSpacing(8)
        corner = QLabel(); corner.setFixedWidth(120); grid.addWidget(corner, 0, 0)
        for c, subj in enumerate(self.subjects):
            lbl = QLabel(subj); lbl.setAlignment(Qt.AlignCenter); lbl.setFixedWidth(152)
            lbl.setStyleSheet(f"font-size:14px; font-weight:bold; color:{P['text_strong']};")
            grid.addWidget(lbl, 0, c + 1)
        div = QFrame(); div.setFixedHeight(1); div.setStyleSheet(f"background:{P['divider']};")
        grid.addWidget(div, 1, 0, 1, len(self.subjects) + 1)
        self.cell_widgets = {}
        for r, attr in enumerate(self.attributes):
            rl = QLabel(attr); rl.setAlignment(Qt.AlignRight | Qt.AlignVCenter); rl.setFixedWidth(120)
            rl.setStyleSheet(f"font-size:11px; color:{P['text_body']}; padding-right:12px;")
            grid.addWidget(rl, r + 2, 0)
            for c, subj in enumerate(self.subjects):
                cell = CellWidget(subj, attr, on_clicked=self._cell_clicked)
                grid.addWidget(cell, r + 2, c + 1, Qt.AlignCenter)
                self.cell_widgets[(subj, attr)] = cell
        lay.addLayout(grid)
        return card

    def _make_clues_card(self):
        card = QFrame(); card.setObjectName("clue_card")
        outer = QVBoxLayout(card); outer.setContentsMargins(20, 14, 20, 14); outer.setSpacing(8)
        sec = QLabel("\u25b8  CLUES")
        sec.setStyleSheet(f"font-size:10px; font-weight:bold; color:{P['text_dim']}; letter-spacing:1px;")
        outer.addWidget(sec)
        grid_clues = QGridLayout(); grid_clues.setSpacing(8)
        for i, clue in enumerate(self.clues):
            icon, tag, text = clue[0], clue[1], clue[2]
            row = QFrame(); row.setObjectName("clue_row")
            rl = QHBoxLayout(row); rl.setContentsMargins(12, 8, 12, 8); rl.setSpacing(10)
            il = QLabel(icon); il.setStyleSheet("font-size:16px;"); il.setFixedWidth(24); rl.addWidget(il)
            tc = QVBoxLayout(); tc.setSpacing(1)
            tl = QLabel(tag); tl.setStyleSheet(f"font-size:9px; font-weight:bold; color:{P['accent_deep']}; letter-spacing:0.5px;")
            tc.addWidget(tl)
            bl = QLabel(text); bl.setWordWrap(True); bl.setStyleSheet(f"font-size:11px; color:{P['text_body']};")
            tc.addWidget(bl); rl.addLayout(tc)
            grid_clues.addWidget(row, i // 2, i % 2)
        outer.addLayout(grid_clues)
        return card

    def _used(self, attr):
        return {v for (s, a), v in self.filled.items() if a == attr}

    def _cell_clicked(self, cell):
        if self.game_over or (cell.subj, cell.attr) in self.filled: return
        if self.active_cell: self.active_cell.deselect_cell()
        self.active_cell = cell; cell.select_cell()
        self.choice_panel.show_choices(cell.subj, cell.attr, self.options[cell.attr], self._used(cell.attr), self._on_pick)
        self.status_lbl.setText(f"Choose a value for {cell.subj} ({cell.attr}).")
        self.status_lbl.setStyleSheet(f"font-size:12px; color:{P['accent_deep']};")

    def _on_pick(self, subj, attr, val):
        if self.game_over or not self.active_cell: return
        cell = self.active_cell; self.active_cell = None; self.choice_panel.clear_panel()
        if val == self.solution[(subj, attr)]:
            self.filled[(subj, attr)] = val
            cell.set_value(val, "correct")
            self.status_lbl.setText(f"\u2713 {subj} \u00b7 {attr} = {val}")
            self.status_lbl.setStyleSheet(f"font-size:12px; color:{P['correct']};")
            if len(self.filled) == len(self.subjects) * len(self.attributes):
                QTimer.singleShot(350, self._win_celebrate)
        else:
            self.lives -= 1
            idx = MAX_LIVES - self.lives - 1
            if 0 <= idx < len(self.heart_labels):
                self.heart_labels[idx].setStyleSheet(f"font-size:20px; color:{P['heart_off']};")
            cell.flash_wrong(val)
            msg = f"\u2717 {val} isn't right for {subj}."
            if self.lives == 1: msg += "  \u26a0 Last life!"
            self.status_lbl.setText(msg)
            self.status_lbl.setStyleSheet(f"font-size:12px; color:{P['wrong']};")
            if self.lives <= 0:
                QTimer.singleShot(900, self._do_game_over)

    def _win_celebrate(self):
        self.game_over = True; self.choice_panel.clear_panel()
        self.status_lbl.setText("\u2713 Solved! Wonderful.")
        self.status_lbl.setStyleSheet(f"font-size:12px; color:{P['correct']};")
        self._overlay = EndOverlay(won=True, coins=self.coins_award, parent=self)
        self._overlay.setGeometry(0, 0, self.width(), self.height())
        self._overlay.show(); self._overlay.raise_()
        QTimer.singleShot(5000, lambda: self._finish(won=True, award=True))

    def _do_game_over(self):
        self.game_over = True; self.choice_panel.clear_panel()
        for (s, a), v in self.solution.items():
            if (s, a) not in self.filled:
                self.cell_widgets[(s, a)].set_value(v, "reveal")
        self.status_lbl.setText("\U0001f494 Out of lives \u2014 here was the answer.")
        self.status_lbl.setStyleSheet(f"font-size:12px; color:{P['wrong']};")
        QTimer.singleShot(700, self._show_loss_overlay)

    def _show_loss_overlay(self):
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
    win = MainWindow()   # standalone uses DEFAULT_DATA
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()