"""
Profile Perfect — Skincare Edition  (PySide6)
==============================================
Infinite Replayability Edition (Crash-Free Side Panel Architecture)
"""

import sys
import random
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QStackedWidget,
    QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui  import QCursor

MAX_LIVES = 2

# ── Palette ────────────────────────────────────────────────────────────────
P = {
    "bg":           "#FAF7F2",
    "bg_card":      "#FFFFFF",
    "bg_panel":     "#F3EDE4",
    "bg_header":    "#F9F0E8",
    "border":       "#E2D5C8",
    "border_dark":  "#C8B8A8",

    "cell_idle":    "#FFFFFF",
    "cell_active":  "#FFF5EC",
    "cell_correct": "#E6F7EE",
    "cell_wrong":   "#FDEAEA",
    "cell_locked":  "#EEF4FF",

    "panel_border": "#D4845A",
    "pill_idle":    "#FAF7F2",
    "pill_hover":   "#FDEBD8",
    "pill_used_bg": "#F0EDE9",
    "pill_used_fg": "#B0A098",

    "accent":       "#D4845A",
    "correct":      "#2E9E62",
    "wrong":        "#D44F4F",
    "locked_fg":    "#4A80CC",

    "text_strong":  "#2C2420",
    "text_body":    "#5A4E47",
    "text_dim":     "#9E8E85",
    "text_white":   "#FFFFFF",
    "heart_on":     "#E8607A",
    "heart_off":    "#DDD0C8",
    "divider":      "#EDE5DC",
}

# ── Theme Pool ─────────────────────────────────────────────────────────────
THEME_POOL = [
    # {
    #     "subtitle": "Morning Routines",
    #     "subjects": ["Serena", "Maya", "Priya"],
    #     "attributes": ["Skin Type", "Routine Step", "Hero Ingredient"],
    #     "options": {
    #         "Skin Type":        ["Oily", "Dry", "Sensitive"],
    #         "Routine Step":     ["Moisturise", "Exfoliate", "Cleanse"],
    #         "Hero Ingredient":  ["Niacinamide", "Hyaluronic Acid", "Centella Asiatica"],
    #     },
    #     "clue_templates": [
    #         ("✨", "Direct", "Midday T-zone shine confirms {Serena} manages {Skin Type:Serena} skin."),
    #         ("💧", "Linked", "The individual handling {Routine Step} relies on {Hero Ingredient} matching context."),
    #         ("🫧", "Linked", "Addressing {Skin Type} with {Hero Ingredient} keeps the barrier resilient."),
    #     ]
    # },
    # {
    #     "subtitle": "Night Treatments",
    #     "subjects": ["Zara", "Lena", "Aisha"],
    #     "attributes": ["Skin Concern", "Treatment", "Active Ingredient"],
    #     "options": {
    #         "Skin Concern":      ["Acne", "Hyperpigmentation", "Anti-Ageing"],
    #         "Treatment":         ["Face Mask", "Facial Oil", "Serum"],
    #         "Active Ingredient": ["Salicylic Acid", "Vitamin C", "Retinol"],
    #     },
    #     "clue_templates": [
    #         ("🌿", "Linked", "Targeting {Skin Concern} effectively requires applying a custom evening {Treatment}."),
    #         ("🍊", "Direct", "{Active Ingredient:Lena} is carefully integrated into {Lena}'s skincare regimen."),
    #         ("⏳", "Linked", "The profile dealing with {Skin Concern} pairs perfectly with {Active Ingredient}."),
    #     ]
    # },
    {
        "subtitle": "Sun Protection",
        "subjects": ["Leo", "Chloe", "Zane"],
        "attributes": ["UV Focus", "Formulation", "Active Filter"],
        "options": {
            "UV Focus":       ["Daily Wear", "Sport/Water", "Sensitive Scalp"],
            "Formulation":    ["Matte Fluid", "Gel-Cream", "Clear Stick"],
            "Active Filter":  ["Zinc Oxide", "Titanium Dioxide", "Tinosorb S"],
        },
        "clue_templates": [
            ("☀️", "Direct", "{Chloe} specifically opted for a specialized {Formulation:Chloe} base."),
            ("🌊", "Linked", "The {UV Focus} protection routine is delivered via an elegant {Formulation} format."),
            ("🔬", "Linked", "Formulating for {UV Focus} demands using mineral-based {Active Filter} filters."),
        ]
    }
]

def generate_procedural_level(theme_data, level_number):
    shuffled = {
        "title": f"Level {level_number}",
        "subtitle": theme_data["subtitle"],
        "subjects": list(theme_data["subjects"]),
        "attributes": list(theme_data["attributes"]),
        "options": {},
        "solution": {}
    }
    
    for attr in shuffled["attributes"]:
        opts = list(theme_data["options"][attr])
        random.shuffle(opts)
        shuffled["options"][attr] = opts
        
        for i, subj in enumerate(shuffled["subjects"]):
            shuffled["solution"][(subj, attr)] = opts[i]
            
    l_subj = random.choice(shuffled["subjects"])
    l_attr = random.choice(shuffled["attributes"])
    l_val = shuffled["solution"][(l_subj, l_attr)]
    shuffled["locked"] = (l_subj, l_attr, l_val)
    
    clues = [("🔒", "Pre-filled", f"{l_subj}'s documentation confirms their {l_attr} is {l_val}.")]
    
    sol = shuffled["solution"]
    subjs = shuffled["subjects"]
    attrs = shuffled["attributes"]
    
    for icon, tag, template in theme_data["clue_templates"]:
        text = template
        
        for s in subjs:
            for a in attrs:
                placeholder = f"{{{a}:{s}}}"
                if placeholder in text:
                    text = text.replace(placeholder, sol[(s, a)])
                    
        for s in subjs:
            text = text.replace(f"{{{s}}}", s)
            
        idx = random.randint(0, len(subjs) - 1)
        for a in attrs:
            text = text.replace(f"{{{a}}}", sol[(subjs[idx], a)])
            
        clues.append((icon, tag, text))
        
    shuffled["clues"] = clues
    return shuffled

# ── Stylesheet ─────────────────────────────────────────────────────────────
SS = f"""
QMainWindow, QWidget#root {{
    background: {P['bg']};
}}
QLabel {{ background: transparent; color: {P['text_body']}; }}

QFrame#header {{
    background: {P['bg_header']};
    border-bottom: 1px solid {P['border']};
}}
QFrame#grid_card {{
    background: {P['bg_card']};
    border: 1px solid {P['border']};
    border-radius: 12px;
}}
QFrame#side_panel {{
    background: {P['bg_card']};
    border: 1px solid {P['border']};
    border-radius: 12px;
}}
QFrame#clue_card {{
    background: {P['bg_card']};
    border: 1px solid {P['border']};
    border-radius: 10px;
}}
QFrame#clue_row {{
    background: {P['bg_panel']};
    border: 1px solid {P['border']};
    border-radius: 8px;
}}
QPushButton#pill {{
    background: {P['pill_idle']};
    color: {P['text_strong']};
    border: 1.5px solid {P['border_dark']};
    border-radius: 14px;
    padding: 6px 14px;
    font-size: 12px;
    text-align: center;
}}
QPushButton#pill:hover {{
    background: {P['pill_hover']};
    border-color: {P['accent']};
    color: {P['accent']};
}}
QPushButton#pill:disabled {{
    background: {P['pill_used_bg']};
    color: {P['pill_used_fg']};
    border-color: {P['border']};
}}
QPushButton#nav_btn {{
    background: {P['accent']};
    color: {P['text_white']};
    border: none;
    border-radius: 8px;
    padding: 9px 28px;
    font-size: 13px;
    font-weight: bold;
}}
QPushButton#nav_btn:hover {{ background: #C07040; }}
"""

# ── Choice Panel ────────────────────────────────────────────────────────────
class ChoicePanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("side_panel")
        self.setFixedWidth(210)
        
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(16, 20, 16, 20)
        self._lay.setSpacing(12)

        self._title = QLabel("SELECT CELL")
        self._title.setWordWrap(True)
        self._title.setAlignment(Qt.AlignCenter)
        self._title.setStyleSheet(
            f"font-size:11px; font-weight:bold; color:{P['text_dim']};"
            f" letter-spacing:1px;")
        self._lay.addWidget(self._title)

        self._desc = QLabel("Click an empty profile slot on the grid to choose an attribute.")
        self._desc.setWordWrap(True)
        self._desc.setAlignment(Qt.AlignCenter)
        self._desc.setStyleSheet(f"font-size:11px; color:{P['text_dim']}; line-height:14px;")
        self._lay.addWidget(self._desc)

        self._btn_container = QWidget()
        self._btn_lay = QVBoxLayout(self._btn_container)
        self._btn_lay.setContentsMargins(0, 10, 0, 0)
        self._btn_lay.setSpacing(8)
        
        self._container_wrapper = self._btn_container
        self._lay.addWidget(self._btn_container)
        
        self._lay.addStretch()
        self._container_wrapper.setVisible(False)
        self._on_pick = None

    def show_choices(self, subj: str, attr: str, options: list[str], used: set, on_pick):
        self._on_pick = on_pick
        self._title.setText(f"{subj.upper()}\n({attr.upper()})")
        self._title.setStyleSheet(f"font-size:12px; font-weight:bold; color:{P['accent']}; text-align:center;")
        self._desc.setText("Select the correct value:")
        
        while self._btn_lay.count():
            item = self._btn_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for val in options:
            btn = QPushButton(val)
            btn.setObjectName("pill")
            btn.setFixedHeight(36)
            btn.setCursor(Qt.PointingHandCursor)
            if val in used:
                btn.setDisabled(True)
            else:
                btn.clicked.connect(lambda _, v=val, s=subj, a=attr: self._on_pick(s, a, v))
            self._btn_lay.addWidget(btn)

        self._container_wrapper.setVisible(True)

    def clear_panel(self):
        self._title.setText("SELECT CELL")
        self._title.setStyleSheet(f"font-size:11px; font-weight:bold; color:{P['text_dim']}; letter-spacing:1px;")
        self._desc.setText("Click an empty profile slot on the grid to choose an attribute.")
        self._container_wrapper.setVisible(False)


# ── Cell Widget ─────────────────────────────────────────────────────────────
class CellWidget(QFrame):
    STATES = {
        "idle":    (P["cell_idle"],    P["border"],      P["text_dim"],    "1px"),
        "active":  (P["cell_active"],  P["accent"],      P["accent"],      "2px"),
        "correct": (P["cell_correct"], P["correct"],     P["correct"],     "2px"),
        "wrong":   (P["cell_wrong"],   P["wrong"],       P["wrong"],       "2px"),
        "locked":  (P["cell_locked"],  P["locked_fg"],   P["locked_fg"],   "1.5px"),
        "reveal":  ("#FFF8EE",         P["accent"],      P["text_body"],   "1px"),
    }

    def __init__(self, subj, attr, on_clicked, parent=None):
        super().__init__(parent)
        self.subj        = subj
        self.attr        = attr
        self._on_clicked = on_clicked
        self._state      = "idle"
        self.locked      = False

        self.setFixedSize(152, 64)
        self.setCursor(Qt.PointingHandCursor)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 4, 6, 4)
        self.lbl = QLabel("", self)
        self.lbl.setAlignment(Qt.AlignCenter)
        self.lbl.setWordWrap(True)
        lay.addWidget(self.lbl, alignment=Qt.AlignCenter)

        self._apply("idle")

    def _apply(self, state: str):
        self._state = state
        bg, border, fg, bw = self.STATES[state]
        bold = "bold" if state in ("correct", "locked", "reveal", "active") else "normal"
        size = "11px" if state in ("correct", "locked", "reveal") else "10px"
        self.setStyleSheet(f"QFrame {{ background:{bg}; border:{bw} solid {border}; border-radius:8px; }}")
        self.lbl.setStyleSheet(f"color:{fg}; font-size:{size}; font-weight:{bold};")

    def set_value(self, text: str, state: str):
        self.lbl.setText(text)
        self._apply(state)

    def select_cell(self):
        if not self.locked and self._state in ("idle", "active"):
            self._apply("active")

    def deselect_cell(self):
        if not self.locked and self._state == "active":
            self._apply("idle")

    def flash_wrong(self, bad_val: str):
        self.lbl.setText(bad_val)
        self._apply("wrong")
        QTimer.singleShot(850, lambda: self.set_value("", "idle"))

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._on_clicked(self)


# ── Level Screen ─────────────────────────────────────────────────────────────
class LevelScreen(QWidget):
    def __init__(self, ld: dict, level_index: int, on_complete, parent=None):
        super().__init__(parent)
        self.setObjectName("root")
        self.ld          = ld
        self.level_index = level_index
        self.on_complete = on_complete

        self.subjects    = ld["subjects"]
        self.attributes  = ld["attributes"]
        self.options     = ld["options"]
        self.solution    = ld["solution"]
        lk = ld["locked"]
        self.locked_subj, self.locked_attr, self.locked_val = lk

        self.filled      = {}
        self.lives       = MAX_LIVES
        self.game_over   = False
        self.active_cell = None

        # Fix: ChoicePanel is cleanly owned locally by the level screen instance
        self.choice_panel = ChoicePanel(self)

        self._build_ui()
        self._seed_locked()

    def _build_ui(self):
        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)
        root_lay.addWidget(self._make_header())

        workspace = QHBoxLayout()
        workspace.setContentsMargins(28, 20, 28, 24)
        workspace.setSpacing(20)

        left_flow = QVBoxLayout()
        left_flow.setSpacing(16)
        left_flow.addWidget(self._make_grid_card())

        self.status_lbl = QLabel("Click an empty cell slot to fill in its matrix identity.")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet(f"font-size:12px; color:{P['text_dim']};")
        left_flow.addWidget(self.status_lbl)

        left_flow.addWidget(self._make_clues_card())
        workspace.addLayout(left_flow, stretch=1)
        
        workspace.addWidget(self.choice_panel)
        root_lay.addLayout(workspace)

    def _make_header(self) -> QFrame:
        hdr = QFrame()
        hdr.setObjectName("header")
        hdr.setFixedHeight(62)
        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(28, 0, 28, 0)

        title = QLabel("PROFILE PERFECT")
        title.setStyleSheet(f"font-size:20px; font-weight:bold; color:{P['accent']};")
        lay.addWidget(title)

        sub = QLabel(f"{self.ld['title']}  ·  {self.ld['subtitle']}")
        sub.setStyleSheet(f"font-size:11px; color:{P['text_dim']};")
        lay.addWidget(sub)
        lay.addStretch()

        self.heart_labels = []
        for _ in range(MAX_LIVES):
            h = QLabel("♥")
            h.setStyleSheet(f"font-size:20px; color:{P['heart_on']};")
            lay.addWidget(h)
            self.heart_labels.append(h)

        return hdr

    def _make_grid_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("grid_card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 16, 20, 20)
        lay.setSpacing(10)

        sec = QLabel("▸  CUSTOMER PROFILES")
        sec.setStyleSheet(f"font-size:10px; font-weight:bold; color:{P['text_dim']}; letter-spacing:1px;")
        lay.addWidget(sec)

        grid = QGridLayout()
        grid.setSpacing(8)

        corner = QLabel()
        corner.setFixedWidth(120)
        grid.addWidget(corner, 0, 0)

        for c, subj in enumerate(self.subjects):
            lbl = QLabel(subj)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFixedWidth(152)
            lbl.setStyleSheet(f"font-size:14px; font-weight:bold; color:{P['text_strong']}; padding-bottom:2px;")
            grid.addWidget(lbl, 0, c + 1)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background:{P['divider']};")
        grid.addWidget(div, 1, 0, 1, len(self.subjects) + 1)

        self.cell_widgets = {}
        for r, attr in enumerate(self.attributes):
            rl = QLabel(attr)
            rl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            rl.setFixedWidth(120)
            rl.setStyleSheet(f"font-size:11px; color:{P['text_body']}; padding-right:12px;")
            grid.addWidget(rl, r + 2, 0)

            for c, subj in enumerate(self.subjects):
                cell = CellWidget(subj, attr, on_clicked=self._cell_clicked)
                if subj == self.locked_subj and attr == self.locked_attr:
                    cell.locked = True
                grid.addWidget(cell, r + 2, c + 1, Qt.AlignCenter)
                self.cell_widgets[(subj, attr)] = cell

        lay.addLayout(grid)
        return card

    def _make_clues_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("clue_card")
        outer = QVBoxLayout(card)
        outer.setContentsMargins(20, 14, 20, 14)
        outer.setSpacing(8)

        sec = QLabel("▸  CLUES")
        sec.setStyleSheet(f"font-size:10px; font-weight:bold; color:{P['text_dim']}; letter-spacing:1px;")
        outer.addWidget(sec)

        grid_clues = QGridLayout()
        grid_clues.setSpacing(8)
        for i, (icon, tag, text) in enumerate(self.ld["clues"]):
            row_f = QFrame()
            row_f.setObjectName("clue_row")
            rl = QHBoxLayout(row_f)
            rl.setContentsMargins(12, 8, 12, 8)
            rl.setSpacing(10)

            il = QLabel(icon)
            il.setStyleSheet("font-size:16px;")
            il.setFixedWidth(24)
            rl.addWidget(il)

            tc = QVBoxLayout()
            tc.setSpacing(1)
            tl = QLabel(tag)
            tl.setStyleSheet(f"font-size:9px; font-weight:bold; color:{P['accent']}; letter-spacing:0.5px;")
            tc.addWidget(tl)
            bl = QLabel(text)
            bl.setWordWrap(True)
            bl.setStyleSheet(f"font-size:11px; color:{P['text_body']};")
            tc.addWidget(bl)
            rl.addLayout(tc)
            grid_clues.addWidget(row_f, i // 2, i % 2)

        outer.addLayout(grid_clues)
        return card

    def _seed_locked(self):
        cell = self.cell_widgets[(self.locked_subj, self.locked_attr)]
        cell.set_value(self.locked_val, "locked")
        self.filled[(self.locked_subj, self.locked_attr)] = self.locked_val

    def _used(self, attr: str) -> set:
        return {v for (s, a), v in self.filled.items() if a == attr}

    def _cell_clicked(self, cell: CellWidget):
        if self.game_over or cell.locked or (cell.subj, cell.attr) in self.filled:
            return

        if self.active_cell:
            self.active_cell.deselect_cell()

        self.active_cell = cell
        cell.select_cell()

        self.choice_panel.show_choices(
            cell.subj, cell.attr,
            options=self.options[cell.attr],
            used=self._used(cell.attr),
            on_pick=self._on_pick
        )
        self.status_lbl.setText(f"Select an option from the right menu for {cell.subj} ({cell.attr})")
        self.status_lbl.setStyleSheet(f"font-size:12px; color:{P['accent']};")

    def _on_pick(self, subj: str, attr: str, val: str):
        if self.game_over or not self.active_cell:
            return

        cell = self.active_cell
        self.active_cell = None
        self.choice_panel.clear_panel()

        if val == self.solution[(subj, attr)]:
            self.filled[(subj, attr)] = val
            cell.set_value(val, "correct")
            self.status_lbl.setText(f"✓ Correct! {subj} · {attr} = {val}")
            self.status_lbl.setStyleSheet(f"font-size:12px; color:{P['correct']};")
            self._check_win()
        else:
            self.lives -= 1
            idx = MAX_LIVES - self.lives - 1
            if 0 <= idx < len(self.heart_labels):
                self.heart_labels[idx].setStyleSheet(f"font-size:20px; color:{P['heart_off']};")
            cell.flash_wrong(val)
            msg = f"✗ {val} is not right for {subj}."
            if self.lives == 1:
                msg += "  ⚠ Last life!"
            self.status_lbl.setText(msg)
            self.status_lbl.setStyleSheet(f"font-size:12px; color:{P['wrong']};")
            if self.lives <= 0:
                QTimer.singleShot(900, self._do_game_over)

    def _check_win(self):
        if len(self.filled) == len(self.subjects) * len(self.attributes):
            QTimer.singleShot(350, self._do_win)

    def _do_win(self):
        self.game_over = True
        self.choice_panel.clear_panel()
        self.on_complete(won=True, level_index=self.level_index)

    def _do_game_over(self):
        self.game_over = True
        self.choice_panel.clear_panel()
        for subj in self.subjects:
            for attr in self.attributes:
                if (subj, attr) not in self.filled:
                    self.cell_widgets[(subj, attr)].set_value(self.solution[(subj, attr)], "reveal")
        self.status_lbl.setText("💔 Out of lives — answers have been revealed.")
        self.status_lbl.setStyleSheet(f"font-size:12px; color:{P['wrong']};")
        QTimer.singleShot(2200, lambda: self.on_complete(won=False, level_index=self.level_index))


# ── Transition Screen ───────────────────────────────────────────────────────
class TransitionScreen(QWidget):
    def __init__(self, title, subtitle, body, btn_text, on_next, parent=None):
        super().__init__(parent)
        self.setObjectName("root")
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(18)

        t = QLabel(title)
        t.setAlignment(Qt.AlignCenter)
        t.setStyleSheet(f"font-size:30px; font-weight:bold; color:{P['accent']};")
        lay.addWidget(t)

        s = QLabel(subtitle)
        s.setAlignment(Qt.AlignCenter)
        s.setStyleSheet(f"font-size:13px; color:{P['text_dim']};")
        lay.addWidget(s)

        card = QFrame()
        card.setObjectName("clue_card")
        card.setFixedWidth(420)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(28, 22, 28, 22)
        bl = QLabel(body)
        bl.setWordWrap(True)
        bl.setAlignment(Qt.AlignCenter)
        bl.setStyleSheet(f"font-size:13px; color:{P['text_body']};")
        cl.addWidget(bl)
        lay.addWidget(card, alignment=Qt.AlignCenter)

        btn = QPushButton(btn_text)
        btn.setObjectName("nav_btn")
        btn.setFixedWidth(200)
        btn.clicked.connect(on_next)
        lay.addWidget(btn, alignment=Qt.AlignCenter)


# ── Main Window ──────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Profile Perfect — Skincare Edition")
        self.setMinimumSize(940, 640)
        self.setStyleSheet(SS)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self._load_level(1)

    def _load_level(self, level_num: int):
        self._clear_stack()
        
        raw_theme = random.choice(THEME_POOL)
        procedural_data = generate_procedural_level(raw_theme, level_num)
        
        # Screen now creates and handles its own local ChoicePanel instance automatically
        screen = LevelScreen(procedural_data, level_num, on_complete=self._on_complete)
        self.stack.addWidget(screen)
        self.stack.setCurrentWidget(screen)

    def _on_complete(self, won: bool, level_index: int):
        if won:
            self._show_transition(
                title    = "🎉 Level Complete!",
                subtitle = f"Prepping matrix challenge run #{level_index + 1}",
                body     = "Every single pairing matches up perfectly!\n\nLet's generate your next random combination configuration map.",
                btn_text = "Next Procedural Run →",
                on_next  = lambda: self._load_level(level_index + 1),
            )
        else:
            self._show_transition(
                title    = "💔 Out of Lives",
                subtitle = f"Matrix calculation failed on puzzle challenge #{level_index}",
                body     = "Tip: use your locked anchor cell data to calculate alignments via analytical deduction paths.",
                btn_text = "Retry Shuffled Seed",
                on_next  = lambda: self._load_level(level_index),
            )

    def _show_transition(self, title, subtitle, body, btn_text, on_next):
        self._clear_stack()
        t = TransitionScreen(title, subtitle, body, btn_text, on_next)
        self.stack.addWidget(t)
        self.stack.setCurrentWidget(t)

    def _clear_stack(self):
        while self.stack.count():
            w = self.stack.widget(0)
            self.stack.removeWidget(w)
            w.deleteLater()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()