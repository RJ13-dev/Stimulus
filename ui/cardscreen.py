# Dynamic tracking: looks for the "assets" folder sitting directly alongside this script file
import sys
import os
import random
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, 
                             QVBoxLayout, QGraphicsDropShadowEffect)
from PySide6.QtGui import QPixmap, QFont, QColor, QPainter, QRadialGradient, QBrush
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QTimer

UI_DIR      = os.path.dirname(os.path.abspath(__file__))
BASE_DIR    = os.path.dirname(UI_DIR) 
ASSET_DIR   = os.path.join(BASE_DIR, "assets")
BG_PATH     = os.path.join(ASSET_DIR, "card_screen.png")

class FlickeringBulb(QWidget):
    """An atmospheric, glowing ambient bulb that flickers randomly."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 100) 
        self.current_opacity = 180
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.flicker)
        self.timer.start(random.randint(50, 150))

    def flicker(self):
        base_flicker = random.choice([200, 210, 220, 230, 140, 240, 100])
        self.current_opacity = max(50, min(255, base_flicker + random.randint(-15, 15)))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        gradient = QRadialGradient(50, 50, 45)
        gradient.setColorAt(0, QColor(255, 202, 67, self.current_opacity))
        gradient.setColorAt(0.3, QColor(216, 154, 58, int(self.current_opacity * 0.5)))
        gradient.setColorAt(1, QColor(0, 0, 0, 0))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(5, 5, 90, 90)


class PuzzleCard(QWidget):
    def __init__(self, title, text, puzzle_id, parent=None):
        super().__init__(parent)
        self.setFixedSize(340, 440)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        self.is_sliding = False
        self.is_hovered = False
        self.expected_center_y = 0

        # Beautiful Window Light theme with high-contrast black text
        self.setStyleSheet("""
            PuzzleCard {
                background-color: #ffca43;
                border: 3px solid #ffe396;
                border-radius: 20px;
            }
        """)

        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(40)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(15)
        self.shadow.setColor(QColor(0, 0, 0, 180))
        self.setGraphicsEffect(self.shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 40, 30, 40)

        title_label = QLabel(title)
        title_label.setFont(QFont("Georgia", 20, QFont.Bold))
        title_label.setStyleSheet("color: #000000; border: none; background: transparent; letter-spacing: 1px;")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)

        text_label = QLabel(text)
        text_label.setFont(QFont("Calibri", 13, QFont.Bold))
        text_label.setStyleSheet("color: #111111; border: none; background: transparent; line-height: 1.5;")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setWordWrap(True)

        self.puzzle_button = QPushButton("Solve Puzzle")
        self.puzzle_button.setFont(QFont("Arial", 11, QFont.Bold))
        self.puzzle_button.setCursor(Qt.PointingHandCursor)
        self.puzzle_button.setStyleSheet("""
            QPushButton {
                background-color: #120d05;
                color: #ffca43;
                border: none;
                border-radius: 22px;
                padding: 12px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #2b200d;
                color: #ffffff;
            }
        """)
        
        self.puzzle_button.clicked.connect(lambda checked=False, p_id=puzzle_id: self.window().show_puzzle(p_id))

        layout.addWidget(title_label)
        layout.addSpacing(15)
        layout.addWidget(text_label, 1)
        layout.addWidget(self.puzzle_button)

        self.hover_anim = QPropertyAnimation(self, b"pos")
        self.hover_anim.setDuration(200)
        self.hover_anim.setEasingCurve(QEasingCurve.OutCubic)

    def enterEvent(self, event):
        if self.is_sliding:
            super().enterEvent(event)
            return

        self.is_hovered = True
        self.shadow.setBlurRadius(55)
        
        curr_x = self.pos().x()
        self.hover_anim.stop()
        self.hover_anim.setStartValue(self.pos())
        self.hover_anim.setEndValue(QPoint(curr_x, self.expected_center_y - 12))
        self.hover_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.is_sliding:
            super().leaveEvent(event)
            return

        self.is_hovered = False
        self.shadow.setBlurRadius(40)
        
        curr_x = self.pos().x()
        self.hover_anim.stop()
        self.hover_anim.setStartValue(self.pos())
        self.hover_anim.setEndValue(QPoint(curr_x, self.expected_center_y))
        self.hover_anim.start()
        super().leaveEvent(event)


class CardScreenApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Attic Puzzle Selection")
        self.resize(1000, 650)
        self.current_index = 0
        self.cards = []
        self.bulbs = []
        self.init_ui()

    def init_ui(self):
        self.bg_label = QLabel(self)
        
        # Diagnostics to make tracking problems in your terminal easy
        if not os.path.exists(BG_PATH):
            print(f"⚠️ PATH ALERT: Could not find image at {os.path.abspath(BG_PATH)}")
            print("Double check that your assets folder and file names are lower case!")
        
        self.background_pixmap = QPixmap(BG_PATH)
        self.bg_label.setPixmap(self.background_pixmap)
        self.bg_label.setScaledContents(True)

        card_data = [
            ("The Dusty Journal", "An old leather-bound diary rests on the floorboards. The pages are brittle, but a strange riddle is scrawled across the final entry.", 1),
            ("The Locked Chest", "Tucked away in the shadow of the rafters is a heavy iron chest. Its mechanical combination lock requires a specific geometric sequence.", 2),
            ("The Attic Window", "Golden light streams through the glass panes. Dust motes dance in the air, revealing an unusual pattern etched into the wood frame.", 3)
        ]

        for title, text, p_id in card_data:
            card = PuzzleCard(title, text, p_id, self)
            card.hide()
            self.cards.append(card)

        # Generate structural sequence of decorative ambient bulbs
        for _ in range(6):
            bulb = FlickeringBulb(self)
            self.bulbs.append(bulb)

        self.left_arrow = QPushButton("<", self)
        self.right_arrow = QPushButton(">", self)
        
        arrow_style = """
            QPushButton {
                background-color: rgba(255, 202, 67, 40);
                color: #ffca43;
                border: 2px solid #ffca43;
                border-radius: 25px;
                font-size: 22px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffca43;
                color: #120d05;
            }
        """
        self.left_arrow.setFixedSize(50, 50)
        self.right_arrow.setFixedSize(50, 50)
        self.left_arrow.setStyleSheet(arrow_style)
        self.right_arrow.setStyleSheet(arrow_style)
        self.left_arrow.setCursor(Qt.PointingHandCursor)
        self.right_arrow.setCursor(Qt.PointingHandCursor)

        self.left_arrow.clicked.connect(self.show_previous_card)
        self.right_arrow.clicked.connect(self.show_next_card)

        self.update_card_positions(animate=False)

    def update_card_positions(self, animate=True, coming_from_right=True):
        center_x = (self.width() - 340) // 2
        center_y = (self.height() - 440) // 2 + 40

        # Position layout navigation controls safely
        self.left_arrow.move(center_x - 80, center_y + 195)
        self.right_arrow.move(center_x + 340 + 30, center_y + 195)

        # Update decorative bulb positions dynamically across rafters
        if len(self.bulbs) >= 6:
            self.bulbs[0].move(center_x + 120, center_y - 150) 
            self.bulbs[1].move(40, 20)
            self.bulbs[2].move(self.width() - 140, 20)
            self.bulbs[3].move(200, 10)
            self.bulbs[4].move(self.width() - 300, 10)
            self.bulbs[5].move(15, 240)
            for b in self.bulbs:
                b.raise_()

        # Render active cards safely outside structural if checks
        for idx, card in enumerate(self.cards):
            card.expected_center_y = center_y 
            if idx == self.current_index:
                card.show()
                card.raise_()
                
                if animate:
                    start_x = self.width() if coming_from_right else -340
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
        self.update_card_positions(animate=False)
        super().resizeEvent(event)

    def show_puzzle(self, puzzle_id):
        print(f"Loading Puzzle Scene #{puzzle_id} Workflow Instance...")
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CardScreenApp()
    window.show()
    sys.exit(app.exec())