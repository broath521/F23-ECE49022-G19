from machine import ADC, Pin, PWM
import time

delay_ms = 500 #delay output by X milliseconds
adc1 = ADC(28)
adc2 = ADC(27)
servo = PWM(Pin(22, mode=Pin.OUT))
servo.freq(400)
servo.duty_u16(17476) #Rest position at 90
 
while True:
    ldr1 = adc1.read_u16()
    ldr2 = adc2.read_u16()
    voltage1 = ldr1 * (3.3/65535)
    voltage2 = ldr2 * (3.3/65535)
    volt_diff = voltage1 - voltage2
    move_amount = 17476 + (volt_diff*8738)
    
    if (volt_diff) < -0.08:
        print("Move Left")
        servo.duty_u16(int(move_amount)) #Move right from rest position [90 degrees] (if 45, then 8738)
    elif (volt_diff) > 0.08:
        print("Move Right")
        servo.duty_u16(int(move_amount)) #Move left from rest position [90 degrees] (if 135, then 26214)
    else:
        print("Don't Move")
    print("Voltage Difference: ", volt_diff)
    time.sleep_ms(delay_ms)