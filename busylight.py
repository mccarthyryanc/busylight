#!/usr/bin/env python
#
#
#
try:
    import hid
    import colorsys
    import numpy as np
except ImportError as e:
    print('Missing a few non-standard modules... can only send commands.')

import click
import time
import socket
import socketserver

class BusyLight(object):
    """
    Simple class for BusyLight
    """
    def __init__(self, red=0, green=0, blue=0, blink=0, tone='quiet', vol=0,
                 verbose=0):
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
        self.verbose=verbose
        self._vendor_id = 0x27bb
        self._product_id = 0x3bcd
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

        if self.verbose > 0:
            print(f'updating buffer: {self.buffer}')

    def set_color(self,r,g,b, blink_rate=0):
        """
        Set the color
        """
        if self.verbose > 0:
            print(f'updating color: {r} {g} {b} {blink_rate}')
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

        if self.verbose > 0:
            buff = self.buffer
            print(f'writing: {buff}')
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

def crazy_lights(length=100, verbose=0, wait_time=1):
    """
    Function to build a playlist of crazy blinking lights.
    """

    # get the busylight opbject
    bl = BusyLight(verbose=verbose)
    random_colors = np.random.randint(0,255, size=(length,3))
    for r,g,b in random_colors:
        bl.set_color(r,g,b)
        bl.add_to_playlist()
    bl.play_sequence(wait_time=wait_time)
    bl.close()

def smooth_rainbow(wait_time=1, steps=100, verbose=0):
    """
    Function to build a smooth rainbow transition
    """

    bl = BusyLight(verbose=verbose)
    for hue in np.linspace(0,1,steps):
        for value in [0.2,0.4,0.6,0.8,1.0,0.8,0.6,0.4,0.2]:
            r,g,b = colorsys.hsv_to_rgb(hue, 1.0, value)
            R, G, B = int(255 * r), int(255 * g), int(255 * b)
            bl.set_color(R,G,B)
            bl.add_to_playlist()
    bl.play_sequence(wait_time=wait_time)
    bl.close()

def clear_bl(verbose=0):
    """
    Function to clear the buffer and display/play nothing.
    """
    bl = BusyLight(verbose=verbose)
    bl.write()
    bl.close()

# Socket Related Methods
class MyTCPHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print("Received command from {}".format(self.client_address[0]))
        command = self.data.decode('utf8')
        print(command)

        if command == 'done':
            crazy_lights(wait_time=0.1)
        elif command == 'clear':
            clear_bl()
        else:
            print(f'unknown command: {command}')


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip_addr = s.getsockname()[0]
    s.close()
    return ip_addr


@click.group()
def cli():
    pass

@cli.command()
@click.option('-b','--blink', type=float, default=1)
@click.option('-v','--verbose',help='SHOW ME WHAT YOU GOT!', count=True)
def test(blink, verbose):
    """
    CLI tool to write to busylight 
    """
    crazy_lights(verbose=verbose, wait_time=blink)

@cli.command()
@click.option('-w','--wait', type=float, default=1)
@click.option('-s','--steps', type=int, default=100)
@click.option('-v','--verbose',help='SHOW ME WHAT YOU GOT!', count=True)
def rainbow(wait, steps, verbose):
    """
    CLI tool to write to busylight 
    """
    smooth_rainbow(verbose=verbose, wait_time=wait, steps=steps)

@cli.command()
@click.option('-v','--verbose',help='SHOW ME WHAT YOU GOT!', count=True)
def clear(verbose):
    """
    CLI tool to write to busylight an "empty" buffer, removes all light/sound. 
    """
    clear_bl(verbose=verbose)

@cli.command()
@click.option('-r','--red', type=int, default=0)
@click.option('-g','--green', type=int, default=0)
@click.option('-b','--blue', type=int, default=0)
@click.option('--blink', type=int, default=0)
@click.option('-v','--verbose',help='SHOW ME WHAT YOU GOT!', count=True)
def show(red, green, blue, blink, verbose):
    """
    CLI tool to write sigle color to busylight.
    """

    bl = BusyLight(red=red, green=green, blue=blue, blink=blink, verbose=verbose)
    bl.write()

@cli.command()
@click.option('-t','--tone', default='openoffice')
@click.option('--vol',type=int, default=3)
@click.option('-v','--verbose',help='SHOW ME WHAT YOU GOT!', count=True)
def say(tone, vol, verbose):
    """
    CLI tool to write signal sounds to busylight. Tone options:

    \b
        * openoffice (default)
        * funky
        * fairytale
        * kuandotrain
        * telephonenordic
        * telephoneoriginal
        * telephonepickmeup
        * buzz
    """

    bl = BusyLight(tone=tone, vol=vol, verbose=verbose)
    bl.write()

@cli.command()
@click.argument('port', type=int)
@click.option('-v','--verbose',help='SHOW ME WHAT YOU GOT!', count=True)
def serve(port, verbose):
    """
    CLI tool to open server and listen for commands.
    """

    host = get_ip()

    # Create the server, binding to localhost on port 9999
    with socketserver.TCPServer((host, port), MyTCPHandler) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        server.serve_forever()

@cli.command()
@click.argument('host', type=str)
@click.argument('port', type=int)
@click.argument('command', type=str)
def send(host, port, command):
    """
    CLI tool to send a command to a listening bustlight server.
    """

    # Create a socket (SOCK_STREAM means a TCP socket)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # Connect to server and send data
        sock.connect((host, port))
        sock.sendall(bytes(command + "\n", "utf-8"))

if __name__ == '__main__':
    cli()
