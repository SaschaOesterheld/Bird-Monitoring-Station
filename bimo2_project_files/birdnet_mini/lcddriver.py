import sys

sys.path.append("./lib")

import i2c_lib
import time 
from datetime import datetime as dt
import weather_i2c

# LCD Address
ADDRESS = 0x27

# commands
LCD_CLEARDISPLAY = 0x01
LCD_RETURNHOME = 0x02
LCD_ENTRYMODESET = 0x04
LCD_DISPLAYCONTROL = 0x08
LCD_CURSORSHIFT = 0x10
LCD_FUNCTIONSET = 0x20
LCD_SETCGRAMADDR = 0x40
LCD_SETDDRAMADDR = 0x80

# flags for display entry mode
LCD_ENTRYRIGHT = 0x00
LCD_ENTRYLEFT = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

# flags for display on/off control
LCD_DISPLAYON = 0x04
LCD_DISPLAYOFF = 0x00
LCD_CURSORON = 0x02
LCD_CURSOROFF = 0x00
LCD_BLINKON = 0x01
LCD_BLINKOFF = 0x00

# flags for display/cursor shift
LCD_DISPLAYMOVE = 0x08
LCD_CURSORMOVE = 0x00
LCD_MOVERIGHT = 0x04
LCD_MOVELEFT = 0x00

# flags for function set
LCD_8BITMODE = 0x10
LCD_4BITMODE = 0x00
LCD_2LINE = 0x08
LCD_1LINE = 0x00
LCD_5x10DOTS = 0x04
LCD_5x8DOTS = 0x00

# flags for backlight control
LCD_BACKLIGHT = 0x08
LCD_NOBACKLIGHT = 0x00

En = 0b00000100  # Enable bit
Rw = 0b00000010  # Read/Write bit
Rs = 0b00000001  # Register select bit


class lcd:
    # Initializes objects and lcd
    def __init__(self,width=20,height=4):
        print("Initialising LCD...")
        self.lcd_device = i2c_lib.i2c_device(ADDRESS)

        self.lcd_write(0x03)
        self.lcd_write(0x03)
        self.lcd_write(0x03)
        self.lcd_write(0x02)

        self.lcd_write(LCD_FUNCTIONSET | LCD_2LINE | LCD_5x8DOTS | LCD_4BITMODE)
        self.lcd_write(LCD_DISPLAYCONTROL | LCD_DISPLAYON)
        self.lcd_write(LCD_CLEARDISPLAY)
        self.lcd_write(LCD_ENTRYMODESET | LCD_ENTRYLEFT)
        # Time before display changes what its showing
        self.display_time = 3
        self.width = width
        self.height = height
        # Last Bird heard
        self.last_bird = "None"
        self.last_bird_timestamp = ""
        self.last_bird_updated = False
        time.sleep(0.2)
        
        self.weather_sensor=weather_i2c.WeatherSensor()

        # clocks EN to latch command
    
    def adjust_string(self,text,display_in_line,display_height=4,display_width=16):
        if display_in_line>display_height:return ""
        else:
            temp = str(text)
            return text.ljust(width)[:width]
            
    def split_for_lcd(self):
        
        text = str(self.last_bird)
        width = self.width
        # Fits entirely on one line
        if len(text) <= width:
            return text, ""

        # Look for last space or hyphen within width
        split_pos = -1
        for i in range(width):
            if text[i] in (" ", "-"):
                split_pos = i

        if split_pos != -1:
            line1 = text[:split_pos].rstrip()
            line2 = text[split_pos + 1:].lstrip()
        else:
            # Hard split with hyphen
            line1 = text[:width - 1] + "-"
            line2 = text[width - 1:]

        return line1, line2

    def lcd_strobe(self, data):
        self.lcd_device.write_cmd(data | En | LCD_BACKLIGHT)
        time.sleep(.0005)
        self.lcd_device.write_cmd(((data & ~En) | LCD_BACKLIGHT))
        time.sleep(.0001)

    def lcd_write_four_bits(self, data):
        self.lcd_device.write_cmd(data | LCD_BACKLIGHT)
        self.lcd_strobe(data)

    # write a command to lcd
    def lcd_write(self, cmd, mode=0):
        self.lcd_write_four_bits(mode | (cmd & 0xF0))
        self.lcd_write_four_bits(mode | ((cmd << 4) & 0xF0))

    # Turn on/off the lcd backlight
    def lcd_backlight(self, state):
        if state in ("on", "On", "ON"):
            self.lcd_device.write_cmd(LCD_BACKLIGHT)
        elif state in ("off", "Off", "OFF"):
            self.lcd_device.write_cmd(LCD_NOBACKLIGHT)
        else:
            print("Unknown State!")

    # put string function
    def lcd_display_string(self, string, line):
        if line == 1:
            self.lcd_write(0x80)
        if line == 2:
            self.lcd_write(0xC0)
        if line == 3:
            self.lcd_write(0x94)
        if line == 4:
            self.lcd_write(0xD4)

        for char in string:
            self.lcd_write(ord(char), Rs)

    # clear lcd and set to home
    def lcd_clear(self):
        self.lcd_write(LCD_CLEARDISPLAY)
        self.lcd_write(LCD_RETURNHOME)

    def mainloop(self):
        print("Entering LCD Main Loop!")
        while True:
            self.lcd_clear()
            # Put Last Bird Info on LCD, and wait out LCD Timer
            datetime_now = dt.now()
            datetime_now = datetime_now.strftime("%d.%m.%Y %H:%M:%S")
            self.lcd_display_string(datetime_now,1)
            if self.last_bird_updated:
                self.last_bird_timestamp = f"({self.last_bird_timestamp})"
                self.last_bird_updated = False 
            self.lcd_display_string(f"Last heard{self.last_bird_timestamp}:", 2)
            print(self.last_bird)
            #Format and print bird name to screen
            line1,line2 = self.split_for_lcd()
            if line2 == ":" or line2 == "":line2=None
            self.lcd_display_string(line1, 3)
            if line2:
                self.lcd_display_string(line2, 4)
            time.sleep(self.display_time)
            # Get Weather Info, put Weather Info on LCD, and wait out LCD Timer
            self.lcd_clear()
            try:
                weather = self.weather_sensor.read()

            except Exception as e:
                print(e)
                self.lcd_display_string("Could not get",2)
                self.lcd_display_string("weather from ",3)
                self.lcd_display_string("sensor!",4)
                time.sleep(self.display_time)
                continue    
            if not weather: 
                self.lcd_display_string(r"No weather got:(",2)
                time.sleep(self.display_time)
                continue
            self.lcd_display_string(datetime_now,1)
            self.lcd_display_string(f"Tempe. : {weather['temperature']} C", 2)
            self.lcd_display_string(f"Luftf. : {weather['humidity']} %", 3)
            self.lcd_display_string(f"Luftd. : {weather['pressure']} hPa", 4)
            time.sleep(self.display_time)
