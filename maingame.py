"""
Stimulus — Main entry point.

All it does now: bootstrap the path, create the ONE QApplication, build the
Game controller (which holds all state), and run the ONE event loop.
The Game object drives the screen sequence; there is no while-loop here.
"""

# ── Path bootstrap (so `from ui...` / `from puzzles...` resolve anywhere) ─
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from game import Game


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    game = Game()    # holds eve, letters, current_index — the whole session
    game.start()     # shows the start screen

    sys.exit(app.exec())   # the real loop; runs until the app quits


if __name__ == "__main__":
    main()