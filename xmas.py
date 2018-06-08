#!/usr/bin/env python

import sys
from recorder import SwhRecorder
from jinja2 import Template
import math
import time
import signal
from http.server import HTTPServer, BaseHTTPRequestHandler, HTTPStatus
import selectors

try:
    from neopixel import Adafruit_NeoPixel, Color
    has_pixels = True
except:
    has_pixels = False
    import pygame


if hasattr(selectors, 'PollSelector'):
    _ServerSelector = selectors.PollSelector
else:
    _ServerSelector = selectors.SelectSelector


PORT = 8080

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
    print('shutdown starting')
    visualization.SR.close()
    if not has_pixels:
        pygame.quit()
    sys.exit()


class Visualization(object):

    VISUALIZATION_METHOD_CHOICES = (
        ('frequency_color', 'Frequency Color'),
        ('single_frequency_amplitude', 'Single Frequency Color'),
        ('color_change_frequency_amplitude', 'Color Change Frequency Amplitude'),
    )
    VISUALIZATION_METHODS = [choice[0] for choice in VISUALIZATION_METHOD_CHOICES]
    visualization_method = VISUALIZATION_METHODS[-1]
    single_frequency_amplitue_color = (255, 255, 255)
    max_db = 1020

    def __init__(self):
        self.dbs = []
        for _ in range(LED_COUNT):
            self.dbs.append(0)

        self.start_time = time.time()

        self.SR = SwhRecorder()
        self.SR.setup()
        self.SR.continuousStart()

        if has_pixels:
            # Create NeoPixel object with appropriate configuration.
            self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
            # Intialize the library (must be called once before other functions).
            self.strip.begin()
        else:
            pygame.init()
            size = 20
            width = int(math.sqrt(LED_COUNT))
            self.screen = pygame.display.set_mode((size * width, size * (width + 1)))
            self.boxes = []
            for led in range(LED_COUNT):
                y = int(led / width) * size
                x = led % width * size
                box = pygame.Rect(x, y, size, size)
                color = int((led * 255.) / LED_COUNT)
                self.screen.fill((color, color, color), box)
                self.boxes.append(box)
            pygame.display.update()

    def run_fft(self):
        xs, ys = self.SR.fft(trimBy=False)

        for led in range(LED_COUNT):
            # 15 -> 315 is the frequency range for most music (deep bass should probably remove the +15)
            led_num = int(led * (300 / LED_COUNT)) + 15
            db = int(ys[led_num] / (20 - (led / (LED_COUNT / 20)) + 1))
            if db > self.dbs[led]:  # jump up fast
                self.dbs[led] = db
            else:  # fade slowly
                self.dbs[led] = int((self.dbs[led] * 2 + db) / 3)

    def loop(self):
        while True:
            if not has_pixels:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        shutdown()
            self.run_fft()
            self.display_fft()
            httpd.serve_once()

    def write_pixel(self, index, rgb_color):
        if has_pixels:
            self.strip.setPixelColor(index, *rgb_color)
        else:
            self.screen.fill(rgb_color, self.boxes[index])

    def display_frequency_color(self):
        for led in range(LED_COUNT):
            rgb_color = rgb_wheel(self.dbs[led])
            self.write_pixel(led, rgb_color)

    def display_single_frequency_amplitude(self):
        for led in range(LED_COUNT):
            rgb_color = [
                min(int(color * self.dbs[led] / self.max_db), 255) for color in self.single_frequency_amplitue_color]
            self.write_pixel(led, rgb_color)

    def display_color_change_frequency_amplitude(self):
        time_degrees = int((time.time() - self.start_time) * 45)  # rotate colors in 8 seconds
        colors = (
            int((math.sin(math.radians(time_degrees)) + 1) * 127.5),
            int((math.sin(math.radians(time_degrees + 90)) + 1) * 127.5),
            int((math.sin(math.radians(time_degrees + 180)) + 1) * 127.5))

        for led in range(LED_COUNT):
            rgb_color = [
                min(int(color * self.dbs[led] / self.max_db), 255) for color in colors]
            self.write_pixel(led, rgb_color)

    def display_fft(self):
        getattr(self, 'display_{}'.format(self.visualization_method))()

        if has_pixels:
            self.strip.show()
        else:
            pygame.display.update()


class Server(BaseHTTPRequestHandler):
    isLeaf = True

    def __init__(self, *args, **kwargs):
        with open('index.html', 'r') as f:
            self.index = Template(f.read())
        super(Server, self).__init__(*args, **kwargs)

    def do_GET(self):
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-type", 'text/html; charset=utf-8')
        self.end_headers()
        template_args = {
            'visualization_method_choices': Visualization.VISUALIZATION_METHOD_CHOICES,
        }
        self.wfile.write(bytes(self.index.render(**template_args), 'utf-8'))

    def do_POST(self):
        visualization_method = str(self.rfile.peek(), 'utf-8').split('=')[-1]
        if visualization_method in Visualization.VISUALIZATION_METHODS:
            visualization.visualization_method = visualization_method

        self.send_response(HTTPStatus.FOUND)
        self.send_header("Location", self.path)
        self.end_headers()


class CustomHTTPServer(HTTPServer):

    def serve_once(self):
        with _ServerSelector() as selector:
            selector.register(self, selectors.EVENT_READ)
            ready = selector.select(.001)
            if ready:
                self._handle_request_noblock()


def signal_handler(signal, frame):
    print('You pressed Ctrl+C')
    shutdown()


signal.signal(signal.SIGINT, signal_handler)
httpd = CustomHTTPServer(("", PORT), Server)
visualization = Visualization()
visualization.loop()
