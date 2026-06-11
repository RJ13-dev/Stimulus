class Card:
    
    def __init__(self, label, task_text, coins, reward_type, room_effect):
        self.label = label            # "Big", "Medium", or "Tiny"
        self.task_text = task_text    # What the task says
        self.coins = coins            # 5, 3, or 1
        self.reward_type = reward_type  # "coins" or "gift"
        self.room_effect = room_effect  # e.g. "sketchbook_on_desk"