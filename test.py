from machine import ADC, Pin, PWM
import time

delay_ms = 100
servo = PWM(Pin(8, mode=Pin.OUT))
servo.freq(50)

freq = 50
period = 1/freq

PW = 1500
loc = PW/1000000
DS = loc/period

upper_bound = 65535
neutral = 32767
lower_bound = 0

pos = int(DS*65535)

while(True):
    '''pos += (direction*incr)
    if(pos >= upper_bound):
        print("upper reached: ", pos)
        direction = -1
    elif(pos <= lower_bound):
        print("lower reached: ", pos)
        direction = 1'''
    servo.duty_u16(pos)

    time.sleep_ms(delay_ms)
