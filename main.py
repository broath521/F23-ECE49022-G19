#list of module imports
from machine import ADC, Pin, SPI, I2C
from time import sleep
from random import random, seed
from lib.ili9341 import Display, color565
from utime import ticks_cpu, ticks_diff, ticks_ms, ticks_diff, sleep_ms
from lib.xglcd_font import XglcdFont
from src.screens import DataMessage, Screen
from src.data import calc_charge, average_volt, format_datetime
from src.solar import Servo, move_servos, read_channel
from lib.imu import MPU6050
from lib.bmp085 import BMP180
from lib.ds1307 import DS1307

def main():
    sleep(.5)
    print("start")
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
        toggle_solar = Pin(27, Pin.IN)
        
        solar_flag = False #flag to disable/enable solar tracking
        
        #setup I2C devices
        i2c0 = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)
        i2c1 = I2C(1, sda=Pin(6), scl=Pin(7), freq=100000)
        
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
        
        ### initialize screen messages and objects ###
        default_val = "-1"
        fontType = XglcdFont('fonts/Unispace12x24.c', 12, 24) #loads the chosen font into a glcd object
        
        #product logo loading
        suns_message = DataMessage("Sun Seeker", int(120 - 5*fontType.width), int(300 - (fontType.height/2)),
                               fontType, color565(255,255,255))
        
        #start screen
        start_message_1 = DataMessage("Loading System...", 0, 60, fontType, color565(255,255,255), value = "", unit = "")
        start_message_2 = DataMessage("Taking Data...", 0, start_message_1.y + int(2*fontType.height),
                                      fontType, color565(255,255,255), value = "", unit = "")
        solar_toggle_msg = DataMessage("Tracking: ", 0, start_message_2.y + int(2*fontType.height),
                                      fontType, color565(255,255,255), value = "Disabled", unit = "")
        
        solar_screen = Screen(display, [solar_toggle_msg, suns_message])
        start_screen = Screen(display, [start_message_1, start_message_2, solar_toggle_msg, suns_message])
        
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
        
        #exit screen message - runs on any error encountered
        exit_msg = DataMessage("Exit Program", 0, 60, fontType, color565(255,255,255), value = "", unit = "")
        
        exit_screen = Screen(display, [exit_msg, suns_message])
        
        screenArr = [start_screen, reset_screen, screen1, screen2, screen3, exit_screen, solar_screen]
        
        #time in between data updates (in ms)
        #charge, time, temp, altitude, distance, steps, LDRs
        timing_arr = [250, 1000, 1500, 1000, 100, 250, 100]
        last_updates = [ticks_ms()]*7
        seed(ticks_cpu())
        
        #used for averaging voltage readings, as ADC readings
        #are unstable due to fluctuating buck converter supply
        voltage_arr = [0]*10
        volt_count = 0
        
        #setup servos
        servo1 = Servo(machine.PWM(machine.Pin(22, mode=machine.Pin.OUT)), 400, 17476)
        servo2 = Servo(machine.PWM(machine.Pin(26, mode=machine.Pin.OUT)), 50)
        servos = [servo1, servo2]
        servo_thresh = 0.3
        ldr_voltages = [0]*4
        move_amount_UD = 17476
        
        #create sensors objects
        imu = MPU6050(i2c1)
        sleep(.25)
        bmp = BMP180(i2c0)
        sleep(.25)
        rtc = DS1307(i2c0)
        #rtc.datetime((2023,10,6,5,12,05,0,0)) #uncomment to set time (EST)

        #start system
        #################################################
        current_screen = 0
        screenArr[current_screen].draw_screen()
        
        #take first charge reading
        supply_v = 3.361
        gain_factor = 6.02
        bat_v = charge_adc.read_u16() * (supply_v / 65535) * gain_factor
        charge = round(calc_charge(bat_v), 2)
        charge_msg.value = str(charge)
        
        #take first datetime reading
        datetime = rtc.datetime()
        print(datetime)
        format_date, format_time = format_datetime(datetime)
        date_msg.value = format_date
        time_msg.value = format_time
        
        #setup variables for step counting
        threshold = .3
        firstStep = True #flag to stop counter from starting as 1
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
        
        #setup variables for distance calculation
        ACCELEROMETER_SENSITIVITY = 16384.0  # Sensitivity for MPU6050
        TIME_INTERVAL = int(1000/timing_arr[4])  # Time interval between measurements
        grav_convert = 9.81
        distance = 0
        accel_arr = [0, 0]
        vel_arr = [0, 0]
        pos_arr = [0, 0]
        dist_msg.value = str(distance) #replace standard value with 0
        
        #setup altitude and take first reading
        bmp.oversample = 2
        bmp.sealevel = 101325
        altitude = round(bmp.altitude, 1)
        alt_msg.value = str(altitude)
        
        #take first temp reading
        temp_c = bmp.temperature
        temp_f= round((temp_c * (9/5) + 32), 1)
        temp_msg.value = str(temp_f)
        
        #set new screen to first data screen
        sleep(1)
        current_screen = 2
        screenArr[current_screen].draw_screen()
        #################################################
        
        #main loop
        while True:
            # Get the current time
            current_time = ticks_ms()
            
            #check state of GPIO pins. Push buttons output reversed values due to debouncing setup.
            state_reset = not reset.value()
            state_forward = not forward.value()
            state_backward = not backward.value()
            state_solar = not toggle_solar.value()
            
            #button check logic
            if(state_reset):
                #Show reset screen, then recall all setup functions and values
                current_screen = 1
                screenArr[current_screen].draw_screen()
                  
                bat_v = charge_adc.read_u16() * (3.3 / 65535) * 6
                charge = round(calc_charge(bat_v), 2)
                charge_msg.value = str(charge)

                datetime = rtc.datetime()
                format_date, format_time = format_datetime(datetime)
                date_msg.value = format_date
                time_msg.value = format_time

                firstStep = True
                steps = 0
                prev_steps = steps
                last_accel = [0, 0, 0]
                
                distance = 0
                accel_arr = [0, 0]
                vel_arr = [0, 0]
                pos_arr = [0, 0]
                dist_msg.value = str(distance)
                
                altitude = round(bmp.altitude, 1)
                alt_msg.value = str(altitude)
                
                temp = bmp.temperature
                temp_msg.value = str(temp)
              
                sleep(1)
                current_screen = 2
                screenArr[current_screen].draw_screen()
                sleep_ms(100)
              
            if(state_forward):
                #go to next screen and load, loop if past last data screen
                current_screen+=1
                if(current_screen>4):
                    current_screen = 2
                      
                sleep_ms(50)
                screenArr[current_screen].draw_screen()
                sleep_ms(100)
              
            if(state_backward):
                #go to past screen and load, loop if past first data screen
                current_screen-=1
                if(current_screen<2):
                    current_screen = 4
                      
                sleep_ms(50)
                screenArr[current_screen].draw_screen()
                sleep_ms(100)
            
            if(state_solar):
                if(solar_toggle_msg.value == "Disabled"):
                    solar_toggle_msg.value = "Enabled"
                elif(solar_toggle_msg.value == "Enabled"):
                    solar_toggle_msg.value = "Disabled"
                
                #store last screen and load solar flag screen
                last_screen = current_screen
                current_screen = 6
                screenArr[current_screen].draw_screen()
                
                #update flag
                solar_flag = not solar_flag
                sleep(4)
                
                #return to last screen
                current_screen = last_screen
                screenArr[current_screen].draw_screen()
                sleep(.5)
            
            ###timing loops###
            current_time = ticks_ms()

            #charge check
            if ticks_diff(current_time, last_updates[0]) >= timing_arr[0]:
                
                bat_v = charge_adc.read_u16() * (supply_v / 65535) * gain_factor
                
                voltage_arr[volt_count] = bat_v
                volt_count+=1
                
                if(volt_count == len(voltage_arr)):
                    #sum the last 10 voltages and average them, then find charge %
                    bat_v_avg = average_volt(voltage_arr)
                    volt_count = 0
                    
                    #find charge percentage based on the average
                    charge = round(calc_charge(bat_v_avg), 2)
                    
                    #update charge message
                    if(current_screen == 2):
                        charge_msg.draw_data(display, str(charge))
                        #date_msg.draw_data(display, bat_v_avg)
                    else:
                        charge_msg.value = str(charge)
                    
                last_updates[0] = current_time
                
            #datetime check
            if ticks_diff(current_time, last_updates[1]) >= timing_arr[1]:
                #pull current datetime
                datetime = rtc.datetime()
                
                #get output strings for date and time
                format_date, format_time = format_datetime(datetime)
                
                #update data and time messages
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
                temp_f= round((temp_c * (9/5) + 32), 1)   #convert the temperature value to fahrenheit
                
                #update temp message
                if(current_screen == 3):
                    temp_msg.draw_data(display, str(temp_f))
                else:
                    temp_msg.value = str(temp_f)
                    
                last_updates[2] = current_time
            
            #altitude check
            if ticks_diff(current_time, last_updates[3]) >= timing_arr[3]:
                #read current altitude
                altitude = round(bmp.altitude, 1)
                
                #update altitude message
                if(current_screen == 3):
                    alt_msg.draw_data(display, str(altitude))
                else:
                    alt_msg.value = str(altitude)
                    
                last_updates[3] = current_time
            
            #distance check
            if ticks_diff(current_time, last_updates[4]) >= timing_arr[4]:
                #set old position as current
                old_pos = pos_arr
                #read accelerometer values and subtract idle offset
                d_ax=imu.accel.x - idle_ax
                d_ay=imu.accel.y - idle_ay
                
                #if either reading is greater than a threshold, compute double-integral to find position
                if(abs(d_ax) > .1 or abs(d_ay) > .1):
                    accel_arr = [d_ax * grav_convert / ACCELEROMETER_SENSITIVITY / 2 , d_ay * grav_convert / ACCELEROMETER_SENSITIVITY / 2]
                    vel_arr = [vel_arr[0] + accel_arr[0]*TIME_INTERVAL, vel_arr[1] + accel_arr[1]*TIME_INTERVAL]
                    pos_arr = [round(pos_arr[0] + vel_arr[0]*TIME_INTERVAL, 3), round(pos_arr[1] + vel_arr[1]*TIME_INTERVAL, 3)]
                    
                    #add to total distance
                    distance += ((pos_arr[0]-old_pos[0])**2 + (pos_arr[1]-old_pos[1])**2)**.5
                distance = round(distance, 2)
                
                #if distance is greater than a minimum, update distance message
                if(distance > .01):
                    if(current_screen == 4):
                        dist_msg.draw_data(display, str(distance))
                    else:
                        dist_msg.value = str(distance)
                    
                last_updates[4] = current_time
                
            #steps check
            if ticks_diff(current_time, last_updates[5]) >= timing_arr[5]:
                #set previous steps to current steps
                prev_steps = steps
                #read accelerometer values for steps
                s_ax=round(imu.accel.x - idle_ax, 2)
                s_ay=round(imu.accel.y - idle_ay, 2)
                s_az=round(imu.accel.z - idle_az, 2)
                
                #calculate magnitutde of readings
                accel_magnitude = (s_ax ** 2 + s_ay ** 2 + s_az ** 2) ** 0.5

                # Detect a step based on the change in acceleration in comparison to a threshold
                # also check if it is the first pass through, to eliminate an extra step being calculated
                if ((accel_magnitude - abs(last_accel[2]) > threshold) and (not firstStep)):
                    steps += 1
                
                if(firstStep):
                    firstStep = False #update to signify first passthrough done
                    
                #reord last acceleration readings
                last_accel = [s_ax, s_ay, s_az]
                
                #update steps message
                if(current_screen == 4 and steps > prev_steps):
                    steps_msg.draw_data(display, str(steps))
                else:
                    steps_msg.value = str(steps)
                    
                last_updates[5] = current_time

            #LDR check
            if ticks_diff(current_time, last_updates[6]) >= timing_arr[6]:
                if(solar_flag):
                    #read voltages from channels 1 to 4 on MCP3234
                    
                    for i in range(4):
                        ldr_voltages[i] = read_channel(i, i2c0)
                        sleep(.1)
                    
                    #rotate servos based off of voltage readings
                    move_amount_UD = move_servos(servos, ldr_voltages, servo_thresh, move_amount_UD)
                
                last_updates[6] = current_time

            
            sleep_ms(10)
            
    except Exception as e:
        print(e)
        display.clear()
        sleep(.5)
        current_screen = 5
        screenArr[current_screen].draw_screen()
        
        sleep(2)
        #display.clear()
        
        while(True):
            state_reset = not reset.value()
            if(state_reset):
                break;
            sleep(.1)
        main()
        
#call main on startup
main()
