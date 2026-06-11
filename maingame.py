from eve import Eve
from letter import Letter
import json_handling as file
from puzzles.wordpicker import WordSearchGame
from puzzles.logigrame import MainWindow
import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                             QGridLayout, QPushButton, QLabel, QHBoxLayout)
from PySide6.QtGui import QFont
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

eve=Eve(0)
index=0

letters: list[Letter]=[]
# shop_items: list[ShopItem]
# journey_df: pd.DataFrame

app = QApplication(sys.argv)
app.setStyle("Fusion")

for x in file.json_data:
    letter=Letter(x['id'], x['text'], x['hint'], x['cards'])
    letters.append(letter)

def pick_card(card):
    pass

def load_letters(i):
     print(letters[i].text)
     print("You have 3 choices to continue")

     letters[i].showCards()

def log_choice():
    pass

x=True

# Import the window class instead of the main execution bloc

def launch_skincare_logic_game():
    # Fire up the window directly
    game_window = MainWindow()
    game_window.show()
    
    sys.exit(app.exec())

def launch_wordpicker():

    game = WordSearchGame()
    game.show()
    sys.exit(app.exec())


while(x): 
 load_letters(index)
 index+=1

 choice=int(input("Select card; 1 2 3"))

 if(choice==1):
    launch_skincare_logic_game()
 elif(choice==2):
    launch_wordpicker()
 else:
    break
 
 print("-------------------------------")

 if(index==1):
    x=False
    break

            