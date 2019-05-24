#!/usr/bin/env python
#
#
#
import time
import logging

__version__ = '0.1'

logger = logging.getLogger(__name__)

try:
    import hid
    import colorsys
    import numpy as np
except ImportError as e:
    logger.info('Missing a few modules... can only send commands.')


class BusyLight(object):
    """
    Simple class for BusyLight
    """
    def __init__(self, red=0, green=0, blue=0, blink=0, tone='quiet', vol=0, vendor_id=0x27bb, product_id=0x3bcd):
        super(BusyLight, self).__init__()
        
        self.tone_names = ['openoffice','funky','fairytale','kuandotrain',
                           'telephonenordic','telephoneoriginal',
                           'telephonepickmeup','buzz']

        self.red=red
        self.green=green
        self.blue=blue
        self.blink_rate=blink
        if hasattr(tone, 'capitalize'):
            self.tone=tone
        else:
            self.tone=self.tone_names[tone]
        self.vol=vol
        self._vendor_id = vendor_id
        self._product_id = product_id
        self.buffer = None
        self.playlist = []

        self.positions = {
            'r': 3,
            'g': 4,
            'b': 5,
            't': 8,
            'blink':7,
        }
        
        self.tones = {
            'openoffice'        : 136,
            'quiet'             : 144,
            'funky'             : 152,
            'fairytale'         : 160,
            'kuandotrain'       : 168,
            'telephonenordic'   : 176,
            'telephoneoriginal' : 184,
            'telephonepickmeup' : 192,
            'buzz'              : 216,
        }

        self.device = hid.device()
        self.device.open(self._vendor_id, self._product_id)
        self.device.set_nonblocking(1)

        self.reset_buffer()
        self.update_buffer()

    def reset_buffer(self):
        """
        Method to reset the buffer to remove light/sound. 
        """

        self.buffer = [0,16,0,0,0,0,0,0,128] \
                      + [0]*50 \
                      + [255, 255, 255, 255, 6, 147]
        self.write()

    def update_buffer(self):
        """
        Method to update the buffer.
        """

        # update the colors and blink rate
        self.buffer[self.positions['r']] = self.red
        self.buffer[self.positions['g']] = self.green
        self.buffer[self.positions['b']] = self.blue
        self.buffer[self.positions['blink']] = self.blink_rate
        # update the tone 
        self.buffer[self.positions['t']] = self.tones[self.tone]
        # ubdate volume
        self.buffer[self.positions['t']] += self.vol

        # update the checksum
        checksum = sum(self.buffer[0:63])
        self.buffer[63] = (checksum >> 8) & 0xffff
        self.buffer[64] = checksum % 256

        logger.debug(f'updating buffer: {self.buffer}')

    def set_color(self,r,g,b, blink_rate=0):
        """
        Set the color
        """
        logger.debug(f'updating color: {r} {g} {b} {blink_rate}')
        self.red = r
        self.green = g
        self.blue = b
        self.blink_rate = blink_rate

    def add_to_playlist(self):
        """
        Add the current buffer to the playlist
        """
        self.update_buffer()
        self.playlist.append(self.buffer.copy())

    def write(self, buff=None):
        """
        Method to write buffer to BusyLight
        """

        if buff is not None:
            self.buffer = buff

        logger.debug(f'writing: {self.buffer}')
        self.device.write(self.buffer)

    def close(self):
        self.device.close()

    def play_sequence(self, wait_time=1):
        """
        Method to run through a list of buffers to write.
        """
        
        for buff in self.playlist:
            self.write(buff=buff)
            time.sleep(wait_time)
            # self.update_buffer()

        # clear the playlist once finished
        self.reset_buffer()
        self.playlist = []

def crazy_lights(length=100, wait_time=1):
    """
    Function to build a playlist of crazy blinking lights.
    """

    # get the busylight opbject
    bl = BusyLight()
    random_colors = np.random.randint(0,255, size=(length,3))
    for r,g,b in random_colors:
        bl.set_color(r,g,b)
        bl.add_to_playlist()
    bl.play_sequence(wait_time=wait_time)
    bl.close()

def smooth_rainbow(wait_time=1, steps=100):
    """
    Function to build a smooth rainbow transition
    """

    bl = BusyLight()
    for hue in np.linspace(0,1,steps):
        for value in [0.2,0.4,0.6,0.8,1.0,0.8,0.6,0.4,0.2]:
            r,g,b = colorsys.hsv_to_rgb(hue, 1.0, value)
            R, G, B = int(255 * r), int(255 * g), int(255 * b)
            bl.set_color(R,G,B)
            bl.add_to_playlist()
    bl.play_sequence(wait_time=wait_time)
    bl.close()

def clear_bl():
    """
    Function to clear the buffer and display/play nothing.
    """
    bl = BusyLight()
    bl.write()
    bl.close()
