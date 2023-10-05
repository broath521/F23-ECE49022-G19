from machine import ADC, Pin, PWM
import time

class Servo(object):
    def __init__(self, _pwm_obj, _freq, _duty_rest):
        self.pwm_obj = _pwm_obj
        self.pwm_obj.freq(_freq)
        self.duty_rest = _duty_rest
        
        #set initial rotation
        self.pwm_obj.duty_u16(self.duty_rest)
        
def move_servo(servo, adc_reading_1, adc_reading_2, threshold):
    volt_diff = adc_reading_1 - adc_reading_2
    move_amount = servo.duty_rest + (volt_diff*8738)
    
    if (volt_diff) < -1*threshold:
        #print("Move Left")
        servo.pwm_obj.duty_u16(int(move_amount)) #Move right from rest position [90 degrees] (if 45, then 8738)
    elif (volt_diff) > threshold:
        #print("Move Right")
        servo.pwm_obj.duty_u16(int(move_amount)) #Move left from rest position [90 degrees] (if 135, then 26214)
    else:
        print("Don't Move")
    #print("Voltage Difference: ", volt_diff)

# Function to read data from a specific channel
def read_channel(channel, i2c):
    address = 0x6a
    # Set the channel in the configuration byte (bits 5 and 4)
    config = 0
    if channel == 1:
        config = 0x30  # Example: Single-ended, channel 0, 18-bit resolution
    elif channel == 0:
        config = 0x10
    elif channel == 3:
        config = 0x50
    elif channel == 2:
        config = 0x70
    i2c.writeto(address, bytes([config]))
    config |= (channel << 5)
    i2c.writeto(address, bytes([config]))

    data = i2c.readfrom(address, 4)  # 4 bytes of data
    # Parse the data (assuming it's in 2's complement)
    raw_value = (data[0] << 16) | (data[1] << 8) | data[2]
    if data[0] & 0x80:  # Check the sign bit
        raw_value -= 0x1000000  # Convert to negative value for 2's complement
    voltage = (raw_value * 3.3) / (2 ** 18) / 2.44 # Convert raw value to voltage (3.3V reference, 18-bit resolution)
    return voltage