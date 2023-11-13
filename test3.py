import uasyncio as asyncio 
from machine import Pin 
import time 

class Button: 
    def __init__ (self, pin, action): 
        self.pin = pin 
        self.action = action 
        self.previous_state = False 
    
    def toggle_bounce(self): 
        button_state = self.pin.value() 
        if button_state and not self.previous_state: 
            asyncio.create_task(self.action()) 
        self. previous_state = button_state 

class Counter: 
    def __init__ (self, cooldown_ms=1000): 
        self.value = 0 
        self.cooldown_ms = cooldown_ms 
        self.last_increment_time = 0 

    def can_increment(self): 
        current_time = time.ticks_ms() 
        return (current_time - self.last_increment_time) >= self.cooldown_ms 

    async def increment(self): 
        if self.can_increment(): 
            self.value += 1 
            print("Button pressed! Counter:", self.value) 
            self.last_increment_time = time.ticks_ms() 
            await asyncio.sleep_ms(0) 

async def main(): 
    counter0 = Counter() 
    counterl = Counter() 

    button0 = Button(Pin(0, Pin.IN, Pin.PULL_DOWN), counter0.increment)
    buttonl = Button(Pin(2, Pin.IN, Pin.PULL_DOWN), counterl.increment) 

    while True: 
        button0.toggle_bounce() 
        buttonl.toggle_bounce() 
        await asyncio. sleep_ms(0) 

asyncio.run(main()) 

