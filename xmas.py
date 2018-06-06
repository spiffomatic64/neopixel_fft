#!/usr/bin/env python

import sys
from recorder import SwhRecorder
import signal
import math

try:
    from neopixel import Adafruit_NeoPixel, Color
    has_pixels = True
except:
    has_pixels = False
    import pygame


# LED strip configuration:
LED_COUNT      = 300       # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 25     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)


def pixel_wheel(pos):
    """b->g->r color wheel from 0 to 1020, neopixels use grb format"""
    if pos < 255:
        return Color(pos, 0, 255)
    elif pos < 510:
        pos -= 255
        return Color(255, 0, 255 - pos)
    elif pos < 765:
        pos -= 510
        return Color(255, pos, 0)
    elif pos <= 1020:
        pos -= 765
        return Color(255 - pos, 255, 0)
    else:
        return Color(0, 255, 0)


def rgb_wheel(pos):
    """b->g->r color wheel from 0 to 1020, to (r, g, b)"""
    if pos < 255:
        return (0, pos, 255)
    elif pos < 510:
        pos -= 255
        return (0, 255, 255 - pos)
    elif pos < 765:
        pos -= 510
        return (pos, 255, 0)
    elif pos <= 1020:
        pos -= 765
        return (255, 255 - pos, 0)
    else:
        return (255, 0, 0)


def shutdown():
    SR.close()
    if not has_pixels:
        pygame.quit()
    sys.exit(0)


def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    shutdown()


def run_fft():
    leds = []
    for led in range(LED_COUNT):
        leds.append(0)

    while True:
        if not has_pixels:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    shutdown()

        xs, ys = SR.fft(trimBy=False)

        for led in range(LED_COUNT):
            # 15 -> 315 is the frequency range for most music (deep bass should probably remove the +15)
            led_num = int(led * (300 / LED_COUNT)) + 15
            db = int(ys[led_num] / (20 - (led / (LED_COUNT / 20)) + 1))
            if db > leds[led]:  # jump up fast
                leds[led] = db
            else:  # fade slowly
                leds[led] = int((leds[led] * 4 + db) / 5)
            if has_pixels:
                strip.setPixelColor(led, pixel_wheel(leds[led]))
            else:
                screen.fill(rgb_wheel(leds[led]), boxes[led])
        if has_pixels:
            strip.show()
        else:
            pygame.display.update()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    SR = SwhRecorder()
    SR.setup()
    SR.continuousStart()

    if has_pixels:
        # Create NeoPixel object with appropriate configuration.
        strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
        # Intialize the library (must be called once before other functions).
        strip.begin()
        run_fft()
    else:
        pygame.init()
        size = 20
        width = int(math.sqrt(LED_COUNT))
        screen = pygame.display.set_mode((size * width, size * (width + 1)))
        boxes = []
        for led in range(LED_COUNT):
            y = int(led / width) * size
            x = led % width * size
            box = pygame.Rect(x, y, size, size)
            color = int((led * 255.) / LED_COUNT)
            screen.fill((color, color, color), box)
            boxes.append(box)
        pygame.display.update()
        run_fft()
