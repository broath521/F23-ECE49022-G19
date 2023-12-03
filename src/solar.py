from machine import ADC, Pin, PWM
from time import sleep

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
            
        elif (UD_voltage) > threshold:
            print("Move Up")
            move_amount_UD += 300
            servos[0].pwm_obj.duty_u16(move_amount_UD)

    sleep(.01)
    return move_amount_UD

# Function to read data from either channel 1 or all 4 channels
def read_channels(i2c, address, ldrs=1):
    voltages = [0]*4
    configs = 0x98, 0xB8, 0xD8, 0xF8
    if(ldrs):
        for i in range(4):
            i2c.writeto(address, bytes([configs[i]]))
            data = i2c.readfrom(address, 3)  # 3 bytes of data
            # Parse the data (assuming it's in 2's complement)
            raw_value = (data[0] << 16) | (data[1] << 8) | data[2]
            voltages[i] = (raw_value / 2**16) / 62.5 # Convert raw value to voltage (3.3V reference, 18-bit resolution)
            if(i<3):
                sleep(.08)
                
        return voltages
    else:
        i2c.writeto(address, bytes([configs[0]]))
        data = i2c.readfrom(address, 3)  # 3 bytes of data
        # Parse the data (assuming it's in 2's complement)
        raw_value = (data[0] << 16) | (data[1] << 8) | data[2]
        voltages[0] = (raw_value / 2**16) / 62.5 # Convert raw value to voltage (3.3V reference, 18-bit resolution) 
        return voltages
    
    