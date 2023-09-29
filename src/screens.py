from ili9341 import Display, color565
from machine import Pin, SPI
from utime import sleep_ms
from xglcd_font import XglcdFont

class DataMessage(object):
    
    def __init__(self, message, x, y, font, color, value = "", unit = ""):
        self.message = message
        self.x = x
        self.y = y
        self.font = font
        self.color = color
        self.value = value
        self.unit = unit
    
    def dataStr(self):
        return self.message + self.value + self.unit

class Screen(object):
    def __init__(self, display, messages = []):
        self.display = display
        self.messages = messages

    def draw_screen(self):
        self.display.clear()
        sleep_ms(100)
        for msg in self.messages:  
            self.display.draw_text(int(msg.x), int(msg.y), msg.dataStr(), msg.font,
                              msg.color, landscape=True)
