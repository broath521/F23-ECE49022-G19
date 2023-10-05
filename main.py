from machine import ADC, Pin, SPI, I2C
from time import sleep
from random import random, seed
from lib.ili9341 import Display, color565
from utime import ticks_cpu, ticks_diff, ticks_ms, ticks_diff, sleep_ms
from lib.xglcd_font import XglcdFont
from src.screens import DataMessage, Screen
from src.data import calc_charge, average_volt, format_datetime
from src.solar import Servo, move_servo, read_channel
from lib.imu import MPU6050
from lib.bmp085 import BMP180
from lib.ds1307 import DS1307

def main():
    sleep(.5)
    print("start")
    """Test code."""
    try:
        #Setup SPI connections and display object
        spi = SPI(0, baudrate=10000000, polarity=1, phase=1, bits=8, firstbit=SPI.MSB,
                      sck=Pin(18), mosi=Pin(19), miso=Pin(16))
        display = Display(spi, dc=Pin(15), cs=Pin(17), rst=Pin(14))

        #setup ADCs
        charge_adc = ADC(28)

        #setup GPIO pins for push buttons
        reset = Pin(10, Pin.IN)
        forward = Pin(11, Pin.IN)
        backward = Pin(12, Pin.IN)
        
        #setup I2C devices
        i2c0 = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
        i2c1 = I2C(1, sda=Pin(6), scl=Pin(7), freq=400000)
        
        ### initialize screen messages and objects ###
        default_val = "-1"
        fontType = XglcdFont('fonts/Unispace12x24.c', 12, 24)
        
        #product logo loading
        suns_message = DataMessage("Sun Seeker", int(120 - 5*fontType.width), int(300 - (fontType.height/2)),
                               fontType, color565(255,255,255))
        
        #start screen
        start_message_1 = DataMessage("Loading System...", 0, 60, fontType, color565(255,255,255), value = "", unit = "")
        start_message_2 = DataMessage("Taking Data...", 0, start_message_1.y + int(2*fontType.height),
                                      fontType, color565(255,255,255), value = "", unit = "")
        start_screen = Screen(display, [start_message_1, start_message_2, suns_message])
        
        #reset screen
        reset_message_1 = DataMessage("Resetting System...", 0, 60, fontType, color565(255,255,255), value = "", unit = "")
        reset_screen = Screen(display, [reset_message_1, suns_message])
        
        #first screen messages
        charge_msg = DataMessage("Charge: ", 0, 60, fontType, color565(255,255,255), value = default_val, unit = "%")
        date_msg = DataMessage("Date: ", 0, charge_msg.y + int(2*fontType.height),
                               fontType, color565(255,255,255), value = default_val)
        time_msg = DataMessage("Time: ", 0, date_msg.y + int(2*fontType.height),
                               fontType, color565(255,255,255), value = default_val)
        
        screen1 = Screen(display, [charge_msg, date_msg, time_msg, suns_message])
        
        #second screen messages
        temp_msg = DataMessage("Temperature: ", 0, 60, fontType, color565(255,255,255), value = default_val, unit = "F")
        alt_msg = DataMessage("Altitude: ", 0, temp_msg.y + int(2*fontType.height),
                               fontType, color565(255,255,255), value = default_val, unit = "m")
        
        #hum_msg = DataMessage("Humidity: ", 0, temp_msg.y + int(2*fontType.height),
        #                       fontType, color565(255,255,255), value = default_val, unit = "g/m^3")
        
        screen2 = Screen(display, [temp_msg, alt_msg, suns_message])
        
        #third screen messages
        dist_msg = DataMessage("Distance: ", 0, 60, fontType, color565(255,255,255), value = default_val, unit = "m")
        steps_msg = DataMessage("Steps: ", 0, dist_msg.y + int(2*fontType.height),
                               fontType, color565(255,255,255), value = default_val, unit = "steps")
        
        screen3 = Screen(display, [dist_msg, steps_msg, suns_message])
        
        screenArr = [start_screen, reset_screen, screen1, screen2, screen3]
        
        #time in between data updates (in ms)
        #charge, time, temp, altitude, distance, steps, LDRs
        timing_arr = [250, 1000, 5000, 1000, 100, 100, 1000]
        last_updates = [ticks_ms()]*7
        seed(ticks_cpu())
        
        #used for averaging voltage readings, as ADC readings
        #are unstable due to fluctuating buck converter supply
        voltage_arr = [0]*40
        volt_count = 0
        
        #setup sensors and servo
        servo1 = Servo(machine.PWM(machine.Pin(22, mode=machine.Pin.OUT)), 400, 17476)
        
        imu = MPU6050(i2c1)
        
        bmp = BMP180(i2c0)
        bmp.oversample = 2
        bmp.sealevel = 101325
        
        rtc = DS1307(i2c0)
        #uncomment to set time (EST)
        #rtc.datetime((2023,10,5,4,11,55,0,0))
        
        #test code to confirm I2C device connections
        print('Scanning I2C0 bus.')
        devices = i2c0.scan() # this returns a list of devices
        device_count = len(devices)

        if device_count == 0:
            print('No i2c device found on I2C0.')
        else:
            print(device_count, 'devices found on I2C0.')

        for device in devices:
            print('Decimal address:', device, ", Hex address: ", hex(device))
        print("")
        
        sleep(.1)
        print('Scanning I2C1 bus.')
        devices = i2c1.scan() # this returns a list of devices
        device_count = len(devices)

        if device_count == 0:
            print('No i2c device found on I2C1.')
        else:
            print(device_count, 'devices found on I2C1.')

        for device in devices:
            print('Decimal address:', device, ", Hex address: ", hex(device))
        print("")

        #start system
        #################################################
        current_screen = 0
        screenArr[current_screen].draw_screen()
        
        bat_v = charge_adc.read_u16() * (3.3 / 65535) * 6
        charge = round(calc_charge(bat_v), 2)
        charge_msg.value = str(charge)
        
        threshold = .75 # Adjust this value to suit your walking pattern
        firstStep = True
        steps = 0
        prev_steps = steps
        last_accel = [0, 0, 0]
        
        #calculate idle accel values to reduce error
        idle_ax_sum = 0
        idle_ay_sum = 0
        idle_az_sum = 0
        
        for i in range(50):
            idle_ax_sum += round(imu.accel.x, 2)
            idle_ay_sum += round(imu.accel.y, 2)
            idle_az_sum += round(imu.accel.z, 2)
            sleep(.05)
        
        idle_ax= round(idle_ax_sum / 50, 2)
        idle_ay= round(idle_ay_sum / 50, 2)
        idle_az= round(idle_az_sum / 50, 2)
        
        ACCELEROMETER_SENSITIVITY = 16384.0  # Sensitivity for MPU6050
        TIME_INTERVAL = 0.1  # Time interval between measurements
        grav_convert = 9.81
        distance = 0
        accel_arr = [0, 0]
        vel_arr = [0, 0]
        pos_arr = [0, 0]
        
        altitude = round(bmp.altitude, 1)
        alt_msg.value = str(altitude)
        
        temp_c = bmp.temperature
        temp_f= round((temp_c * (9/5) + 32), 1)
        temp_msg.value = str(temp_f)
        
        sleep(1)
        current_screen = 2
        screenArr[current_screen].draw_screen()
        #################################################
        
        #main loop
        while True:
            # Get the current time
            current_time = ticks_ms()
            
            #check state of GPIO pins. Push buttons output reversed values.
            state_reset = not reset.value()
            state_forward = not forward.value()
            state_backward = not backward.value()
            button_array = [state_reset, state_forward, state_backward]
            
            #button check logic
            if(state_reset):
                print("reset")
                current_screen = 1
                screenArr[current_screen].draw_screen()
                  
                bat_v = charge_adc.read_u16() * (3.3 / 65535) * 6
                charge = round(calc_charge(bat_v), 2)
                charge_msg.value = str(charge)

                firstStep = True
                steps = 0
                prev_steps = steps
                last_accel = [0, 0, 0]
                
                distance = 0
                accel_arr = [0, 0]
                vel_arr = [0, 0]
                pos_arr = [0, 0]
                
                altitude = round(bmp.altitude, 1)
                alt_msg.value = str(altitude)
                
                temp = bmp.temperature
                temp_msg.value = str(temp)
              
                sleep(1)
                current_screen = 2
                screenArr[current_screen].draw_screen()
                sleep_ms(100)
              
            if(state_forward):
              
                current_screen+=1
                if(current_screen>4):
                    current_screen = 2
                      
                sleep_ms(50)
                screenArr[current_screen].draw_screen()
                sleep_ms(100)
              
            if(state_backward):
              
                current_screen-=1
                if(current_screen<2):
                    current_screen = 4
                      
                sleep_ms(50)
                screenArr[current_screen].draw_screen()
                sleep_ms(100)
            
            ###timing loops###
            current_time = ticks_ms()

            #charge check
            if ticks_diff(current_time, last_updates[0]) >= timing_arr[0]:
                
                bat_v = charge_adc.read_u16() * (3.3 / 65535) * 6
                
                voltage_arr[volt_count] = bat_v
                volt_count+=1
                
                if(volt_count == 40):
                    #sum the last 10 voltages and average them, then find charge %
                    bat_v_avg = average_volt(voltage_arr)
                    volt_count = 0
                    
                    #find charge percentage based on the average
                    charge = round(calc_charge(bat_v_avg), 2)
                    
                    print(charge, charge_msg.value)
                    if(current_screen == 2):
                        charge_msg.draw_data(display, str(charge))
                        #time_msg.draw_data(display, str(bat_v_avg))
                    else:
                        charge_msg.value = str(charge)
                    
                last_updates[0] = current_time
                
            #datetime check
            if ticks_diff(current_time, last_updates[1]) >= timing_arr[1]:
                datetime = rtc.datetime()
                
                format_date, format_time = format_datetime(datetime)
                
                if(current_screen == 2):
                    date_msg.draw_data(display, format_date)
                    time_msg.draw_data(display, format_time)
                else:
                    date_msg.value = format_date
                    time_msg.value = format_time
                    
                last_updates[1] = current_time
                
            #temp check
            if ticks_diff(current_time, last_updates[2]) >= timing_arr[2]:
                
                temp_c = round(bmp.temperature, 1)        #get the temperature in degree celsius
                #pres_hPa = bmp.pressure        #get the pressure in hpa
                #altitude = bmp.altitude        #get the altitude
                temp_f= round((temp_c * (9/5) + 32), 1)   #convert the temperature value in fahrenheit
                
                if(current_screen == 3):
                    temp_msg.draw_data(display, str(temp_f))
                else:
                    temp_msg.value = str(temp_f)
                    
                last_updates[2] = current_time
            
            #altitude check
            if ticks_diff(current_time, last_updates[3]) >= timing_arr[3]:
                altitude = round(bmp.altitude, 1)
                
                if(current_screen == 3):
                    alt_msg.draw_data(display, str(altitude))
                else:
                    alt_msg.value = str(altitude)
                    
                last_updates[3] = current_time
            
            #distance check
            if ticks_diff(current_time, last_updates[4]) >= timing_arr[4]:
                #read accelerometer values for distance
                d_ax=round((imu.accel.x - idle_ax), 4)
                d_ay=round((imu.accel.y - idle_ay), 4)
                if(abs(d_ax) > .1 or abs(d_ay) > .1):
                    print("d_ax: " + str(d_ax) + " d_ay: " + str(d_ay))
                    accel_arr = [d_ax * grav_convert, d_ay * grav_convert]
                    vel_arr = [vel_arr[0] + accel_arr[0]*TIME_INTERVAL, vel_arr[1] + accel_arr[1]*TIME_INTERVAL]
                    pos_arr = [round(pos_arr[0] + vel_arr[0]*TIME_INTERVAL, 3), round(pos_arr[1] + vel_arr[1]*TIME_INTERVAL, 3)]
                #print("Position (x, y): " + str(pos_arr[0]) + " " + str(pos_arr[1]))
                
                if(current_screen == 4):
                    dist_msg.draw_data(display, str(0))
                else:
                    dist_msg.value = str(0)
                    
                last_updates[4] = current_time
                
            #steps check
            if ticks_diff(current_time, last_updates[5]) >= timing_arr[5]:
                prev_steps = steps
                #read accelerometer values for steps
                s_ax=round(imu.accel.x - idle_ax, 2)
                s_ay=round(imu.accel.y - idle_ay, 2)
                s_az=round(imu.accel.z - idle_az, 2)
                #print(s_ax, s_ay, s_az)
                accel_magnitude = (s_ax ** 2 + s_ay ** 2 + s_az ** 2) ** 0.5

                # Detect a step based on the change in acceleration
                if ((accel_magnitude - last_accel[2] > threshold) and (not firstStep)):
                    steps += 1
                
                firstStep = False
                last_accel = [s_ax, s_ay, s_az]
                
                
                if(current_screen == 4 and steps > prev_steps):
                    steps_msg.draw_data(display, str(steps))
                else:
                    steps_msg.value = str(steps)
                    
                last_updates[5] = current_time

            #LDR check
            if ticks_diff(current_time, last_updates[6]) >= timing_arr[6]:
                #read voltages from channel 1 and channel 2 on MCP3234
                voltage_channel_0 = read_channel(0, i2c0)
                sleep(.1)
                voltage_channel_1 = read_channel(1, i2c0)
                    
                move_servo(servo1, voltage_channel_0, voltage_channel_1, .1)
                
                last_updates[6] = current_time

            
            sleep_ms(10)
            
    except KeyboardInterrupt:
        display.cleanup()
        
main()
