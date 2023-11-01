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
