#!/usr/bin/env python

import sys
from recorder import SwhRecorder
import signal
import math
import time

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

# visualization methods: 'frequency_color', 'simple_frequency_amplitude', 'color_change_frequency_amplitude'
VISUALIZATION_METHOD = 'color_change_frequency_amplitude'
SIMPLE_FREQUENCY_AMPLITUDE_COLOR = (255, 255, 255)
MAX_DB = 1020
color_change_frequency_amplitude_time = 0
start_time = time.time()


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


def write_pixel(index, rgb_color):
    if has_pixels:
        strip.setPixelColor(index, *rgb_color)
    else:
        screen.fill(rgb_color, boxes[index])


def display_frequency_color(dbs):
    for led in range(LED_COUNT):
        rgb_color = rgb_wheel(dbs[led])
        write_pixel(led, rgb_color)


def display_simple_frequency_amplitude(dbs):
    for led in range(LED_COUNT):
        rgb_color = [min(int(color * dbs[led] / MAX_DB), 255) for color in SIMPLE_FREQUENCY_AMPLITUDE_COLOR]
        write_pixel(led, rgb_color)


def display_color_change_frequency_amplitude(dbs):
    global color_change_frequency_amplitude_time

    color_change_frequency_amplitude_time = int((time.time() - start_time) * 45)  # rotate colors in 8 seconds
    color_change_frequency_amplitude_color = (
        int((math.sin(math.radians(color_change_frequency_amplitude_time)) + 1) * 127.5),
        int((math.sin(math.radians(color_change_frequency_amplitude_time + 90)) + 1) * 127.5),
        int((math.sin(math.radians(color_change_frequency_amplitude_time + 180)) + 1) * 127.5))

    for led in range(LED_COUNT):
        rgb_color = [min(int(color * dbs[led] / MAX_DB), 255) for color in color_change_frequency_amplitude_color]
        write_pixel(led, rgb_color)


def display_fft(dbs):
    if VISUALIZATION_METHOD == 'frequency_color':
        display_frequency_color(dbs)
    elif VISUALIZATION_METHOD == 'simple_frequency_amplitude':
        display_simple_frequency_amplitude(dbs)
    elif VISUALIZATION_METHOD == 'color_change_frequency_amplitude':
        display_color_change_frequency_amplitude(dbs)
    else:
        display_frequency_color(dbs)

    if has_pixels:
        strip.show()
    else:
        pygame.display.update()


def run_fft():
    dbs = []
    for _ in range(LED_COUNT):
        dbs.append(0)

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
            if db > dbs[led]:  # jump up fast
                dbs[led] = db
            else:  # fade slowly
                dbs[led] = int((dbs[led] * 2 + db) / 3)

        display_fft(dbs)


def shutdown():
    SR.close()
    if not has_pixels:
        pygame.quit()
    sys.exit(0)


def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    shutdown()


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
