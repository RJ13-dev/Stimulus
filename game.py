"""
Stimulus — Game controller.
File location: STIMULUS/game.py  (project root, beside maingame.py)

Flow:
    StartScreen --begin_story()--> LobbyScreen
        --"Get My Letter"--> LetterScreen (current letter)
            --"See your choices"--> CardScreenApp (3 cards)
                --card chosen, puzzle solved--> letter_complete()
                    --> back to LobbyScreen (coins updated, next letter armed)
        --"Shop"--> ShopScreen

Screens never reference each other. They only call back into the Game.
"""

from eve import Eve
from letter import Letter
import json_handling as file


class Game:
    def __init__(self):
        # ---- persistent session state ----
        self.eve = Eve(200)

        self.letters: list[Letter] = [
            Letter(x["id"], x["text"], x["hint"], x["cards"])
            for x in file.json_data
        ]

        self.current_index = 0          # which letter we're on
        self.coins_earned_this_run = 0  # optional running tally

        # ---- references to live windows (kept so they aren't GC'd) ----
        self.start_screen = None
        self.lobby_screen = None
        self.letter_screen = None
        self.card_screen = None
        self.puzzle_win = None

    # ── Entry ────────────────────────────────────────────────────────────
    def start(self):
        """Show the first screen the player sees."""
        from ui.startscreen import StartScreen
        self.start_screen = StartScreen(game=self)
        self.start_screen.show()

    # ── Lobby (the hub) ──────────────────────────────────────────────────
    def begin_story(self):
        """Start screen -> 'Begin Eve's Story'. Goes to the lobby."""
        self.current_index = 0
        self.show_lobby()

    def continue_story(self):
        """Start screen -> 'Continue'. (Hook for save-loading later.)"""
        # TODO: load self.current_index / self.eve from save.json
        self.show_lobby()

    def show_lobby(self):
        """The attic hub. Player chooses Shop or Get My Letter from here.

        Everything funnels back here: after a letter's puzzle is done, and
        after the shop closes. Closing/reopening keeps the coin badge fresh.
        """
        # Tidy any screens that brought us back here.
        if self.letter_screen is not None:
            self.letter_screen.close()
            self.letter_screen = None
        if self.card_screen is not None:
            self.card_screen.close()
            self.card_screen = None

        # If all letters are done, show the ending instead of the lobby.
        if self.current_index >= len(self.letters):
            self.show_ending()
            return

        from ui.lobbyscreen import LobbyScreen
        if self.lobby_screen is None:
            self.lobby_screen = LobbyScreen(game=self)
            self.lobby_screen.show()
        self.lobby_screen.refresh_coins()
        self.lobby_screen.show()
        self.lobby_screen.raise_()
        self.lobby_screen.activateWindow()

    # ── Story progression ────────────────────────────────────────────────
    def show_current_letter(self):
        """Lobby -> 'Get My Letter'. Play the letter for current_index.

        When the letter screen's video freezes and the player taps the
        button, it calls back to show_choices(), opening the card screen.
        """
        if self.current_index >= len(self.letters):
            self.show_ending()
            return

        # Leaving the lobby — close it so it isn't lingering behind.
        if self.lobby_screen is not None:
            self.lobby_screen.close()
            self.lobby_screen = None

        if self.card_screen is not None:
            self.card_screen.close()
            self.card_screen = None

        letter = self.letters[self.current_index]

        from ui.letterscreen import LetterScreen
        self.letter_screen = LetterScreen(game=self, letter=letter)
        self.letter_screen.show()

    def show_choices(self):
        """Letter screen -> 'See your choices'. Open the card screen."""
        if self.current_index >= len(self.letters):
            self.show_ending()
            return

        letter = self.letters[self.current_index]

        from ui.cardscreen import CardScreenApp
        self.card_screen = CardScreenApp(letter=letter, game=self)
        self.card_screen.show()

    def letter_complete(self, coins_earned: int = 0):
        """A card/puzzle finished. Bank coins, arm the next letter, and
        return the player to the lobby (NOT straight into the next letter)."""
        if coins_earned:
            self.award_coins(coins_earned)

        self.current_index += 1     # next 'Get My Letter' gives the next one

        # Whether or not letters remain, we route through the lobby.
        # show_lobby() itself shows the ending once letters run out.
        self.show_lobby()

    def show_ending(self):
        """All letters done. Replace with a real end screen later."""
        print("All letters complete! Eve's story is finished for now.")
        for w in (self.card_screen, self.letter_screen, self.lobby_screen):
            if w is not None:
                w.close()
        self.card_screen = self.letter_screen = self.lobby_screen = None
        # from ui.endscreen import EndScreen
        # self.end_screen = EndScreen(game=self)
        # self.end_screen.show()

    # ── Coins / Eve state ────────────────────────────────────────────────
    def award_coins(self, amount: int):
        """Add coins to Eve. Tries common method/attribute names."""
        self.coins_earned_this_run += amount
        if hasattr(self.eve, "earn_coins"):
            self.eve.earn_coins(amount)
        elif hasattr(self.eve, "add_coins"):
            self.eve.add_coins(amount)
        elif hasattr(self.eve, "coins"):
            self.eve.coins += amount

    # ── Puzzle launching + completion ────────────────────────────────────
    def launch_puzzle(self, puzzle_id: int, coins_on_win: int = 0):
        """Open the puzzle for a chosen card and wire its completion back
        into letter_complete(). Called by the card screen's show_puzzle()."""
        # Card screen has done its job; close it so the puzzle is alone.
        if self.card_screen is not None:
            self.card_screen.close()
            self.card_screen = None

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

        # If the puzzle exposes a `completed` signal, finishing it advances
        # the story automatically (-> letter_complete -> lobby).
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
        self.letter_complete(coins_earned)   # banks coins, returns to lobby