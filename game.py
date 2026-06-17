"""
Stimulus — Game controller.
File location: STIMULUS/game.py  (project root, beside maingame.py)

Flow:
    StartScreen --begin_story()--> LobbyScreen
        --"Get My Letter"--> LetterScreen (a RANDOM unused letter)
            --"See your choices"--> CardScreenApp (3 cards)
                --card chosen, puzzle solved--> returns to the card screen
        --"Shop"--> ShopScreen

Letter selection:
    Letters are served in RANDOM order with no repeats. `unused_letters`
    holds the indices not yet shown this run; each "Get My Letter" pops a
    random one into `current_index`. This is in-memory only and resets every
    run (no save file).

Screens never reference each other. They only call back into the Game.
"""

import random

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

        # ---- random, no-repeat letter selection (in memory) ----
        # Pool of letter indices not yet shown this run.
        self.unused_letters: list[int] = list(range(len(self.letters)))
        random.shuffle(self.unused_letters)
        # Which letter is currently in play. None until the first pick.
        self.current_index: int | None = None

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

    # ── Letter pool helpers ──────────────────────────────────────────────
    def _reset_letter_pool(self):
        """Refill and reshuffle the unused-letter pool (new run)."""
        self.unused_letters = list(range(len(self.letters)))
        random.shuffle(self.unused_letters)
        self.current_index = None

    def letters_remaining(self) -> int:
        return len(self.unused_letters)

    # ── Lobby (the hub) ──────────────────────────────────────────────────
    def begin_story(self):
        """Start screen -> 'Begin Eve's Story'. Fresh pool, go to the lobby."""
        self._reset_letter_pool()
        self.show_lobby()

    def continue_story(self):
        """Start screen -> 'Continue'. (Hook for save-loading later.)"""
        # TODO: load eve / unused_letters from save.json when saves exist.
        self.show_lobby()

    def show_lobby(self):
        """The attic hub. Player chooses Shop or Get My Letter from here."""
        if self.letter_screen is not None:
            self.letter_screen.close()
            self.letter_screen = None
        if self.card_screen is not None:
            self.card_screen.close()
            self.card_screen = None

        # No letters left to give -> ending.
        if not self.unused_letters:
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
        """Lobby -> 'Get My Letter'. Pick a RANDOM unused letter and play it.

        The chosen letter is removed from the pool here, so it can never be
        served again this run. The same `current_index` is reused for that
        letter's puzzles until the player moves on.
        """
        # If we don't already have a letter in play, draw a new random one.
        if self.current_index is None:
            if not self.unused_letters:
                self.show_ending()
                return
            self.current_index = self.unused_letters.pop()  # already shuffled

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
        """Letter screen -> 'See your choices'. Open the card screen.

        Also used as the puzzles' return_cb, so finishing a puzzle drops the
        player back onto the same letter's three cards.
        """
        if self.current_index is None:
            # Safety: nothing in play (e.g. came back after ending).
            self.show_lobby()
            return

        letter = self.letters[self.current_index]

        from ui.cardscreen import CardScreenApp
        self.card_screen = CardScreenApp(letter=letter, game=self)
        self.card_screen.show()

    def finish_letter(self):
        """Call when the player is DONE with the current letter and wants the
        next one. Clears current_index so the next 'Get My Letter' draws a new
        random letter, then returns to the lobby (or ending)."""
        self.current_index = None
        self.show_lobby()

    def show_ending(self):
        """All letters shown. Replace with a real end screen later."""
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

    # ── Puzzle launching ─────────────────────────────────────────────────
    def launch_puzzle(self, puzzle_id, coins_on_win=0, card_data=None):
        if self.card_screen is not None:
            self.card_screen.close()
            self.card_screen = None

        if puzzle_id == 1:        # Big -> logigrame
            from puzzles.logigrame import MainWindow
            self.puzzle_win = MainWindow(data=card_data, coins=coins_on_win,
                                         game=self, return_cb=self.show_choices)
        elif puzzle_id == 2:      # Medium -> sequence
            from puzzles.sequence_game import SequenceGame
            self.puzzle_win = SequenceGame(data=card_data, coins=coins_on_win,
                                           game=self, return_cb=self.show_choices)
        else:                     # Tiny -> reflection (later)
            from puzzles.sequence_game import SequenceGame
            self.puzzle_win = SequenceGame(data=card_data, coins=coins_on_win,
                                           game=self, return_cb=self.show_choices)

        self.puzzle_win.show()

    def on_puzzle_completed(self, coins_earned: int = 0):
        """Legacy hook. The puzzles now award coins and route back to the
        card screen themselves, so this is only used if you reconnect the
        `completed` signal to advance past a letter instead."""
        if self.puzzle_win is not None:
            self.puzzle_win.close()
            self.puzzle_win = None
        self.finish_letter()