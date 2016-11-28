#!/usr/bin/env python

#sudo apt-get install python-qt4 python-qwt5-qt4 python-matplotlib python-scipy python-pyaudio


import sys
from recorder import *
import signal
import math

from neopixel import *




# LED strip configuration:
LED_COUNT      = 300       # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 25     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)

def wheel(pos):
    """b->g->r color wheel from 0 to 1020, neopixels use grb format"""
    
    if pos < 255:
        return Color(pos , 0 , 255)
    elif pos < 510:
        pos -= 255
        return Color(255 , 0, 255 - pos )
    elif pos < 765:
        pos -= 510
        return Color(255 , pos, 0)
    elif pos<=1020:
        pos -= 765
        return Color(255 - pos, 255, 0)
    else:
        return Color(0, 255, 0)

def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    SR.close()
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    
    SR=SwhRecorder()
    SR.setup()
    SR.continuousStart()
    
    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
    # Intialize the library (must be called once before other functions).
    strip.begin()
    leds = []
    for led in range(LED_COUNT):
        leds.append(0)
    
    while True:
        xs,ys=SR.fft(trimBy=False)
        #print "%d,%d" % (xs.size,ys.size)

        for led in range(LED_COUNT):
            led_num = int(led * (led/100.0))
            #print led_num,
            db = int(ys[led_num]/(20-(led/15)))
            if db > leds[led]:
                leds[led] = db
            else:
                leds[led] = int((leds[led] * 4 + db) / 5 )
            #print db,
            strip.setPixelColor(led, wheel(leds[led] ))
        strip.show()
        #print ""
        
        #print min(ys),max(ys)