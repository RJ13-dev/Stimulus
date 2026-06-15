"""
Stimulus — Letter Screen (intro video)
File location: STIMULUS/ui/letterscreen.py

Plays a silent video of the letter sliding down, freezes on the final
frame, then fades in a "See your choices" button that advances the story.

Assets expected:
    STIMULUS/assets/letter_slide.mp4          (the video; H.264 .mp4)
    STIMULUS/assets/letter_lastframe.png       (optional fallback still)

Robustness notes:
  * Audio is muted explicitly.
  * On EndOfMedia we pause + seek near the end so the last frame holds
    instead of clearing to black.
  * If the video can't be loaded/played, we fall back to the still image
    (or just the room) and still show the button, so the game never stalls.
"""

# ── Path bootstrap (project root is two folders up from ui/) ─────────────
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QStackedLayout,
    QDialog, QVBoxLayout
)
from PySide6.QtCore import Qt, QTimer, QUrl, QRectF
from PySide6.QtGui import (
    QPixmap, QFont, QPainter, QPainterPath, QColor, QPen, QBrush, QLinearGradient
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_DIR   = os.path.join(BASE_DIR, "assets")
VIDEO_PATH  = os.path.join(ASSET_DIR, "letter_slide.mp4")
STILL_PATH  = os.path.join(ASSET_DIR, "letter_lastframe.png")  # optional fallback

W, H = 960, 640


class StyledButton(QPushButton):
    """Lamplit button, same look as the start screen's primary button."""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._hovered = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(QFont("Georgia", 15))

    def enterEvent(self, e):
        self._hovered = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hovered = False
        self.update()
        super().leaveEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(1.5, 1.5, self.width() - 3, self.height() - 3)
        radius = 12
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        grad = QLinearGradient(0, rect.top(), 0, rect.bottom())
        if self._hovered:
            grad.setColorAt(0, QColor(178, 112, 72))
            grad.setColorAt(1, QColor(132, 76, 44))
        else:
            grad.setColorAt(0, QColor(150, 90, 56))
            grad.setColorAt(1, QColor(112, 62, 36))
        p.fillPath(path, QBrush(grad))
        p.setPen(QPen(QColor(196, 112, 64, 230), 1.5))
        p.drawPath(path)
        p.setPen(QColor(255, 240, 208))
        p.setFont(self.font())
        p.drawText(self.rect(), Qt.AlignCenter, self.text())
        p.end()


class ChoicesDialog(QDialog):
    """A framed dialog that floats above the frozen video frame and shows the
    actual letter text.

    A QDialog is its own top-level OS window, so the native video surface
    can't paint over it — solving the 'invisible overlay button' problem.
    """
    def __init__(self, letter_text="", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setModal(True)
        self.setFixedSize(540, 460)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 34, 40, 30)
        lay.setSpacing(16)

        title = QLabel("A letter has arrived.")
        title.setFont(QFont("Georgia", 19, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #FFE9B0; background: transparent;")
        lay.addWidget(title)

        # ---- Letter text in a scroll area (handles long letters) ----
        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: transparent; width: 8px; margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(196,136,78,150); border-radius: 4px; min-height: 24px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        body = QLabel(letter_text or "(The letter's words are faded...)")
        body.setFont(QFont("Georgia", 13))
        body.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        body.setWordWrap(True)
        body.setStyleSheet("color: #E7CFA3; background: transparent; line-height: 150%;")
        scroll.setWidget(body)
        lay.addWidget(scroll, 1)

        self.go_btn = StyledButton("See your choices", self)
        self.go_btn.setFixedHeight(50)
        self.go_btn.clicked.connect(self.accept)   # closes dialog, returns Accepted
        lay.addWidget(self.go_btn)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(2, 2, self.width() - 4, self.height() - 4)
        path = QPainterPath()
        path.addRoundedRect(rect, 18, 18)
        grad = QLinearGradient(0, rect.top(), 0, rect.bottom())
        grad.setColorAt(0.0, QColor(46, 30, 14, 252))
        grad.setColorAt(1.0, QColor(28, 18, 8, 252))
        p.fillPath(path, QBrush(grad))
        p.setPen(QPen(QColor(196, 136, 78, 230), 2))
        p.drawPath(path)
        p.end()


class LetterScreen(QMainWindow):
    def __init__(self, game=None, letter=None):
        super().__init__()
        self.game = game
        self.letter = letter            # the Letter whose text the dialog shows
        self.setWindowTitle("Stimulus")
        self.setFixedSize(W, H)
        self._frozen = False
        self._has_played = False
        self._build()
        # Start playback shortly after show, so the widget is realised first.
        QTimer.singleShot(80, self._start_video)

    # ── UI ───────────────────────────────────────────────────────────────
    def _build(self):
        root = QWidget()
        self.setCentralWidget(root)
        root.setStyleSheet("background: #120A04;")
        self._root = root

        # Stacked layout: video at the bottom, fallback still above it.
        self.stack = QStackedLayout(root)
        self.stack.setStackingMode(QStackedLayout.StackAll)

        # ---- Video widget ----
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background: #120A04;")
        # Fill the window, cropping slightly rather than letterboxing with
        # black bars. The video is 1920x1020 (~1.88:1); the window is 1.5:1,
        # so this trims a little off the sides instead of adding bars.
        self.video_widget.setAspectRatioMode(Qt.KeepAspectRatioByExpanding)
        self.stack.addWidget(self.video_widget)

        # ---- Fallback still (shown only if the video fails) ----
        self.still_label = QLabel()
        self.still_label.setAlignment(Qt.AlignCenter)
        self.still_label.setStyleSheet("background: #120A04;")
        if os.path.exists(STILL_PATH):
            self.still_label.setPixmap(
                QPixmap(STILL_PATH).scaled(W, H, Qt.KeepAspectRatioByExpanding,
                                           Qt.SmoothTransformation))
        self.still_label.hide()
        self.stack.addWidget(self.still_label)

        # ---- Button: parented DIRECTLY to root, NOT inside the stack ----
        # QVideoWidget uses a native surface on Windows that paints over any
        # sibling inside the same stacked layout — the classic "overlay button
        # is invisible behind the video" bug. Making the button a direct child
        # of root and raising it lets it float above the video surface.
        self.choices_btn = StyledButton("See your choices", root)
        self.choices_btn.setGeometry(W // 2 - 130, H - 120, 260, 54)
        self.choices_btn.clicked.connect(self._on_choices)
        self.choices_btn.hide()
        self._btn_opacity = 0.0

        # ---- Media player ----
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.audio.setMuted(True)                 # silent, as requested
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video_widget)
        # Multiple end-detection paths — whichever fires first wins. Relying
        # on EndOfMedia alone is unreliable across Qt multimedia backends.
        self.player.mediaStatusChanged.connect(self._on_status)
        self.player.playbackStateChanged.connect(self._on_playback_state)
        self.player.positionChanged.connect(self._on_position)
        self.player.durationChanged.connect(self._on_duration)
        self.player.errorOccurred.connect(self._on_error)
        self._duration = 0
        self._guard_timer = None

    # ── Playback ───────────────────────────────────────────────────────────
    def _start_video(self):
        print(f"[letter] VIDEO_PATH = {VIDEO_PATH}")
        print(f"[letter] exists? {os.path.exists(VIDEO_PATH)}")
        if os.path.exists(VIDEO_PATH):
            self.player.setSource(QUrl.fromLocalFile(VIDEO_PATH))
            self.player.setPlaybackRate(1.5)   # play at 1.5x speed
            print("[letter] source set, rate 1.5x, calling play()")
            self.player.play()
            # Duration-INDEPENDENT safety net: even if the video never loads
            # and durationChanged never fires, force the button after 8s so
            # the game can never stall on this screen.
            self._hard_timer = QTimer(self)
            self._hard_timer.setSingleShot(True)
            self._hard_timer.timeout.connect(self._force_reveal)
            self._hard_timer.start(8000)
        else:
            print(f"[!] letter video not found at {VIDEO_PATH}")
            self._fail_to_still()

    def _force_reveal(self):
        print("[letter] hard 8s timer fired -> forcing button reveal")
        self._freeze_last_frame()

    def _on_status(self, status):
        print(f"[letter] mediaStatus -> {status}")
        if status == QMediaPlayer.EndOfMedia:
            self._freeze_last_frame()
        elif status == QMediaPlayer.InvalidMedia:
            print("[letter] INVALID MEDIA — codec/format problem")
            self._fail_to_still()

    def _on_duration(self, dur):
        print(f"[letter] duration -> {dur} ms")
        self._duration = dur
        if dur > 0 and self._guard_timer is None:
            self._guard_timer = QTimer(self)
            self._guard_timer.setSingleShot(True)
            self._guard_timer.timeout.connect(self._freeze_last_frame)
            self._guard_timer.start(dur + 300)

    def _on_position(self, pos):
        if pos > 0 and not self._has_played:
            print(f"[letter] playback started, position moving ({pos} ms)")
        if pos > 0:
            self._has_played = True
        if self._duration > 0 and pos >= self._duration - 80:
            print("[letter] position reached end -> freeze")
            self._freeze_last_frame()

    def _on_playback_state(self, state):
        print(f"[letter] playbackState -> {state}")
        if (state == QMediaPlayer.StoppedState
                and self._duration > 0
                and getattr(self, "_has_played", False)):
            print("[letter] stopped after playing -> freeze")
            self._freeze_last_frame()

    def _on_error(self, *args):
        print(f"[!] video playback error: {self.player.errorString()}")
        self._fail_to_still()

    def _freeze_last_frame(self):
        """Hold the final frame instead of clearing to black."""
        if self._frozen:
            return
        print("[letter] _freeze_last_frame -> revealing button")
        self._frozen = True
        dur = self.player.duration()
        self.player.pause()
        if dur > 0:
            self.player.setPosition(max(0, dur - 30))
        self._reveal_button()

    def _fail_to_still(self):
        """Video unavailable: show the still (or just the dark bg) + button."""
        if self._frozen:
            return
        self._frozen = True
        self.video_widget.hide()
        self.still_label.show()
        self._reveal_button()

    # ── Reveal: floating dialog above the frozen frame ─────────────────────
    def _reveal_button(self):
        print("[letter] _reveal_button -> opening choices dialog")
        if getattr(self, "_dialog_open", False):
            return
        self._dialog_open = True

        # Pull the text from the Letter. Falls back gracefully if the
        # attribute is named differently or no letter was passed.
        letter_text = ""
        if self.letter is not None:
            letter_text = (getattr(self.letter, "text", None)
                           or getattr(self.letter, "body", None)
                           or str(self.letter))

        dlg = ChoicesDialog(letter_text=letter_text, parent=self)
        geo = self.frameGeometry()
        dlg.move(geo.center().x() - dlg.width() // 2,
                 geo.center().y() - dlg.height() // 2)

        result = dlg.exec()
        if result == QDialog.Accepted:
            self._on_choices()

    # ── Advance ────────────────────────────────────────────────────────────
    def _on_choices(self):
        # Stop the player cleanly before leaving.
        self.player.stop()
        if self.game is not None:
            self.game.show_choices()    # controller opens the card screen
            self.close()
        else:
            print("See your choices. (no game controller — run via maingame.py)")


if __name__ == "__main__":
    # Standalone test (no game controller).
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    screen = LetterScreen()
    screen.show()
    sys.exit(app.exec())