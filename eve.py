import numpy as np


class Eve:
        coin_history:np.array=[]
        room_items:list=[]
        choice_history:list=[]
        current_letter=""
        hints:list=[]
    
        def __init__(self,coins):
            self.coins=coins

        def earn_coins(self,amount):
            self.coins+=amount
        
        def spend_coins(self,amount):
            self.coins-=amount
        
        def add_room_item(key):
            pass
        
        def total_earned():
            pass
        
        def save():
            pass
        
        def avg_effort():
            pass