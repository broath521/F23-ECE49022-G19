import machine
import time

# I2C setup
i2c = machine.I2C(1, scl=machine.Pin(7), sda=machine.Pin(6), freq = 400000)  # Replace 5 and 4 with your actual SCL and SDA pins

# MCP3424 configuration
address = 0x68  # Default address, change if you've connected the address pins differently

servo = machine.PWM(machine.Pin(22, mode=machine.Pin.OUT))
servo.freq(400)
servo.duty_u16(17476) #Rest position at 90

# Function to read data from a specific channel
def read_channel(channel):
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

# Read data from multiple channels
while True:
    voltage_channel_0 = read_channel(0)
    
    time.sleep(0.1)
    
    voltage_channel_1 = read_channel(1)
    
    

    UD_voltage = voltage_channel_0 - voltage_channel_1
    move_amount_UD = 17476 + (UD_voltage*8738)
    #move_amount_LR = 17476 + (LR_voltage*8738)
    
    if (UD_voltage) < -0.1:
        print("Move Down")
        servo.duty_u16(int(move_amount_UD)) #Move right from rest position [90 degrees] (if 45, then 8738)
    elif (UD_voltage) > 0.1:
        print("Move Up")
        servo.duty_u16(int(move_amount_UD)) #Move left from rest position [90 degrees] (if 135, then 26214)
    else:
        print("Don't Move")
    print("Up/Down Voltage Difference: ", UD_voltage)
    time.sleep(.1)  # Adjust the interval as needed
