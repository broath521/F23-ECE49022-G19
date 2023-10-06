import machine
import time



def main():
    time.sleep(0.5)
    # I2C setup

    led = machine.Pin(25, machine.Pin.OUT)
    led.toggle()
    # MCP3424 configuration


    servo1 = machine.PWM(machine.Pin(22, mode=machine.Pin.OUT)) #Up Down Servo
    servo1.freq(400)
    move_UD = 17476
    servo1.duty_u16(move_UD) #Rest position at 90


    servo2 = machine.PWM(machine.Pin(13, mode=machine.Pin.OUT)) #Left Right Servo
    servo2.freq(50)


    thresh = 0.3




    # Read data from multiple channels
    while True:
        
        
        voltage_channel_0 = read_channel(0)
        
        time.sleep(0.2)
        
        voltage_channel_1 = read_channel(1)
        
        time.sleep(0.2)
        
        voltage_channel_2 = read_channel(2)
        
        time.sleep(0.2)
        
        voltage_channel_3 = read_channel(3)
        
        time.sleep(0.2)


        UD_voltage = ((voltage_channel_3 + voltage_channel_2) / 2) - ((voltage_channel_0 + voltage_channel_1) / 2)
        LR_voltage = ((voltage_channel_0 + voltage_channel_3) / 2) - ((voltage_channel_2 + voltage_channel_1) / 2)
        
                 
        if (LR_voltage) < -1*thresh:
    #         print("Move Right")
            servo2.duty_u16(int(4000)) #Move right from rest position [90 degrees] (if 45, then 8738)
        elif (LR_voltage) > thresh:
    #         print("Move Left")
            servo2.duty_u16(int(5000)) #Move left from rest position [90 degrees] (if 135, then 26214)
        else:
            servo2.duty_u16(int(0))
            
            if (UD_voltage) < -1*thresh:
        #         print("Move Down")
                
                while move_UD > 8738:
                    move_UD -= 600
                    servo1.duty_u16(move_UD)
                    time.sleep(0.1)
                    
                time.sleep(0.1)#Move down from rest position [90 degrees] (if 45, then 8738)
            elif (UD_voltage) > thresh:
        #         print("Move Up")
        
                while move_UD < 26214:
                    move_UD += 600
                    servo1.duty_u16(move_UD)
                    time.sleep(0.1)#Move up from rest position [90 degrees] (if 135, then 26214)
            
            
        led.toggle()
    #     print("BL: ", voltage_channel_0, "      BR: ", voltage_channel_1, "      TR: ", voltage_channel_2, "      TL: ", voltage_channel_3)
    # 
    #
    
    
# Function to read data from a specific channel
def read_channel(channel):
    # Channel configuration corresponds to bits 5 and 6
    i2c = machine.I2C(1, scl=machine.Pin(7), sda=machine.Pin(6), freq = 400000)  # Replace 5 and 4 with your actual SCL and SDA pins
    address = 0x68  # Default address, change if you've connected the address pins differently
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
#     config |= (channel << 5)
#     i2c.writeto(address, bytes([config]))
    data = i2c.readfrom(address, 3)  # 4 bytes of data
#     print("data 0", bin(data[0]))
#     print("data 1", data[1])
#     print("data 2:" ,data[2])
#     print(bytes(data))
    # Parse the data (assuming it's in 2's complement)
    raw_value = (data[0] << 16) | (data[1] << 8) | data[2]
    voltage = (raw_value / 2**16) / 62.5 # Convert raw value to voltage (3.3V reference, 18-bit resolution)
    return voltage


main()
