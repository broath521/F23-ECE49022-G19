#list of module imports
from machine import ADC, Pin, SPI, I2C
from time import sleep
from random import random, seed
from lib.ili9341 import Display, color565
from utime import ticks_cpu, ticks_diff, ticks_ms, ticks_diff, sleep_ms
from src.screens import DataMessage, Screen, setup_screens
from src.data import calc_charge, average_volt, format_datetime
from src.solar import Servo, move_servos, read_channels
from lib.imu import MPU6050
from lib.bmp085 import BMP180
from lib.ds1307 import DS1307
import uasyncio as asyncio


async def button_loop(screenArr, i2c0, gain_factor, rtc, bmp, buttons):
    global current_screen, solar_flag
    while True:
        #check state of GPIO pins. Push buttons output reversed values due to debouncing setup.
        state_reset = not buttons[0].value()
        state_forward = not buttons[1].value()
        state_backward = not buttons[2].value()
        state_solar = not buttons[3].value()
        
        #button check logic
        if(state_reset):
            #Show reset screen, then recall all setup functions and values
            current_screen = 1
            screenArr[current_screen].draw_screen()
            
            voltages = read_channels(i2c0, 0x6c, 0)
            bat_v = voltages[0]
            bat_v_scaled = bat_v  * gain_factor
            charge = round(calc_charge(bat_v_scaled), 0)
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
            
            print("Reset Button Pressed")
            print("Steps: " + str(steps))
            print("Distance: " + str(distance) + " m")
            print("Temperature: " + str(temp) + " F")
            print("Altitude: " + str(altitude) + " m")
            print("Charge: " + str(charge) + " %")
            print("Date: " + format_date)
            print("Time: " + format_time)
            
            sleep_ms(10)
          
        elif(state_forward):
            #go to next screen and load, loop if past last data screen
            current_screen+=1
            if(current_screen>4):
                current_screen = 2
            '''print("Forward Pressed")
            print("Current Screen: " + str(current_screen-1))'''
            sleep_ms(100)
            screenArr[current_screen].draw_screen()
            sleep_ms(100)
          
        elif(state_backward):
            #go to past screen and load, loop if past first data screen
            current_screen-=1
            if(current_screen<2):
                current_screen = 4
            '''print("Backward Pressed")
            print("Current Screen: " + str(current_screen-1))'''
            sleep_ms(100)
            screenArr[current_screen].draw_screen()
            sleep_ms(100)
        
        elif(state_solar):
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
            
        await asyncio.sleep(0)
        
async def async_loop_1(timing_arr, i2c0, rtc, bmp, servos, servo_thresh, move_amount_UD, gain_factor, display):
    while True:
        ###timing loops###
        current_time = ticks_ms()

        #charge check
        if ticks_diff(current_time, last_updates[0]) >= timing_arr[0]:
            diff_arr[0] = ticks_diff(current_time, last_updates[0])
            voltages = read_channels(i2c0, 0x6c, 0)
            bat_v = voltages[0]
            bat_v_scaled = bat_v  * gain_factor
            charge = round(calc_charge(bat_v_scaled), 0)
            
            #update charge message
            if(current_screen == 2):
                charge_msg.draw_data(display, str(charge))
            else:
                charge_msg.value = str(charge)
                
            last_updates[0] = current_time
            
        await asyncio.sleep(0)
        current_time = ticks_ms()
        #datetime check
        if ticks_diff(current_time, last_updates[1]) >= timing_arr[1]:
            diff_arr[1] = ticks_diff(current_time, last_updates[1])
            #pull current datetime
            datetime = rtc.datetime()
            
            #get output strings for date and time
            format_date, format_time = format_datetime(datetime)
            
            #update data and time messages
            if(current_screen == 2):
                #date_msg.draw_data(display, format_date)
                time_msg.draw_data(display, format_time)
            else:
                date_msg.value = format_date
                time_msg.value = format_time

            last_updates[1] = current_time
        
        await asyncio.sleep(0)
        current_time = ticks_ms()
        #temp check
        if ticks_diff(current_time, last_updates[2]) >= timing_arr[2]:
            diff_arr[2] = ticks_diff(current_time, last_updates[2])
            temp_c = round(bmp.temperature, 1)        #get the temperature in degree celsius
            temp_f= round((temp_c * (9/5) + 32), 1)   #convert the temperature value to fahrenheit
            
            #update temp message
            if(current_screen == 3):
                temp_msg.draw_data(display, str(temp_f))
            else:
                temp_msg.value = str(temp_f)

            last_updates[2] = current_time
        
        await asyncio.sleep(0)
        current_time = ticks_ms()
        #altitude check
        if ticks_diff(current_time, last_updates[3]) >= timing_arr[3]:
            diff_arr[3] = ticks_diff(current_time, last_updates[3])
            #read current altitude
            altitude = round(bmp.altitude, 1)
            
            #update altitude message
            if(current_screen == 3):
                alt_msg.draw_data(display, str(altitude))
            else:
                alt_msg.value = str(altitude)

            last_updates[3] = current_time
        
        await asyncio.sleep(0)
        current_time = ticks_ms()
        #LDR check
        if ticks_diff(current_time, last_updates[5]) >= timing_arr[5]:
            diff_arr[5] = ticks_diff(current_time, last_updates[5])
            current_time = ticks_ms()
            if(solar_flag):
                #read voltages from channels 1 to 4 on MCP3234
                ldr_voltages = read_channels(i2c0, 0x6a)
                #rotate servos based off of voltage readings
                move_amount_UD = move_servos(servos, ldr_voltages, servo_thresh, move_amount_UD)

            last_updates[5] = current_time
            
async def async_loop_2(timing_arr, i2c1, imu, accel_arr, vel_arr, pos_arr, idle_ax, idle_ay, idle_az, last_accel, threshold, grav_convert, ACCELEROMETER_SENSITIVITY, TIME_INTERVAL, firstStep, display):
    distance = float(dist_msg.value)
    steps = int(steps_msg.value)
    while True:
        ###timing loops###
        current_time = ticks_ms()

        #distance check
        if ticks_diff(current_time, last_updates[4]) >= timing_arr[4]:
            diff_arr[4] = ticks_diff(current_time, last_updates[4])
            #print(diff_arr[4])
            #set old position as current
            old_pos = pos_arr
            #read accelerometer values and subtract idle offset
            d_ax=round(imu.accel.x - idle_ax, 2)
            d_ay=round(imu.accel.y - idle_ay, 2)
            d_az=round(imu.accel.z - idle_az, 2)

            #if either reading is greater than a threshold, compute double-integral to find position
            if(abs(d_ax) > .1 or abs(d_ay) > .1):
                accel_arr = [d_ax * grav_convert / ACCELEROMETER_SENSITIVITY / 2 , d_ay * grav_convert / ACCELEROMETER_SENSITIVITY / 2]
                vel_arr = [vel_arr[0] + accel_arr[0]*TIME_INTERVAL, vel_arr[1] + accel_arr[1]*TIME_INTERVAL]
                pos_arr = [round(pos_arr[0] + vel_arr[0]*TIME_INTERVAL, 3), round(pos_arr[1] + vel_arr[1]*TIME_INTERVAL, 3)]
                
                #add to total distance
                distance += ((pos_arr[0]-old_pos[0])**2 + (pos_arr[1]-old_pos[1])**2)**.5
            distance = round(distance, 2)
            
            print(distance)
            
            #if distance is greater than a minimum, update distance message
            if(distance > .01):
                if(current_screen == 4):
                    dist_msg.draw_data(display, str(distance))
                else:
                    dist_msg.value = str(distance)
            
            #set previous steps to current steps
            prev_steps = steps
            
            #calculate magnitutde of readings
            accel_magnitude = (d_ax ** 2 + d_ay ** 2 + d_az ** 2) ** 0.5

            # Detect a step based on the change in acceleration in comparison to a threshold
            # also check if it is the first pass through, to eliminate an extra step being calculated
            if ((accel_magnitude - abs(last_accel[2]) > threshold) and (not firstStep)):
                steps += 1
            
            if(firstStep):
                firstStep = False #update to signify first passthrough done
                
            #update last acceleration readings
            last_accel = [d_ax, d_ay, d_az]
            
            #update steps message
            if(current_screen == 4 and steps > prev_steps):
                steps_msg.draw_data(display, str(steps))
            else:
                steps_msg.value = str(steps)
                
            last_updates[4] = current_time
            
        await asyncio.sleep(0)
        
def main():
    global screenArr, charge_msg, date_msg, time_msg, temp_msg, alt_msg, dist_msg, steps_msg, solar_toggle_msg, current_screen
    global solar_flag, diff_arr, ldr_voltages, move_amount_UD, last_updates, distance
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
        
        buttons = [reset, forward, backward, toggle_solar]
        
        solar_flag = True #flag to disable/enable solar tracking
        
        #setup I2C devices
        i2c0 = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)
        i2c1 = I2C(1, sda=Pin(6), scl=Pin(7), freq=100000)
        
        #send general call reset to MCP3424 chips to latch their addr pins
        '''while True:
            try:
                i2c0.writeto(0x00, bytearray([0x06]))
                sleep(.3)
                break
            except:
                print("Fail")
                sleep(.3)
                pass'''

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
        
        screenArr, charge_msg, date_msg, time_msg, temp_msg, alt_msg, dist_msg, steps_msg, solar_toggle_msg = setup_screens(display)
        
        #time in between data updates (in ms)
        #charge, time, temp, altitude, distance/steps, LDRs
        timing_arr = [5500, 1000, 1000, 15500, 150, 1500]
        diff_arr = [0]*7
        
        seed(ticks_cpu())
        
        #used for averaging voltage readings, as ADC readings
        #are unstable due to fluctuating buck converter supply
        voltage_arr = [0]*30
        volt_count = 0
        
        #setup servos
        servo1 = Servo(machine.PWM(machine.Pin(8, mode=machine.Pin.OUT)), 400, 17476)
        servo2 = Servo(machine.PWM(machine.Pin(9, mode=machine.Pin.OUT)), 50)
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
        #rtc.datetime((2023,11,1,3,02,48,0,0)) #uncomment to set time (EST)

        #start system
        #################################################
        current_screen = 0
        screenArr[current_screen].draw_screen()
        
        #take first charge reading
        gain_factor = 12.09
        voltages = read_channels(i2c0, 0x6c, 0)
        bat_v = voltages[0]
        bat_v_scaled = bat_v  * gain_factor
        charge = round(calc_charge(bat_v_scaled), 0)
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
        steps_msg.value = str(steps)
        
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
        
        last_updates = [ticks_ms()]*6
        ##########################################################
        #main async logic loops
        loop = asyncio.get_event_loop()
        #loop.create_task(button_loop(screenArr, i2c0, gain_factor, rtc, bmp, buttons))
        loop.create_task(async_loop_1(timing_arr, i2c0, rtc, bmp, servos, servo_thresh, move_amount_UD, gain_factor, display))
        loop.create_task(async_loop_2(timing_arr, i2c1, imu, accel_arr, vel_arr, pos_arr, idle_ax, idle_ay, idle_az, last_accel, threshold, grav_convert, ACCELEROMETER_SENSITIVITY, TIME_INTERVAL, firstStep, display))
            
        # Start the event loop
        loop.run_forever()
    except KeyboardInterrupt:
        print("woops")
    '''except Exception as e:
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
        main()'''
        
#call main on startup
main()