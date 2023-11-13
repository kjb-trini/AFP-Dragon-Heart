# roundrobin.py Test/demo of round-robin scheduling
# Author: Peter Hinch
# Copyright Peter Hinch 2017-2020 Released under the MIT license

# Result on Pyboard 1.1 with print('Foo', n) commented out
# executions/second 5575.6 on uasyncio V3

# uasyncio V2 produced the following results
# 4249 - with a hack where sleep_ms(0) was replaced with yield
# Using sleep_ms(0) 2750

import uasyncio as asyncio

from ssd1306 import SSD1306_I2C
from machine import Pin, PWM, I2C

count = 0
period = 5

i2c = I2C(0,sda=Pin(16), scl=Pin(17), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

async def foo():
    global count
    while True:
        await asyncio.sleep_ms(0)
        count += 1

async def main(delay):
    asyncio.create_task(foo())
    print('Testing for {:d} seconds'.format(delay))
    await asyncio.sleep(delay)
    oled.rect(0, 0, 64, 8, 8, True)
    oled.text(str(count), 0, 0, 0)
    oled.show()


asyncio.run(main(period))
print('Coro executions per sec =', count/period)