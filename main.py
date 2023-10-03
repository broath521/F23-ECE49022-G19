"""ILI9341 demo (fonts)."""
from time import sleep
from random import random, seed
from src.ili9341 import Display, color565
from machine import Pin, SPI
from utime import ticks_cpu, ticks_diff, ticks_ms, ticks_diff, sleep_ms
from src.xglcd_font import XglcdFont
from src.screens import DataMessage, Screen

def main():
    sleep(.5)
    """Test code."""
    try:
        #Setup SPI connections and display object
        spi = SPI(0, baudrate=10000000, polarity=1, phase=1, bits=8, firstbit=SPI.MSB,
                      sck=Pin(18), mosi=Pin(19), miso=Pin(16))
        display = Display(spi, dc=Pin(15), cs=Pin(17), rst=Pin(14))

        #load the chosen font into the system
        #print('Loading fonts...')
        #print('Loading unispace')
        fontType = XglcdFont('fonts/Unispace12x24.c', 12, 24)

        #setup GPIO pins for push buttons
        reset = Pin(10, Pin.IN)
        forward = Pin(11, Pin.IN)
        backward = Pin(12, Pin.IN)

        ### initialize screen messages and objects ###
        default_val = "0"
        
        #product logo loading
        suns_message = DataMessage("Sun Seeker", int(120 - 5*fontType.width), int(300 - (fontType.height/2)),
                               fontType, color565(255,255,255))
        
        #first screen messages
        charge_msg = DataMessage("Charge: ", 0, 60, fontType, color565(255,255,255), value = default_val, unit = "%")
        
        time_msg = DataMessage("Time: ", 0, charge_msg.y + int(2*fontType.height),
                               fontType, color565(255,255,255), value = default_val)
        
        screen1 = Screen(display, [charge_msg, time_msg, suns_message])
        
        #second screen messages
        temp_msg = DataMessage("Temperature: ", 0, 60, fontType, color565(255,255,255), value = default_val, unit = "F")
        hum_msg = DataMessage("Humidity: ", 0, temp_msg.y + int(2*fontType.height),
                               fontType, color565(255,255,255), value = default_val, unit = "g/m^3")
        
        screen2 = Screen(display, [temp_msg, hum_msg, suns_message])
        
        #third screen messages
        dist_msg = DataMessage("Distance: ", 0, 60, fontType, color565(255,255,255), value = default_val, unit = "m")
        alt_msg = DataMessage("Altitude: ", 0, dist_msg.y + int(2*fontType.height),
                               fontType, color565(255,255,255), value = default_val, unit = "m")
        steps_msg = DataMessage("Steps: ", 0, alt_msg.y + int(2*fontType.height),
                               fontType, color565(255,255,255), value = default_val, unit = "steps")
        
        screen3 = Screen(display, [dist_msg, alt_msg, steps_msg, suns_message])
        
        screenArr = [screen1, screen2, screen3]

        #initialize remaining variables
        current_screen = 0
        screenArr[current_screen].draw_screen()
        timing_arr = [5000, 5000, 5000, 5000, 5000, 5000, 5000]
        last_updates = [ticks_ms()]*7
        seed(ticks_cpu())
        
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
              sleep_ms(100)
              
            if(state_forward):
              
              current_screen+=1
              if(current_screen>2):
                  current_screen = 0
                  
              sleep_ms(50)
              screenArr[current_screen].draw_screen()
              sleep_ms(200)
              
            if(state_backward):
              
              current_screen-=1
              if(current_screen<0):
                  current_screen = 2
                  
              sleep_ms(50)
              screenArr[current_screen].draw_screen()
              sleep_ms(200)
            
            ###timing loops###
            current_time = ticks_ms()

            #charge check
            if ticks_diff(current_time, last_updates[0]) >= timing_arr[0]:
                r = round(random() * 100.0, 2)
                
                if(current_screen == 0):
                    charge_msg.draw_data(display, str(r))
                else:
                    charge_msg.value = str(r)
                    
                last_updates[0] = current_time
                
            #time check
            if ticks_diff(current_time, last_updates[1]) >= timing_arr[1]:
                r = int(random() * 24)
                
                if(current_screen == 0):
                    time_msg.draw_data(display, str(r))
                else:
                    time_msg.value = str(r)
                    
                last_updates[1] = current_time
                
            #temp check
            if ticks_diff(current_time, last_updates[2]) >= timing_arr[2]:
                r = round(60 + random() * 20.0, 1)
                
                if(current_screen == 1):
                    temp_msg.draw_data(display, str(r))
                else:
                    temp_msg.value = str(r)
                    
                last_updates[2] = current_time
                
            #humidity check
            if ticks_diff(current_time, last_updates[3]) >= timing_arr[3]:
                r = round(random() * 30.0, 1)
                
                if(current_screen == 1):
                    hum_msg.draw_data(display, str(r))
                else:
                    hum_msg.value = str(r)
                    
                last_updates[3] = current_time
                
            #distance check
            if ticks_diff(current_time, last_updates[4]) >= timing_arr[4]:
                r = round(random() * 1000.0, 1)
                
                if(current_screen == 2):
                    dist_msg.draw_data(display, str(r))
                else:
                    dist_msg.value = str(r)
                    
                last_updates[4] = current_time
                
            #altitude check
            if ticks_diff(current_time, last_updates[5]) >= timing_arr[5]:
                r = round(random() * 1000.0, 1)
                
                if(current_screen == 2):
                    alt_msg.draw_data(display, str(r))
                else:
                    alt_msg.value = str(r)
                    
                last_updates[5] = current_time
                
            #steps check
            if ticks_diff(current_time, last_updates[6]) >= timing_arr[6]:
                r = int(random() * 1000.0)
                
                if(current_screen == 2):
                    steps_msg.draw_data(display, str(r))
                else:
                    steps_msg.value = str(r)
                    
                last_updates[6] = current_time


            sleep_ms(10)
            
    except KeyboardInterrupt:
        display.cleanup()
        


main()
