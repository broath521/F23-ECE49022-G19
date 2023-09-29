"""ILI9341 demo (fonts)."""
from time import sleep
from ili9341 import Display, color565
from machine import Pin, SPI
from utime import ticks_cpu, ticks_diff, ticks_ms, ticks_diff, sleep_ms
from xglcd_font import XglcdFont
from screens import DataMessage, Screen

def test():
    """Test code."""
    try:
        #Setup SPI connections and display object
        spi = SPI(0, baudrate=10000000, polarity=1, phase=1, bits=8, firstbit=SPI.MSB,
                      sck=Pin(18), mosi=Pin(19), miso=Pin(16))
        display = Display(spi, dc=Pin(15), cs=Pin(17), rst=Pin(14))

        #load the chosen font into the system
        print('Loading fonts...')
        print('Loading unispace')
        unispace = XglcdFont('fonts/Unispace12x24.c', 12, 24)

        #setup GPIO pins for push buttons
        reset = Pin(10, Pin.IN)
        forward = Pin(11, Pin.IN)
        backward = Pin(12, Pin.IN)

        ### initialize screen messages and objects ###
        #first screen messages
        charge_msg = DataMessage("Charge: ", 60, 300, unispace, color565(255,255,255));
        time_msg = DataMessage("Time: ", charge_msg.x + int(2*unispace.height),
                                   300, unispace, color565(255,255,255));
        
        screen1 = Screen(display, [charge_msg, time_msg])
        
        #second screen messages
        temp_msg = DataMessage("Temperature: ", 60, 300, unispace, color565(255,255,255));
        hum_msg = DataMessage("Humidity: ", temp_msg.x + int(2*unispace.height),
                                   300, unispace, color565(255,255,255));
        
        screen2 = Screen(display, [temp_msg, hum_msg])
        
        #third screen messages
        dist_msg = DataMessage("Distance: ", 60, 300, unispace, color565(255,255,255));
        alt_msg = DataMessage("Altitude: ", dist_msg.x + int(2*unispace.height),
                                   300, unispace, color565(255,255,255));
        steps_msg = DataMessage("Steps: ", alt_msg.x + int(2*unispace.height),
                                   300, unispace, color565(255,255,255));
        
        screen3 = Screen(display, [dist_msg, alt_msg, steps_msg])
        
        screenArr = [screen1, screen2, screen3]

        current_screen = 0
        screenArr[current_screen].draw_screen()
        
        while True:
            # Get the current time
            current_time = ticks_ms()
            
            #check state of GPIO pins
            state_reset = not reset.value()
            state_forward = not forward.value()
            state_backward = not backward.value()
            
            if(state_reset):
              print("reset")
              sleep_ms(100)
              
            if(state_forward):
              print("forward")
              
              current_screen+=1
              if(current_screen>2):
                  current_screen = 0
                  
              sleep_ms(50)
              screenArr[current_screen].draw_screen()
              sleep_ms(200)
              
            if(state_backward):
              print("backward")
              
              current_screen-=1
              if(current_screen<0):
                  current_screen = 2
                  
              sleep_ms(50)
              screenArr[current_screen].draw_screen()
              sleep_ms(200)
    
            
    except KeyboardInterrupt:
        display.cleanup()


test()
