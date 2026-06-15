# Card selection screen
# File location: STIMULUS/ui/cardscreen.py
#
# Now takes (letter, game). Each card's "Solve Puzzle" routes its
# completion back through the game controller so the story advances.

# ── Path bootstrap ───────────────────────────────────────────────────────
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton,
                             QVBoxLayout, QGraphicsDropShadowEffect)
from PySide6.QtGui import (QPixmap, QFont, QColor, QPainter, QRadialGradient,
                           QBrush, QPen, QLinearGradient, QPainterPath)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QTimer, QRectF

UI_DIR      = os.path.dirname(os.path.abspath(__file__))
BASE_DIR    = os.path.dirname(UI_DIR)
ASSET_DIR   = os.path.join(BASE_DIR, "assets")
BG_PATH     = os.path.join(ASSET_DIR, "just-bg.png")


class PuzzleCard(QWidget):
    def __init__(self, title, text, puzzle_id, parent=None):
        super().__init__(parent)
        self.setFixedSize(360, 470)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.is_sliding = False
        self.is_hovered = False
        self.expected_center_y = 0
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(45)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(16)
        self.shadow.setColor(QColor(20, 10, 0, 190))
        self.setGraphicsEffect(self.shadow)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(34, 46, 34, 40)
        title_label = QLabel(title)
        title_label.setFont(QFont("Georgia", 22, QFont.Bold))
        title_label.setStyleSheet("color: #1a1206; background: transparent; letter-spacing: 1px;")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        divider = QLabel("\u2756")
        divider.setFont(QFont("Georgia", 14))
        divider.setStyleSheet("color: #8a6512; background: transparent;")
        divider.setAlignment(Qt.AlignCenter)
        text_label = QLabel(text)
        text_label.setFont(QFont("Calibri", 13))
        text_label.setStyleSheet("color: #2a1d08; background: transparent; line-height: 150%;")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setWordWrap(True)
        self.puzzle_button = QPushButton("Solve Puzzle")
        self.puzzle_button.setFont(QFont("Arial", 11, QFont.Bold))
        self.puzzle_button.setCursor(Qt.PointingHandCursor)
        self.puzzle_button.setStyleSheet("""
            QPushButton { background-color: #1c1206; color: #ffd167; border: none;
                border-radius: 24px; padding: 13px; letter-spacing: 2px; }
            QPushButton:hover { background-color: #33240d; color: #fff2cc; }
        """)
        self.puzzle_button.clicked.connect(
            lambda checked=False, p_id=puzzle_id: self.window().show_puzzle(p_id))
        layout.addWidget(title_label)
        layout.addSpacing(10)
        layout.addWidget(divider)
        layout.addStretch(1)
        layout.addWidget(text_label)
        layout.addStretch(1)
        layout.addWidget(self.puzzle_button)
        self.hover_anim = QPropertyAnimation(self, b"pos")
        self.hover_anim.setDuration(220)
        self.hover_anim.setEasingCurve(QEasingCurve.OutCubic)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(2, 2, self.width() - 4, self.height() - 4)
        radius = 22
        grad = QLinearGradient(0, rect.top(), 0, rect.bottom())
        grad.setColorAt(0.0, QColor(255, 224, 138))
        grad.setColorAt(0.5, QColor(255, 202, 67))
        grad.setColorAt(1.0, QColor(237, 178, 48))
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        painter.fillPath(path, QBrush(grad))
        painter.setPen(QPen(QColor(255, 233, 168), 3))
        painter.drawPath(path)
        inner = QRectF(rect.left() + 6, rect.top() + 6, rect.width() - 12, rect.height() - 12)
        inner_path = QPainterPath()
        inner_path.addRoundedRect(inner, radius - 6, radius - 6)
        painter.setPen(QPen(QColor(255, 255, 255, 90), 1.5))
        painter.drawPath(inner_path)

    def enterEvent(self, event):
        if self.is_sliding:
            super().enterEvent(event); return
        self.is_hovered = True
        self.shadow.setBlurRadius(60)
        curr_x = self.pos().x()
        self.hover_anim.stop()
        self.hover_anim.setStartValue(self.pos())
        self.hover_anim.setEndValue(QPoint(curr_x, self.expected_center_y - 14))
        self.hover_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.is_sliding:
            super().leaveEvent(event); return
        self.is_hovered = False
        self.shadow.setBlurRadius(45)
        curr_x = self.pos().x()
        self.hover_anim.stop()
        self.hover_anim.setStartValue(self.pos())
        self.hover_anim.setEndValue(QPoint(curr_x, self.expected_center_y))
        self.hover_anim.start()
        super().leaveEvent(event)


class CardScreenApp(QWidget):
    def __init__(self, letter=None, game=None):
        super().__init__()
        self.letter = letter        # the Letter whose 3 cards we show
        self.game = game            # controller for completion callbacks
        self.setWindowTitle("Attic Puzzle Selection")
        self.resize(1000, 650)
        self.current_index = 0
        self.cards = []
        self.bulbs = []
        self.puzzle_win = None
        self.init_ui()

    def _build_card_data(self):
        """Return a list of (title, text, puzzle_id) for the 3 cards.

        Default = the attic placeholder. When your Letter/Card classes are
        wired, build this from `self.letter.cards` instead, e.g.:

            data = []
            for c in self.letter.cards:
                data.append((c.title, c.text, c.puzzle_id))
            return data

        puzzle_id convention: 1 = logigrame, 2 = wordpicker, 3 = reflection.
        """
        return [
            ("The Dusty Journal", "An old leather-bound diary rests on the floorboards. The pages are brittle, but a strange riddle is scrawled across the final entry.", 1),
            ("The Locked Chest", "Tucked away in the shadow of the rafters is a heavy iron chest. Its mechanical combination lock requires a specific geometric sequence.", 2),
            ("The Attic Window", "Golden light streams through the glass panes. Dust motes dance in the air, revealing an unusual pattern etched into the wood frame.", 3),
        ]

    def init_ui(self):
        self.bg_label = QLabel(self)
        if not os.path.exists(BG_PATH):
            print(f"\u26a0\ufe0f PATH ALERT: Could not find image at {os.path.abspath(BG_PATH)}")
        self.background_pixmap = QPixmap(BG_PATH)
        self.bg_label.setPixmap(self.background_pixmap)
        self.bg_label.setScaledContents(True)
        self.vignette = QLabel(self)
        self.vignette.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.vignette.setStyleSheet("""
            background: qradialgradient(cx:0.5, cy:0.5, radius:0.75, fx:0.5, fy:0.5,
                stop:0 rgba(0,0,0,0), stop:0.65 rgba(0,0,0,40), stop:1 rgba(0,0,0,150));
        """)
        for title, text, p_id in self._build_card_data():
            card = PuzzleCard(title, text, p_id, self)
            card.hide()
            self.cards.append(card)
        
        self.left_arrow = QPushButton("\u2039", self)
        self.right_arrow = QPushButton("\u203a", self)
        arrow_style = """
            QPushButton { background-color: rgba(20, 12, 4, 110); color: #ffd167;
                border: 2px solid rgba(255, 209, 103, 160); border-radius: 26px;
                font-size: 26px; font-weight: bold; padding-bottom: 4px; }
            QPushButton:hover { background-color: rgba(255, 209, 103, 235);
                color: #1c1206; border: 2px solid #ffe6a8; }
        """
        self.left_arrow.setFixedSize(52, 52)
        self.right_arrow.setFixedSize(52, 52)
        self.left_arrow.setStyleSheet(arrow_style)
        self.right_arrow.setStyleSheet(arrow_style)
        self.left_arrow.setCursor(Qt.PointingHandCursor)
        self.right_arrow.setCursor(Qt.PointingHandCursor)
        self.left_arrow.clicked.connect(self.show_previous_card)
        self.right_arrow.clicked.connect(self.show_next_card)
        self.update_card_positions(animate=False)

    def update_card_positions(self, animate=True, coming_from_right=True):
        center_x = (self.width() - 360) // 2
        center_y = (self.height() - 470) // 2 + 40
        self.left_arrow.move(center_x - 84, center_y + 209)
        self.right_arrow.move(center_x + 360 + 32, center_y + 209)
        if len(self.bulbs) >= 6:
            self.bulbs[0].move(center_x + 125, center_y - 160)
            self.bulbs[1].move(40, 20)
            self.bulbs[2].move(self.width() - 150, 20)
            self.bulbs[3].move(200, 10)
            self.bulbs[4].move(self.width() - 310, 10)
            self.bulbs[5].move(15, 240)
            for b in self.bulbs:
                b.raise_()
        for idx, card in enumerate(self.cards):
            card.expected_center_y = center_y
            if idx == self.current_index:
                card.show()
                card.raise_()
                if animate:
                    start_x = self.width() if coming_from_right else -360
                    card.move(QPoint(start_x, center_y))
                    card.is_sliding = True
                    self.anim = QPropertyAnimation(card, b"pos")
                    self.anim.setDuration(480)
                    self.anim.setStartValue(QPoint(start_x, center_y))
                    self.anim.setEndValue(QPoint(center_x, center_y))
                    self.anim.setEasingCurve(QEasingCurve.OutQuint)
                    self.anim.finished.connect(lambda c=card: setattr(c, 'is_sliding', False))
                    self.anim.start()
                else:
                    card.is_sliding = False
                    card.move(center_x, center_y)
            else:
                card.is_sliding = False
                card.hide()
        self.left_arrow.raise_()
        self.right_arrow.raise_()

    def show_next_card(self):
        self.cards[self.current_index].hover_anim.stop()
        self.cards[self.current_index].is_sliding = True
        self.current_index = (self.current_index + 1) % len(self.cards)
        self.update_card_positions(animate=True, coming_from_right=True)

    def show_previous_card(self):
        self.cards[self.current_index].hover_anim.stop()
        self.cards[self.current_index].is_sliding = True
        self.current_index = (self.current_index - 1) % len(self.cards)
        self.update_card_positions(animate=True, coming_from_right=False)

    def resizeEvent(self, event):
        self.bg_label.resize(self.size())
        self.vignette.resize(self.size())
        self.vignette.raise_()
        self.update_card_positions(animate=False)
        super().resizeEvent(event)

    # Coin reward per card type (big puzzle / crossword / reflection).
    COINS_BY_CARD = {1: 8, 2: 5, 3: 2}

    def show_puzzle(self, puzzle_id):
        """Hand off to the game controller, which launches the puzzle and
        wires its completion back to advance the story. Standalone (no game)
        just opens the puzzle directly for visual testing."""
        coins = self.COINS_BY_CARD.get(puzzle_id, 0)

        if self.game is not None:
            self.game.launch_puzzle(puzzle_id, coins_on_win=coins)
        else:
            # No controller (running this file standalone): open directly.
            if puzzle_id == 1:
                from puzzles.logigrame import MainWindow
                self.puzzle_win = MainWindow()
            elif puzzle_id == 2:
                from puzzles.wordpicker import WordSearchGame
                self.puzzle_win = WordSearchGame()
            else:
                from puzzles.logigrame import MainWindow
                self.puzzle_win = MainWindow()
            self.puzzle_win.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CardScreenApp()   # no letter/game -> attic placeholder, direct launch
    window.show()
    sys.exit(app.exec())
