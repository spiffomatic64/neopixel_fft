# NeoPixel_FFT

Neopixel visualizer for audio FFT signal

Using the example from: http://www.swharden.com/wp/2013-05-09-realtime-fft-audio-visualization-with-python/

Visualized the fft from the microphone on my webcam over 300 neopixels. 

Starting with the lower frequencies, going up (in a log-ish mannor) to higher frequencies, low db=blue going to green, then red.

## Installation

Follow raspberrypi neopixel guide here: https://learn.adafruit.com/neopixels-on-raspberry-pi/software

sudo apt-get install python-matplotlib python-numpy python-scipy python-pyaudio 

## Usage

sudo python ./xmas.py

## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D

## History

11/27 Uploaded

## Credits

SWHarden.com

## License

TODO: Write license
