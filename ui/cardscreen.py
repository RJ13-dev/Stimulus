# Card selection screen
# File location: STIMULUS/ui/cardscreen.py
#
# Takes (letter, game). Each card's "Solve Puzzle" routes through the game
# controller. A wooden "Exit to Lobby" button returns to the lobby and frees
# the current letter so the next "Get My Letter" draws a fresh random one.

# ── Path bootstrap ───────────────────────────────────────────────────────
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton,
                               QVBoxLayout, QGraphicsDropShadowEffect)
from PySide6.QtGui import (QPixmap, QFont, QColor, QPainter, QRadialGradient,
                           QBrush, QPen, QLinearGradient, QPainterPath)
from PySide6.QtCore import (Qt, QPropertyAnimation, QEasingCurve, QPoint,
                            QTimer, QRectF, Signal)

UI_DIR      = os.path.dirname(os.path.abspath(__file__))
BASE_DIR    = os.path.dirname(UI_DIR)
ASSET_DIR   = os.path.join(BASE_DIR, "assets")
BG_PATH     = os.path.join(ASSET_DIR, "card_screen.png")


# ─────────────────────────────────────────────────────────────────────────
#  Wooden button (matches lobby / shop / puzzle Exit style)
# ─────────────────────────────────────────────────────────────────────────
class WoodenButton(QWidget):
    clicked = Signal()

    def __init__(self, text, width=190, parent=None):
        super().__init__(parent)
        self.text = text
        self._hover = False
        self._pressed = False
        self.setFixedSize(width, 48)
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
        p.fillPath(sh, QColor(0, 0, 0, 90))
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


# ─────────────────────────────────────────────────────────────────────────
#  Redesigned Luxury Card UI
# ─────────────────────────────────────────────────────────────────────────
class PuzzleCard(QWidget):
    def __init__(self, title, text, puzzle_id, parent=None):
        super().__init__(parent)
        # Optimized sizing to comfortably sit within the 650px window height
        self.setFixedSize(300, 350)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.is_sliding = False
        self.is_hovered = False
        self.expected_center_y = 0

        # High fidelity deep atmosphere shadow
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(35)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(12)
        self.shadow.setColor(QColor(5, 2, 0, 1140))
        self.setGraphicsEffect(self.shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 36, 32, 36)
        layout.setSpacing(0)

        # Crisp, warm white title
        title_label = QLabel(title)
        title_label.setFont(QFont("Georgia", 24, QFont.Bold))
        title_label.setStyleSheet("color: #fffaf0; background: transparent; letter-spacing: 1px;")
        title_label.setAlignment(Qt.AlignCenter)

        # Elegant star separator matching the color motif
        divider = QLabel("\u2756")
        divider.setFont(QFont("Georgia", 12))
        divider.setStyleSheet("color: #e5c158; background: transparent; opacity: 0.85;")
        divider.setAlignment(Qt.AlignCenter)

        # Muted champagne text layout with tailored readability rules
        text_label = QLabel(text)
        text_label.setFont(QFont("Calibri", 13))
        text_label.setStyleSheet("""
            color: #dfd5ca; 
            background: transparent; 
            line-height: 140%;
        """)
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setWordWrap(True)

        self.puzzle_button = WoodenButton("Solve Puzzle", width=200, parent=self)
        # self.puzzle_button = QPushButton("SOLVE PUZZLE")
        # self.puzzle_button.setFont(QFont("Arial", 10, QFont.Bold))
        # self.puzzle_button.setCursor(Qt.PointingHandCursor)
        # self.puzzle_button.setMinimumHeight(44)
        
        #     QPushButton {
        #         background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        #                                     stop:0 #f3d681, stop:1 #d9b44a);
        #         color: #1a1107;
        #         border: 1px solid #b89530;
        #         border-radius: 22px;
        #         letter-spacing: 2px;
        #         font-weight: bold;
        #     }
        #     QPushButton:hover {
        #         background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        #                                     stop:0 #fff0c2, stop:1 #eac45d);
        #         color: #100a04;
        #         border: 1px solid #d4af37;
        #     }
        #     QPushButton:pressed {
        #         background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        #                                     stop:0 #d9b44a, stop:1 #b89530);
        #         padding-top: 2px;
        #     }
        # """)
        self.puzzle_button.clicked.connect(
            lambda checked=False, p_id=puzzle_id: self.window().show_puzzle(p_id))

        layout.addWidget(title_label)
        layout.addSpacing(8)
        layout.addWidget(divider)
        layout.addStretch(1)
        layout.addWidget(text_label)
        layout.addStretch(1)
        layout.addWidget(self.puzzle_button, alignment=Qt.AlignHCenter)

        self.hover_anim = QPropertyAnimation(self, b"pos")
        self.hover_anim.setDuration(200)
        self.hover_anim.setEasingCurve(QEasingCurve.OutCubic)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(2, 2, self.width() - 4, self.height() - 4)
        radius = 24

        # Premium Dark Charcoal-Amber Palette
        grad = QLinearGradient(0, rect.top(), 0, rect.bottom())
        grad.setColorAt(0.0, QColor(35, 27, 20, 240))
        grad.setColorAt(1.0, QColor(22, 17, 13, 220))

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        painter.fillPath(path, QBrush(grad))

        # Fine, high-contrast outer border
        painter.setPen(QPen(QColor(115, 95, 75, 140), 1.5))
        painter.drawPath(path)

        # Delicate internal golden accent pinstripe
        inner = QRectF(rect.left() + 6, rect.top() + 6, rect.width() - 12, rect.height() - 12)
        inner_path = QPainterPath()
        inner_path.addRoundedRect(inner, radius - 6, radius - 6)
        painter.setPen(QPen(QColor(229, 193, 88, 40), 1.0))
        painter.drawPath(inner_path)

    def enterEvent(self, event):
        if self.is_sliding:
            super().enterEvent(event); return
        self.is_hovered = True
        self.shadow.setBlurRadius(50)
        curr_x = self.pos().x()
        self.hover_anim.stop()
        self.hover_anim.setStartValue(self.pos())
        self.hover_anim.setEndValue(QPoint(curr_x, self.expected_center_y - 12))
        self.hover_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.is_sliding:
            super().leaveEvent(event); return
        self.is_hovered = False
        self.shadow.setBlurRadius(35)
        curr_x = self.pos().x()
        self.hover_anim.stop()
        self.hover_anim.setStartValue(self.pos())
        self.hover_anim.setEndValue(QPoint(curr_x, self.expected_center_y))
        self.hover_anim.start()
        super().leaveEvent(event)


class CardScreenApp(QWidget):
    def __init__(self, letter=None, game=None):
        super().__init__()
        self.letter = letter
        self.game = game
        self.setWindowTitle("Attic Puzzle Selection")
        self.resize(1000, 650)
        self.current_index = 0
        self.cards = []
        self.bulbs = []
        self.puzzle_win = None
        self.init_ui()

    def _build_card_data(self):
        return [
            ("Hard", "Play the logigrame, test your skills and get 50 coins.", 1),
            ("Medium", "Play the sequence game, test your skills and get 30 coins.", 2),
            ("Easy", "Escape from this letter but remember no coins means no shopping.", 3),
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
            QPushButton { background-color: rgba(20, 12, 4, 140); color: #e5c158;
                border: 2px solid rgba(229, 193, 88, 140); border-radius: 26px;
                font-size: 28px; font-weight: bold; padding-bottom: 5px; }
            QPushButton:hover { background-color: #e5c158;
                color: #1a1107; border: 2px solid #fff0c2; }
        """
        self.left_arrow.setFixedSize(52, 52)
        self.right_arrow.setFixedSize(52, 52)
        self.left_arrow.setStyleSheet(arrow_style)
        self.right_arrow.setStyleSheet(arrow_style)
        self.left_arrow.setCursor(Qt.PointingHandCursor)
        self.right_arrow.setCursor(Qt.PointingHandCursor)
        self.left_arrow.clicked.connect(self.show_previous_card)
        self.right_arrow.clicked.connect(self.show_next_card)

        self.exit_btn = WoodenButton("Exit to Lobby", width=190, parent=self)
        self.exit_btn.move(28, 24)
        self.exit_btn.clicked.connect(self._exit_to_lobby)
        self.exit_btn.raise_()

        self.update_card_positions(animate=False)

    def _exit_to_lobby(self):
        if self.game is not None:
            if hasattr(self.game, "finish_letter"):
                self.game.finish_letter()
            elif hasattr(self.game, "show_lobby"):
                self.game.show_lobby()
            self.close()
        else:
            print("Exit to lobby (no game controller — run via maingame.py)")

    def update_card_positions(self, animate=True, coming_from_right=True):
        card_w, card_h = 300, 350
        center_x = (self.width() - card_w) // 2
        center_y = (self.height() - card_h) // 2 + 30
        
        # Center arrows beautifully flanking the new card proportions
        self.left_arrow.move(center_x - 80, center_y + (card_h // 2) - 26)
        self.right_arrow.move(center_x + card_w + 28, center_y + (card_h // 2) - 26)

        for idx, card in enumerate(self.cards):
            card.expected_center_y = center_y
            if idx == self.current_index:
                card.show()
                card.raise_()
                if animate:
                    start_x = self.width() if coming_from_right else -card_w
                    card.move(QPoint(start_x, center_y))
                    card.is_sliding = True
                    self.anim = QPropertyAnimation(card, b"pos")
                    self.anim.setDuration(450)
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
        self.exit_btn.raise_()

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

    def show_puzzle(self, puzzle_id):
        if puzzle_id == 3:
            self._exit_to_lobby()
            return

        card = self.letter.cards[self.current_index]
        coins = card.get("coins", 0) if isinstance(card, dict) else getattr(card, "coins", 0)
        data  = card.get("data") if isinstance(card, dict) else getattr(card, "data", None)
        if self.game is not None:
            self.game.launch_puzzle(puzzle_id, coins_on_win=coins, card_data=data)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CardScreenApp()
    window.show()
    sys.exit(app.exec())