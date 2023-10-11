from machine import ADC, Pin, PWM
import time

class Servo(object):
    def __init__(self, _pwm_obj, _freq, _duty_rest = None):
        self.pwm_obj = _pwm_obj
        self.pwm_obj.freq(_freq)
        
        if(_duty_rest):
            self.duty_rest = _duty_rest
            #set initial rotation
            self.pwm_obj.duty_u16(self.duty_rest)
        
def move_servos(servos, voltages, threshold, move_amount_UD):
    #calulate up-down and left-right movements
    UD_voltage = ((voltages[2] + voltages[3]) / 2) - ((voltages[0] + voltages[1]) / 2)
    LR_voltage = ((voltages[0] + voltages[3]) / 2) - ((voltages[1] + voltages[2]) / 2)
#     move_amount_UD = 17476 + (UD_voltage*8738)
#     move_amount_LR = 17476 + (LR_voltage*8738)
    #move_amount_UD = 17476
    #move_amount_LR = 17476
    if (LR_voltage < -1*threshold):
        print("Move Right")
        servos[1].pwm_obj.duty_u16(int(4000)) #Move right from rest position [90 degrees] (if 45, then 8738)
    elif (LR_voltage > threshold):
        print("Move Left")
        servos[1].pwm_obj.duty_u16(int(5000)) #Move left from rest position [90 degrees] (if 135, then 26214)
    else:
        servos[1].pwm_obj.duty_u16(int(0))
            
        if (UD_voltage < -1*threshold):
            print("Move Down")
            move_amount_UD -= 300
            servos[0].pwm_obj.duty_u16(move_amount_UD)
            '''while move_amount_UD > 8738:
                move_amount_UD[0] = move_amount_UD[0] - 600
                servos[0].pwm_obj.duty_u16(move_amount_UD)
                time.sleep(0.1)#Move down from rest position [90 degrees] (if 45, then 8738)'''
            
            time.sleep(0.1)
        elif (UD_voltage) > threshold:
            print("Move Up")
            move_amount_UD += 300
            servos[0].pwm_obj.duty_u16(move_amount_UD)
            '''while move_amount_UD < 26214:
                move_amount_UD[0] = move_amount_UD[0] + 600
                servos[0].pwm_obj.duty_u16(move_amount_UD)
                time.sleep(0.1)#Move up from rest position [90 degrees] (if 135, then 26214)'''
    time.sleep(.1)
    return move_amount_UD
    
# Function to read data from a specific channel
def read_channel(channel, i2c):
    address = 0x6a
    # Set the channel in the configuration byte (bits 5 and 4)
    config = 0
    if channel == 1: #Top Right LDR
        config = 0xB8  
    elif channel == 0: #Bottom Right LDR
        config = 0x98
    elif channel == 3: #Top Right LDR
        config = 0xF8
    elif channel == 2: #Top Left LDR
        config = 0xD8
    
    i2c.writeto(address, bytes([config]))
    data = i2c.readfrom(address, 3)  # 4 bytes of data
    # Parse the data (assuming it's in 2's complement)
    raw_value = (data[0] << 16) | (data[1] << 8) | data[2]
    voltage = (raw_value / 2**16) / 62.5 # Convert raw value to voltage (3.3V reference, 18-bit resolution)
    return voltage