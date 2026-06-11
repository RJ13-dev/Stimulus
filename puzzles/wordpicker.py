import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                             QGridLayout, QPushButton, QLabel, QHBoxLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class WordSearchGame(QWidget):
    def __init__(self):
        super().__init__()
        
        # 1. Game State/Logic Variables
        self.grid_data = [
            ['S', 'E', 'R', 'U'],
            ['A', 'C', 'N', 'M'],
            ['G', 'L', 'O', 'W'],
            ['H', 'B', 'Y', 'T']
        ]
        self.target_words = ["SERUM", "ACNE", "GLOW"]
        self.found_words = []
        self.current_selection = ""
        
        # 2. Setup the Window GUI
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Skincare Word Search")
        self.setStyleSheet("background-color: #FFF0F5; ") # Soft lavender/pink blush background
        
        # Main Layout (Vertical)
        main_layout = QVBoxLayout()
        
        # Top Label: Instructions / Found Words Tracker
        self.info_label = QLabel("Find hidden words: SERUM, ACNE, GLOW")
        self.info_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #4A4A4A; margin: 10px;")
        main_layout.addWidget(self.info_label)
        
        # 3. Create the Grid Layout for Letters
        grid_layout = QGridLayout()
        grid_layout.setSpacing(8)
        
        for row in range(4):
            for col in range(4):
                letter = self.grid_data[row][col]
                btn = QPushButton(letter)
                btn.setFixedSize(60, 60)
                btn.setFont(QFont("Arial", 16, QFont.Bold))
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #FFFFFF;
                        border: 2px solid #DB7093;
                        border-radius: 10px;
                        color: #333333;
                    }
                    QPushButton:pressed {
                        background-color: #FFB6C1;
                    }
                """)
                
                # Connect the click event using a lambda to pass the specific letter
                btn.clicked.connect(lambda checked, l=letter: self.letter_clicked(l))
                grid_layout.addWidget(btn, row, col)
                
        main_layout.addLayout(grid_layout)
        
        # 4. Selection Display and Control Buttons
        self.selection_label = QLabel("Selection: ")
        self.selection_label.setFont(QFont("Arial", 14))
        self.selection_label.setStyleSheet("color: #333333; margin-top: 15px;")
        main_layout.addWidget(self.selection_label)
        
        # Action Buttons Layout (Horizontal)
        action_layout = QHBoxLayout()
        
        self.check_btn = QPushButton("Check Word")
        self.check_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.check_btn.setStyleSheet("background-color: #FF69B4; color: white; padding: 10px; border-radius: 5px;")
        self.check_btn.clicked.connect(self.check_word)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setFont(QFont("Arial", 12))
        self.clear_btn.setStyleSheet("background-color: #C0C0C0; color: black; padding: 10px; border-radius: 5px;")
        self.clear_btn.clicked.connect(self.clear_selection)
        
        action_layout.addWidget(self.check_btn)
        action_layout.addWidget(self.clear_btn)
        
        main_layout.addLayout(action_layout)
        self.setLayout(main_layout)

    # 5. Event Handling Methods
    def letter_clicked(self, letter):
        self.current_selection += letter
        self.selection_label.setText(f"Selection: {self.current_selection}")
        
    def clear_selection(self):
        self.current_selection = ""
        self.selection_label.setText("Selection: ")
        
    def check_word(self):
        if self.current_selection in self.target_words:
            if self.current_selection not in self.found_words:
                self.found_words.append(self.current_selection)
                self.info_label.setText(f"Found: {', '.join(self.found_words)}")
                
                if len(self.found_words) == len(self.target_words):
                    self.info_label.setText("✨ Level Complete! Perfect Skin! ✨")
            else:
                self.info_label.setText("Already found that word!")
        else:
            self.info_label.setText("Not a hidden skincare word. Try again!")
            
        self.clear_selection()

# 6. Application Execution
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     game = WordSearchGame()
#     game.show()
#     sys.exit(app.exec())