#!/usr/bin/env python

import sys
from recorder import SwhRecorder
import signal

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
        # print("{},{}".format(xs.size, ys.size))

        for led in range(LED_COUNT):
            led_num = int(led * (led / 100.0))
            # print(led_num)
            db = int(ys[led_num] / (20 - (led / 15)))
            if db > leds[led]:
                leds[led] = db
            else:
                leds[led] = int((leds[led] * 4 + db) / 5)
            # print(db)
            if has_pixels:
                strip.setPixelColor(led, pixel_wheel(leds[led]))
            else:
                screen.fill(rgb_wheel(leds[led]), boxes[led])
        # print('')
        if has_pixels:
            strip.show()
        else:
            pygame.display.update()
        # print("")

        # print(min(ys), max(ys))


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
        screen = pygame.display.set_mode((500, 800))
        boxes = []
        size = 10
        for led in range(LED_COUNT):
            y = int(led / 8) * size
            x = led % 8 * size
            box = pygame.Rect(x, y, x + size, y + size)
            color = int((led / 8) * 255 / (LED_COUNT / 8))
            screen.fill((color, color, color), box)
            boxes.append(box)
        pygame.display.update()
        run_fft()
