import _thread
from time import sleep
from ssd1306 import SSD1306_I2C
from machine import Pin, PWM, I2C
from rotary_irq_rp2 import RotaryIRQ


### LEFT SIDE GPIO ###
buttonSolenoid = Pin(0, Pin.IN, Pin.PULL_DOWN)
solenoid = Pin(1,Pin.OUT)
solenoid.off()

buttonESC = Pin(2, Pin.IN, Pin.PULL_DOWN)
pwm = PWM(Pin(3))
pwm.freq(50)


### RIGHT SIDE GPIO ###
selectB  = Pin(26, Pin.IN, Pin.PULL_DOWN)
selectG  = Pin(22, Pin.IN, Pin.PULL_DOWN)
selectR  = Pin(21, Pin.IN, Pin.PULL_DOWN)
fireMode = "Safe"

knob_button = Pin(20, Pin.IN, Pin.PULL_UP)
rotary = RotaryIRQ(
    pin_num_clk = 18,                  # GPIO pin connected to encoder CLK pin
    pin_num_dt = 19,                   # GPIO pin connected to encoder DT pin
    min_val = 0,                       # minimum value in the encoder range. Also the starting value
    max_val = 100,                     # maximum value in the encoder range
    reverse = False,                   # reverse count direction
    range_mode = RotaryIRQ.RANGE_WRAP, # count behavior at min_val and max_val
    pull_up = False,                   # enable internal pull up resistors
    half_step = True,                  # half-step mode
    invert = False                     # invert the CLK and DT signals
    )

i2c = I2C(0,sda=Pin(16), scl=Pin(17), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)


### GLOBAL VARIABLES ###
REFRESH_RATE = 100
masterClock  = 0

MIN_Speed    = 1000000
MAX_Speed    = 2000000
MOTOR_OFFSET = 14
MOTOR_SPEED  = 0

knob_old = rotary.value()

ON_TIME = 5 # Time Solenoid spent "ON" (Default = 5)
reset   = 10 # Time Solenoid spent "OFF" to reset the solenoid (Default = 10)
buffer  = 10 # Additional time to get the desired Darts per Second
cycle   = ON_TIME + reset + buffer  # Total time of a "Shot" cycle
DPS     = 7
'''
Formula:
Darts per Second = 100/(ON_TIME + reset + buffer)

Buffer =  DPS
    0     =  Max, ~6.6 Darts per second
    1.66  =  6 Darts per second
    5     =  5 Darts per second
    10    =  4 Darts per second
    18    = ~3 Darts per second
    35    =  2 Darts per second
    85    =  1 Darts per second
'''

fireVal     = 0
prevFireVal = 0

shots_fired = 0
shot_limit  = 3
firing      = 0

locker      = _thread.allocate_lock()


def fire():
    global shots_fired
    global firing
    
    locker.acquire()
    firing = 1
    if fireMode is "Burst":
        for x in range(shot_limit):
            solenoid.on()
            sleep(ON_TIME/100)
            solenoid.off()
            sleep((reset + buffer)/100)
            shots_fired += 1
    else:
        solenoid.on()
        sleep(ON_TIME/100)
        solenoid.off()
        sleep((reset + buffer)/100)
        shots_fired += 1
    locker.release()
    firing = 0
    _thread.exit()


def motor(speed):
    motor_output = MIN_Speed
    if speed is not 0:
        motor_output += int((speed/100) * (MAX_Speed-MIN_Speed))
    pwm.duty_ns(motor_output)


def CalcDPS():
    global buffer
    global cycle
    global DPS
    
    buffer = (100/DPS) - (ON_TIME + reset) #  buffer = 100/DPS - (ON_TIME + reset)
    cycle = ON_TIME + reset + buffer  # Total time of a "Shot" cycle
    
    print("DPS: " + str(DPS) + ", Buffer: " + str(buffer))


CalcDPS()
while 1:
    sleep(1 / REFRESH_RATE)
    
    
    #Select Fire
    if selectB.value():
        fireMode = "Safe"
    elif selectG.value():
        fireMode = "Single"
    elif selectR.value():
        fireMode = "Burst"
    else:
        fireMode = "Auto"
    
    
    
    #Solenoid Control
    #fireVal = not knob_button.value()
    fireVal = buttonSolenoid.value()
    
    if (not firing) and (fireMode is not "Safe"):
        if fireVal != (prevFireVal * fireVal):
            _thread.start_new_thread(fire,())
        elif (fireMode is "Auto") * fireVal:
            _thread.start_new_thread(fire,())
    prevFireVal = fireVal
    
    
    # Motor/ESC Control
    if buttonESC.value():
        if fireMode is "Single":
            MOTOR_SPEED = 14 # Lowest speed
        elif fireMode is "Burst":
            MOTOR_SPEED = 57
        elif fireMode is "Auto":
            MOTOR_SPEED = 100
        else:
            MOTOR_SPEED = 0       
    else:
        MOTOR_SPEED = 0
    motor(MOTOR_SPEED)
    
    
    # Knob Control
    if not knob_button.value():
        rotary.set(value = 0) # Resets the Knob Counter
    
    knob_new = rotary.value()

    if knob_old != knob_new:
        knob_old = knob_new
    
    # OLED Control    
    oled.fill(0) # fill entire screen with colour = 0
    oled.text("Mode: " + fireMode, 0, 0, 8) 
    oled.text("Solenoid: " + str(buttonSolenoid.value()), 0, 16, 8) 
    oled.text("Motors: " + str(buttonESC.value()), 0, 32, 8) 
    oled.text("Knob: " + str(knob_button.value()) + ", " + str(knob_new), 0, 46, 8) 
    oled.show()
    
    
    masterClock += 1
    if masterClock >= REFRESH_RATE:
        masterClock = 0
