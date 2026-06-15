"""
Stimulus — Game controller.
File location: STIMULUS/game.py  (project root, beside maingame.py)

This object holds ALL session state and drives the screen sequence.
It replaces the old while-loop: instead of looping over letters, it keeps
`current_index` on itself and advances it whenever a letter is completed.

The flow it orchestrates:

    StartScreen --begin_story()--> CardScreenApp (letter 0)
        --card chosen, puzzle solved--> letter_complete()
        --> CardScreenApp (letter 1) --> ... --> show_ending()

Screens never reference each other. They only call back into the Game.
"""

from eve import Eve
from letter import Letter
import json_handling as file


class Game:
    def __init__(self):
        # ---- persistent session state ----
        self.eve = Eve(0)

        self.letters: list[Letter] = [
            Letter(x["id"], x["text"], x["hint"], x["cards"])
            for x in file.json_data
        ]

        self.current_index = 0          # which letter we're on (was the loop var)
        self.coins_earned_this_run = 0  # optional running tally

        # ---- references to live windows (kept so they aren't GC'd) ----
        self.start_screen = None
        self.letter_screen = None
        self.card_screen = None
        self.puzzle_win = None

    # ── Entry ────────────────────────────────────────────────────────────
    def start(self):
        """Show the first screen the player sees."""
        from ui.startscreen import StartScreen
        self.start_screen = StartScreen(game=self)
        self.start_screen.show()

    # ── Story progression ────────────────────────────────────────────────
    # Flow for each letter:
    #   show_current_letter()  -> LetterScreen (video of letter sliding down)
    #     --player clicks "See your choices"-->  show_choices()
    #   show_choices()         -> CardScreenApp (the 3 cards)
    def begin_story(self):
        """Called when the player clicks 'Begin Eve's Story'."""
        self.current_index = 0
        self.show_current_letter()

    def continue_story(self):
        """Called by the 'Continue' button. (Hook for save-loading later.)"""
        # TODO: load self.current_index / self.eve from save.json
        self.show_current_letter()

    def show_current_letter(self):
        """Play the letter video for whichever letter we're currently on.

        When the video freezes and the player taps the button, the letter
        screen calls back to show_choices(), which opens the card screen.
        """
        if self.current_index >= len(self.letters):
            self.show_ending()
            return

        # Close a previous card screen if one is lingering.
        if self.card_screen is not None:
            self.card_screen.close()
            self.card_screen = None

        letter = self.letters[self.current_index]

        from ui.letterscreen import LetterScreen
        self.letter_screen = LetterScreen(game=self, letter=letter)
        self.letter_screen.show()

    def show_choices(self):
        """Open the card screen for the current letter. Called by the
        letter screen after its video finishes and the button is clicked."""
        if self.current_index >= len(self.letters):
            self.show_ending()
            return

        letter = self.letters[self.current_index]

        from ui.cardscreen import CardScreenApp
        self.card_screen = CardScreenApp(letter=letter, game=self)
        self.card_screen.show()

    def letter_complete(self, coins_earned: int = 0):
        """A card/puzzle for the current letter finished. Advance the story.

        Called by a puzzle (via Game.on_puzzle_completed) or directly by a
        reflection card when the player is done with this letter.
        """
        if coins_earned:
            self.award_coins(coins_earned)

        self.current_index += 1         # <-- this is the old `index += 1`
        if self.current_index < len(self.letters):
            self.show_current_letter()  # <-- the loop "repeats"
        else:
            self.show_ending()          # <-- the loop condition failed

    def show_ending(self):
        """All letters done. Replace this with a real end screen later."""
        print("All letters complete! Eve's story is finished for now.")
        if self.card_screen is not None:
            self.card_screen.close()
        # from ui.endscreen import EndScreen
        # self.end_screen = EndScreen(game=self)
        # self.end_screen.show()

    # ── Coins / Eve state ────────────────────────────────────────────────
    def award_coins(self, amount: int):
        """Add coins to Eve. Tries a few common method/attribute names so
        this works whatever your Eve class looks like; adjust to match."""
        self.coins_earned_this_run += amount
        if hasattr(self.eve, "add_coins"):
            self.eve.add_coins(amount)
        elif hasattr(self.eve, "coins"):
            self.eve.coins += amount
        else:
            # Fallback: store on the game itself.
            pass

    # ── Puzzle launching + completion ────────────────────────────────────
    def launch_puzzle(self, puzzle_id: int, coins_on_win: int = 0):
        """Open the puzzle for a chosen card and wire its completion back
        into letter_complete(). Called by the card screen's show_puzzle()."""
        if puzzle_id == 1:
            from puzzles.logigrame import MainWindow
            self.puzzle_win = MainWindow()
        elif puzzle_id == 2:
            from puzzles.wordpicker import WordSearchGame
            self.puzzle_win = WordSearchGame()
        else:
            # Card 3 (reflection) placeholder until that screen exists.
            from puzzles.logigrame import MainWindow
            self.puzzle_win = MainWindow()

        # If the puzzle exposes a `completed` signal, connect it so that
        # finishing the puzzle advances the story automatically.
        if hasattr(self.puzzle_win, "completed"):
            self.puzzle_win.completed.connect(
                lambda earned=coins_on_win: self.on_puzzle_completed(earned)
            )

        self.puzzle_win.show()

    def on_puzzle_completed(self, coins_earned: int = 0):
        """Handler the puzzle's `completed` signal calls."""
        if self.puzzle_win is not None:
            self.puzzle_win.close()
            self.puzzle_win = None
        self.letter_complete(coins_earned)