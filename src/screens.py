from lib.ili9341 import Display, color565
from machine import Pin, SPI
from utime import sleep_ms
from lib.xglcd_font import XglcdFont

class DataMessage(object):
    
    def __init__(self, message, x, y, font, color, value = "", unit = ""):
        self.message = message
        self.x = x
        self.y = y
        self.font = font
        self.color = color
        self.value = value
        self.unit = unit

    def draw_data(self, display, data):
        if(len(str(data)) < len(self.value)):
            display.draw_text(int(self.x + len(self.message) * self.font.width), int(self.y), self.value + " " + self.unit,
                          self.font, 0, landscape=False)
        
        self.value = str(data)
        
        display.draw_text(int(self.x + len(self.message) * self.font.width), int(self.y), self.value + " " + self.unit,
                          self.font, self.color, landscape=False)
        
class Screen(object):
    def __init__(self, display, messages = []):
        self.display = display
        self.messages = messages

    def draw_screen(self):
        self.display.clear()
        for msg in self.messages:
            self.display.draw_text(int(msg.x), int(msg.y), msg.message, msg.font,
                              msg.color, landscape=False)
            msg.draw_data(self.display, msg.value)
        
        #self.display.draw_image("images/Python41x49.raw", 100, 220, 25, 25)

def setup_screens(display):
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
        
        return screenArr, charge_msg, date_msg, time_msg, temp_msg, alt_msg, dist_msg, steps_msg, solar_toggle_msg