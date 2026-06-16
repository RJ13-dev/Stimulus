"""
Stimulus — Little Shop
File location: STIMULUS/ui/shop.py

Eve's Curated Essentials. On open, a "Welcome to the Shop" panel fades in
over the storefront, then dissolves as the item cards slide up. Each item is
a frosted translucent glass card you can hover (lift + brighten) and click to
buy — spending Eve's coins, marking it owned, updating the coin badge.

Conventions match the rest of Stimulus:
  * optional `game` controller (reads/writes game.eve)
  * runnable standalone for visual testing
  * a `closed` signal so the lobby can refresh coins on return

Background asset:  STIMULUS/assets/shop_bg.png
Item icons (optional): STIMULUS/assets/shop/<key>.png
"""

# ── Path bootstrap (this file lives in ui/, so go TWO levels up) ─────────
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QScrollArea, QGridLayout,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect
)
from PySide6.QtCore import (
    Qt, QTimer, QRectF, QPoint, Signal, QPropertyAnimation,
    QEasingCurve, QParallelAnimationGroup
)
from PySide6.QtGui import (
    QPixmap, QFont, QPainter, QPainterPath, QLinearGradient,
    QRadialGradient, QColor, QPen, QBrush
)

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_DIR = os.path.join(BASE_DIR, "assets")
BG_PATH   = os.path.join(ASSET_DIR, "shop_bg.png")
ICON_DIR  = os.path.join(ASSET_DIR, "shop")

W, H = 900, 760


# ─────────────────────────────────────────────────────────────────────────
#  Catalogue.  `effect` keys line up with letters.json room_effect names.
# ─────────────────────────────────────────────────────────────────────────
SHOP_ITEMS = [
    # --- Original Items ---
    {"key": "skincare_kit",   "name": "Glow Essence Kit",   "price": 60,  "emoji": "🧴", "effect": "clear_skin_glow"},
    {"key": "tumbler",        "name": "Floral Tumbler",     "price": 25,  "emoji": "🥤", "effect": "hydrated_vibe"},
    {"key": "watch",          "name": "Rose Gold Watch",    "price": 120, "emoji": "⌚", "effect": "elegant_wrist"},
    {"key": "makeup_palette", "name": "Pastel Makeup Set",  "price": 45,  "emoji": "🎨", "effect": "rosy_cheeks"},
    {"key": "plushie",        "name": "Cuddly Bear Toy",    "price": 30,  "emoji": "🧸", "effect": "plushie_on_bed"},
    {"key": "heels",          "name": "Starlight Shoes",    "price": 85,  "emoji": "👠", "effect": "fancy_footwear"},
    {"key": "gown",           "name": "Designer Gown",      "price": 250, "emoji": "👗", "effect": "gala_ready"},
    {"key": "perfume",        "name": "Luxury Perfume",     "price": 75,  "emoji": "🪻", "effect": "scent_trail"},
    {"key": "hair_clip",      "name": "Ribbon Bow Clip",    "price": 15,  "emoji": "🎀", "effect": "perfect_hair"},
    {"key": "mirror",         "name": "Vanity Mirror",      "price": 55,  "emoji": "🪞", "effect": "vanity_reflection"},
    {"key": "handbag",        "name": "Chic Mini Bag",      "price": 110, "emoji": "👜", "effect": "stylish_walk"},
    {"key": "sunglasses",     "name": "Cat-Eye Glasses",    "price": 40,  "emoji": "🕶️", "effect": "cool_aesthetic"},

    # --- New Added Items ---
    {"key": "claw_clip",      "name": "Matte Claw Clip",    "price": 10,  "emoji": "💇‍♀️", "effect": "cozy_updo"},
    {"key": "lip_oil",        "name": "Glossy Lip Oil",     "price": 20,  "emoji": "💄", "effect": "high_shine_smile"},
    {"key": "scrunchies",     "name": "Silk Scrunchie Set", "price": 12,  "emoji": "⭕",  "effect": "zero_crease_hair"},
    {"key": "journal",        "name": "Aesthetic Journal",  "price": 22,  "emoji": "✍️", "effect": "mindful_thoughts"},
    {"key": "jewelry_box",    "name": "Velvet Jewelry Box", "price": 35,  "emoji": "💍", "effect": "organized_sparkle"},
    {"key": "pj_set",         "name": "Satin Pajama Set",   "price": 50,  "emoji": "👚", "effect": "sleepover_chic"},
    {"key": "scented_candle", "name": "Lavender Vanilla",  "price": 18,  "emoji": "🕯️", "effect": "calming_aroma"},
    {"key": "headphones",     "name": "Pastel Headphones",  "price": 95,  "emoji": "🎧", "effect": "lofi_beats_vibe"},
    {"key": "nail_kit",       "name": "Press-On Nail Kit",  "price": 28,  "emoji": "💅", "effect": "fresh_manicure"},
    {"key": "tote_bag",       "name": "Canvas Tote Bag",    "price": 20,  "emoji": "🛍️", "effect": "thrifting_ready"},
    {"key": "body_mist",      "name": "Berry Blush Mist",   "price": 24,  "emoji": "✨", "effect": "sparkling_aura"},
    {"key": "hair_dryer",     "name": "Blowout Styler",     "price": 150, "emoji": "💨", "effect": "salon_volume"},
]


# ─────────────────────────────────────────────────────────────────────────
#  Frosted coin badge (top-right)
# ─────────────────────────────────────────────────────────────────────────
class CoinBadge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._coins = 0
        self.setFixedSize(170, 54)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def set_coins(self, value):
        self._coins = int(value); self.update()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(2, 2, self.width() - 4, self.height() - 4)
        path = QPainterPath(); path.addRoundedRect(r, 16, 16)
        p.fillPath(path, QColor(28, 18, 8, 150))        # translucent dark glass
        p.setPen(QPen(QColor(255, 226, 150, 120), 1.5)); p.drawPath(path)
        cd = 28; coin = QRectF(r.left() + 12, r.center().y() - cd / 2, cd, cd)
        cg = QRadialGradient(coin.center(), cd / 2)
        cg.setColorAt(0.0, QColor(255, 226, 140)); cg.setColorAt(1.0, QColor(214, 158, 48))
        p.setBrush(QBrush(cg)); p.setPen(QPen(QColor(150, 100, 24), 2)); p.drawEllipse(coin)
        p.setFont(QFont("Georgia", 12, QFont.Bold)); p.setPen(QColor(140, 92, 20))
        p.drawText(coin, Qt.AlignCenter, "C")
        p.setFont(QFont("Georgia", 16, QFont.Bold))
        tr = QRectF(coin.right() + 8, r.top(), r.right() - coin.right() - 12, r.height())
        p.setPen(QColor(0, 0, 0, 130)); p.drawText(tr.translated(1, 1), Qt.AlignVCenter | Qt.AlignLeft, f"{self._coins:,}")
        p.setPen(QColor(255, 246, 224)); p.drawText(tr, Qt.AlignVCenter | Qt.AlignLeft, f"{self._coins:,}")
        p.end()


# ─────────────────────────────────────────────────────────────────────────
#  Frosted glass item card — hover to lift/brighten, click to buy
# ─────────────────────────────────────────────────────────────────────────
class ItemCard(QWidget):
    buy_requested = Signal(dict)

    def __init__(self, item, parent=None):
        super().__init__(parent)
        self.item = item
        self.owned = False
        self.affordable = True
        self._hover = False
        self._pressed = False
        self.setFixedSize(180, 210)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(28)
        self._shadow.setXOffset(0)
        self._shadow.setYOffset(10)
        self._shadow.setColor(QColor(10, 6, 2, 160))
        self.setGraphicsEffect(self._shadow)

        self._icon = None
        icon_path = os.path.join(ICON_DIR, f"{item['key']}.png")
        if os.path.exists(icon_path):
            self._icon = QPixmap(icon_path)

        self._lift = QPropertyAnimation(self, b"pos")
        self._lift.setDuration(160)
        self._lift.setEasingCurve(QEasingCurve.OutCubic)
        self._base_pos = None

    def enterEvent(self, e):
        self._hover = True
        self._shadow.setBlurRadius(44)
        if self._base_pos is not None and not self.owned:
            self._lift.stop()
            self._lift.setStartValue(self.pos())
            self._lift.setEndValue(QPoint(self._base_pos.x(), self._base_pos.y() - 8))
            self._lift.start()
        self.update()

    def leaveEvent(self, e):
        self._hover = False
        self._shadow.setBlurRadius(28)
        if self._base_pos is not None:
            self._lift.stop()
            self._lift.setStartValue(self.pos())
            self._lift.setEndValue(self._base_pos)
            self._lift.start()
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and not self.owned and self.affordable:
            self._pressed = True; self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self._pressed:
            self._pressed = False; self.update()
            if self.rect().contains(e.position().toPoint()):
                self.buy_requested.emit(self.item)

    def remember_base(self):
        self._base_pos = self.pos()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(3, 3, self.width() - 6, self.height() - 6)
        radius = 18
        path = QPainterPath(); path.addRoundedRect(r, radius, radius)

        # ---- frosted glass body: translucent vertical gradient ----
        glass = QLinearGradient(r.topLeft(), r.bottomLeft())
        if self.owned:
            glass.setColorAt(0.0, QColor(255, 255, 255, 40))
            glass.setColorAt(1.0, QColor(180, 170, 150, 70))
        elif self._hover:
            glass.setColorAt(0.0, QColor(255, 250, 235, 165))
            glass.setColorAt(1.0, QColor(235, 220, 195, 120))
        else:
            glass.setColorAt(0.0, QColor(255, 250, 240, 120))
            glass.setColorAt(1.0, QColor(225, 212, 190, 90))
        p.fillPath(path, QBrush(glass))

        # top sheen — glassy highlight along the upper edge
        p.save(); p.setClipPath(path)
        sheen = QLinearGradient(r.topLeft(), QRectF(r).adjusted(0, 0, 0, -r.height() * 0.6).bottomLeft())
        sheen.setColorAt(0.0, QColor(255, 255, 255, 110))
        sheen.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.fillRect(r, QBrush(sheen))
        p.restore()

        # frosted border — brighter when hovered
        border = QColor(255, 240, 210, 220) if (self._hover and not self.owned) else QColor(255, 246, 230, 130)
        p.setPen(QPen(border, 1.6)); p.drawPath(path)

        # ---- icon recess (translucent) ----
        slot = QRectF(r.center().x() - 46, r.top() + 18, 92, 92)
        sp = QPainterPath(); sp.addRoundedRect(slot, 16, 16)
        p.fillPath(sp, QColor(255, 255, 255, 70))
        p.setPen(QPen(QColor(255, 248, 232, 120), 1.4)); p.drawPath(sp)

        if self._icon and not self._icon.isNull():
            scaled = self._icon.scaled(76, 76, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            p.drawPixmap(int(slot.center().x() - scaled.width() / 2),
                         int(slot.center().y() - scaled.height() / 2), scaled)
        else:
            p.setFont(QFont("Segoe UI Emoji", 34))
            p.setPen(QColor(90, 60, 28))
            p.drawText(slot, Qt.AlignCenter, self.item["emoji"])

        # name (dark text reads on the light frost)
        p.setFont(QFont("Georgia", 12, QFont.Bold))
        p.setPen(QColor(48, 30, 14))
        name_rect = QRectF(r.left() + 8, slot.bottom() + 8, r.width() - 16, 40)
        p.drawText(name_rect, Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, self.item["name"])

        # price pill / owned tag — translucent
        pill = QRectF(r.center().x() - 46, r.bottom() - 42, 92, 30)
        pp = QPainterPath(); pp.addRoundedRect(pill, 15, 15)
        if self.owned:
            p.fillPath(pp, QColor(120, 110, 92, 170))
            p.setPen(QColor(245, 240, 230)); p.setFont(QFont("Georgia", 10, QFont.Bold))
            p.drawText(pill, Qt.AlignCenter, "Owned")
        else:
            p.fillPath(pp, QColor(60, 38, 18, 150) if self.affordable else QColor(120, 50, 40, 150))
            p.setPen(QPen(QColor(255, 226, 150, 150), 1.2)); p.drawPath(pp)
            cd = 16; coin = QRectF(pill.left() + 12, pill.center().y() - cd / 2, cd, cd)
            cg = QRadialGradient(coin.center(), cd / 2)
            cg.setColorAt(0.0, QColor(255, 226, 140)); cg.setColorAt(1.0, QColor(214, 158, 48))
            p.setBrush(QBrush(cg)); p.setPen(QPen(QColor(150, 100, 24), 1.2)); p.drawEllipse(coin)
            p.setFont(QFont("Georgia", 12, QFont.Bold)); p.setPen(QColor(255, 246, 224))
            p.drawText(QRectF(coin.right(), pill.top(), pill.right() - coin.right() - 8, pill.height()),
                       Qt.AlignCenter, str(self.item["price"]))
        p.end()


# ─────────────────────────────────────────────────────────────────────────
#  Welcome panel — frosted overlay shown on entry, then fades away
# ─────────────────────────────────────────────────────────────────────────
class WelcomePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(40)

    def _tick(self):
        self._t += 0.05
        self.update()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(14, 8, 3, 150))   # dim behind the panel

        cw, ch = 460, 200
        r = QRectF((w - cw) / 2, (h - ch) / 2, cw, ch)
        path = QPainterPath(); path.addRoundedRect(r, 22, 22)
        glass = QLinearGradient(r.topLeft(), r.bottomLeft())
        glass.setColorAt(0.0, QColor(45, 35, 30, 200))   # Dark warm charcoal, slightly less transparent
        glass.setColorAt(1.0, QColor(25, 20, 15, 170))   # Very deep, dark chocolate brown
        p.fillPath(path, QBrush(glass))
        p.setPen(QPen(QColor(255, 246, 230, 180), 2)); p.drawPath(path)

        glow_a = int(40 + 30 * (0.5 + 0.5 * math.sin(self._t)))
        glow = QRadialGradient(r.center(), cw * 0.45)
        glow.setColorAt(0.0, QColor(255, 198, 110, glow_a))
        glow.setColorAt(1.0, QColor(255, 198, 110, 0))
        p.fillRect(r, QBrush(glow))

        p.setPen(QColor(70, 44, 20)); p.setFont(QFont("Georgia", 14))
        p.drawText(QRectF(r.left(), r.top() + 34, r.width(), 30), Qt.AlignCenter, "✦  ✦  ✦")
        p.setFont(QFont("Georgia", 26, QFont.Bold)); p.setPen(QColor(255, 253, 245))
        p.drawText(QRectF(r.left(), r.center().y() - 28, r.width(), 44), Qt.AlignCenter, "Welcome to the Shop")
        p.setFont(QFont("Georgia", 12, -1, True)); p.setPen(QColor(255, 253, 245))
        p.drawText(QRectF(r.left(), r.center().y() + 18, r.width(), 30), Qt.AlignCenter, "Eve's Curated Essentials")
        p.end()


# ─────────────────────────────────────────────────────────────────────────
#  Shop screen
# ─────────────────────────────────────────────────────────────────────────
class ShopScreen(QMainWindow):
    closed = Signal()

    def __init__(self, game=None):
        super().__init__()
        self.game = game
        self.setWindowTitle("Eve's Curated Essentials")
        self.setFixedSize(W, H)
        self.cards = []
        self._build()
        self._refresh_states()
        QTimer.singleShot(60, self._play_intro)

    def _coins(self):
        eve = getattr(self.game, "eve", None) if self.game else None
        return int(getattr(eve, "coins", 0) or 0) if eve else 0

    def _owned_keys(self):
        eve = getattr(self.game, "eve", None) if self.game else None
        items = getattr(eve, "room_items", None) if eve else None
        return set(items) if items else set()

    def _build(self):
        root = QWidget(); self.setCentralWidget(root)
        root.setStyleSheet("background: #2A1D10;")

        self.bg = QLabel(root)
        if os.path.exists(BG_PATH):
            pix = QPixmap(BG_PATH).scaled(W, H, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x = max(0, (pix.width() - W) // 2); y = max(0, (pix.height() - H) // 2)
            self.bg.setPixmap(pix.copy(x, y, W, H))
        else:
            print(f"[!] shop_bg.png not found at {BG_PATH}")
            self.bg.setStyleSheet("background: #2A1D10;")
        self.bg.setGeometry(0, 0, W, H)

        # light scrim only along the bottom, so the room stays visible
        scrim = QLabel(root)
        scrim.setGeometry(0, 0, W, H)
        scrim.setAttribute(Qt.WA_TransparentForMouseEvents)
        scrim.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
            " stop:0 rgba(20,12,4,0), stop:0.55 rgba(20,12,4,0),"
            " stop:1 rgba(16,9,3,110));")

        self.coin_badge = CoinBadge(root)
        self.coin_badge.move(W - self.coin_badge.width() - 22, 20)
        self.coin_badge.set_coins(self._coins())
        self.coin_badge.raise_()

        title = QLabel("The Little Shop", root)
        title.setFont(QFont("Georgia", 20, QFont.Bold))
        title.setStyleSheet("color: #FFE9B0; background: transparent;")
        title.setGeometry(28, 22, 400, 36)
        self.title = title

        self.scroll = QScrollArea(root)
        self.scroll.setGeometry(24, int(H * 0.42), W - 48, int(H * 0.52))
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { background: transparent; width: 8px; margin: 2px; }
            QScrollBar::handle:vertical { background: rgba(255,236,200,140);
                border-radius: 4px; min-height: 24px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        holder = QWidget(); holder.setStyleSheet("background: transparent;")
        grid = QGridLayout(holder)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(18); grid.setVerticalSpacing(18)

        cols = 4
        for i, item in enumerate(SHOP_ITEMS):
            card = ItemCard(item)
            card.buy_requested.connect(self._try_buy)
            grid.addWidget(card, i // cols, i % cols, Qt.AlignCenter)
            self.cards.append(card)
        self.scroll.setWidget(holder)

        self.status = QLabel("", root)
        self.status.setFont(QFont("Georgia", 12))
        self.status.setStyleSheet("color: #FFE9C8; background: transparent;")
        self.status.setGeometry(28, int(H * 0.42) - 30, W - 56, 26)

        # welcome overlay on top of everything
        self.welcome = WelcomePanel(root)
        self.welcome.setGeometry(0, 0, W, H)
        self.welcome.raise_()

    def _play_intro(self):
        # Slide the grid down a touch and hide it behind the welcome panel.
        # NOTE: no QGraphicsOpacityEffect on the QScrollArea — animating that
        # is unreliable and can leave the content stuck invisible. We use a
        # pure position slide instead, which always works.
        self._scroll_home = self.scroll.geometry()           # resting spot
        self.scroll.move(self._scroll_home.x(), self._scroll_home.y() + 50)
        QTimer.singleShot(1300, self._dismiss_welcome)

    def _dismiss_welcome(self):
        # Fade out the welcome panel (opacity effect on a custom QWidget is fine).
        self._wfx = QGraphicsOpacityEffect(self.welcome)
        self.welcome.setGraphicsEffect(self._wfx)
        self._fade_w = QPropertyAnimation(self._wfx, b"opacity")
        self._fade_w.setDuration(450)
        self._fade_w.setStartValue(1.0); self._fade_w.setEndValue(0.0)
        self._fade_w.setEasingCurve(QEasingCurve.InOutQuad)
        self._fade_w.finished.connect(self.welcome.hide)
        self._fade_w.start()

        # Slide the grid up into its resting position.
        self._rise = QPropertyAnimation(self.scroll, b"pos")
        self._rise.setDuration(520)
        self._rise.setStartValue(self.scroll.pos())
        self._rise.setEndValue(QPoint(self._scroll_home.x(), self._scroll_home.y()))
        self._rise.setEasingCurve(QEasingCurve.OutCubic)
        self._rise.start()

    def _try_buy(self, item):
        coins = self._coins()
        if item["effect"] in self._owned_keys():
            return
        if coins < item["price"]:
            self._flash(f"Not quite enough for {item['name']} — {item['price'] - coins} more to go.")
            return
        eve = getattr(self.game, "eve", None) if self.game else None
        if eve is not None:
            if hasattr(eve, "spend_coins"):
                eve.spend_coins(item["price"])
            elif hasattr(eve, "coins"):
                eve.coins -= item["price"]
            self._mark_owned(eve, item["effect"])
        self.coin_badge.set_coins(self._coins())
        self._flash(f"{item['name']} is yours. It'll look lovely in the room.")
        self._refresh_states()

    def _mark_owned(self, eve, effect_key):
        if hasattr(eve, "add_room_item"):
            try:
                eve.add_room_item(effect_key); return
            except TypeError:
                pass
        items = getattr(eve, "room_items", None)
        if isinstance(items, list):
            if effect_key not in items:
                items.append(effect_key)
        else:
            eve.room_items = [effect_key]

    def _refresh_states(self):
        owned = self._owned_keys(); coins = self._coins()
        for card in self.cards:
            card.owned = card.item["effect"] in owned
            card.affordable = coins >= card.item["price"]
            card.update()

    def _flash(self, msg):
        self.status.setText(msg)

    def closeEvent(self, e):
        self.closed.emit()
        super().closeEvent(e)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    class _FakeEve:
        def __init__(self):
            self.coins = 120
            self.room_items = []
        def spend_coins(self, n): self.coins -= n
        def add_room_item(self, key): self.room_items.append(key)

    class _FakeGame:
        def __init__(self): self.eve = _FakeEve()

    shop = ShopScreen(game=_FakeGame())
    shop.show()
    sys.exit(app.exec())