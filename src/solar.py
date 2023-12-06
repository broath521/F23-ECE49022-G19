from machine import ADC, Pin, PWM
from time import sleep

class Servo(object):
    def __init__(self, _pwm_obj, _freq):
        self.pwm_obj = _pwm_obj
        self.pwm_obj.freq(_freq)

    def convert_pulse(self, PW):
        period = self.pwm_obj.freq
        DS = (PW / 1000000) / period
        return int(DS*65535)
    

def move_servos(servos, voltages, threshold, PW_UD):
    #calulate up-down and left-right movements
    UD_voltage = ((voltages[3] + voltages[0]) / 2) - ((voltages[2] + voltages[1]) / 2)
    LR_voltage = ((voltages[2] + voltages[0]) / 2) - ((voltages[1] + voltages[3]) / 2)
    
    #print("Voltages: ", voltages)

    if (LR_voltage < -1*threshold):
        print("Move Right")
        servos[1].pwm_obj.duty_u16(int(8.0*65535/100)) #Move right with 8% duty cycle
    elif (LR_voltage > threshold):
        print("Move Left")
        servos[1].pwm_obj.duty_u16(int(7.0*65535/100)) #Move left with 7% duty cycle
    else:
        servos[1].pwm_obj.duty_u16(int(7.5*65535/100)) #stationary with 7.5% duty cycle
        print(PW_UD)
        if (UD_voltage < -1*threshold and PW_UD > 1167):
            print("Move Down")
            PW_UD -= 20
            DS = servo[0].convert_pulse(PW_UD)
            servos[0].pwm_obj.duty_u16(int(PW_UD))
            sleep(.1)
            
        elif (UD_voltage > threshold and PW_UD < 1833):
            print("Move Up")
            PW_UD += 20
            DS = servo[0].convert_pulse(PW_UD)
            servos[0].pwm_obj.duty_u16(int(PW_UD))
            sleep(.1)

    sleep(.05)
    return PW_UD

# Function to read data from either channel 1 or all 4 channels
def read_channels(i2c, address, ldrs=1):
    voltages = [0]*4
    configs = [0x98, 0xB8, 0xD8, 0xF8]
    if(ldrs):
        for i in range(4):
            i2c.writeto(address, bytes([configs[i]]))
            data = i2c.readfrom(address, 3)  # 3 bytes of data
            # Parse the data (assuming it's in 2's complement)
            raw_value = (data[0] << 16) | (data[1] << 8) | data[2]
            voltages[i] = (raw_value / 2**16) / 62.5 # Convert raw value to voltage (3.3V reference, 18-bit resolution)
            sleep(.08)
                
        return voltages
    else:
        i2c.writeto(address, bytes([configs[0]]))
        data = i2c.readfrom(address, 3)  # 3 bytes of data
        # Parse the data (assuming it's in 2's complement)
        raw_value = (data[0] << 16) | (data[1] << 8) | data[2]
        voltages[0] = (raw_value / 2**16) / 62.5 # Convert raw value to voltage (3.3V reference, 18-bit resolution) 
        return voltages
    
    