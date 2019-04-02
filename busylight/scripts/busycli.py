#!/usr/bin/env python
#
#
import os
import click
import logging
import logging.config
import socket
import socketserver
import busylight

# Setup logger
logger = logging.getLogger(__name__)
_log_filename = os.path.expanduser('~/busylight.log')

def configure_logging(verbose, logfn):
    """
    Function to handle setting up logger
    """

    # TODO: just use the integer value and pass that to the config.
    if verbose == 0:
        log_lvl = 'ERROR'
    elif verbose == 1:
        log_lvl = 'WARNING'
    elif verbose == 2:
        log_lvl = 'INFO'
    elif verbose > 2:
        log_lvl = 'DEBUG'

    # Just keep it here for simplicity
    config = {
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'}},
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
                'level': log_lvl,
                'stream': 'ext://sys.stdout'},
            'file_handler': {
                'backupCount': 20,
                'class': 'logging.handlers.RotatingFileHandler',
                'encoding': 'utf8',
                'filename': logfn,
                'formatter': 'simple',
                'level': 'DEBUG',
                'maxBytes': 10485760}},
        'loggers': {
            'blobcli': {
                'handlers': ['console', 'file_handler'],
                'level': log_lvl,
                'propagate': False}},
        'root': {
            'handlers': ['console', 'file_handler'],
            'level': log_lvl},
        'version': 1}

    logging.config.dictConfig(config)
    logging.captureWarnings(True)


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
        logger.info("Received command from {}".format(self.client_address[0]))
        command = self.data.decode('utf8')
        logger.info(command)

        if command == 'done':
            busylight.crazy_lights(wait_time=0.1)
        elif command == 'clear':
            busylight.clear_bl()
        else:
            logger.warn(f'unknown command: {command}')


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip_addr = s.getsockname()[0]
    s.close()
    return ip_addr


@click.group()
@click.option('-l','--logfn', help='log file path', default=_log_filename,
              type=click.Path())
@click.option('-v', '--verbose', help="SHOW ME WHAT YOU GOT!", count=True)
def cli(logfn, verbose):
    configure_logging(verbose, logfn)

@cli.command()
@click.option('-b','--blink', type=float, default=1)
def test(blink):
    """
    CLI tool to write to busylight 
    """
    busylight.crazy_lights(wait_time=blink)

@cli.command()
@click.option('-w','--wait', type=float, default=1)
@click.option('-s','--steps', type=int, default=100)
def rainbow(wait, steps):
    """
    CLI tool to write to busylight 
    """
    busylight.smooth_rainbow(wait_time=wait, steps=steps)

@cli.command()
def clear():
    """
    CLI tool to write to busylight an "empty" buffer, removes all light/sound. 
    """
    busylight.clear_bl()

@cli.command()
@click.option('-r','--red', type=int, default=0)
@click.option('-g','--green', type=int, default=0)
@click.option('-b','--blue', type=int, default=0)
@click.option('--blink', type=int, default=0)
def show(red, green, blue, blink):
    """
    CLI tool to write sigle color to busylight.
    """

    bl = busylight.BusyLight(red=red, green=green, blue=blue, blink=blink)
    bl.write()

@cli.command()
@click.option('-t','--tone', default='openoffice')
@click.option('--vol',type=int, default=3)
def say(tone, vol):
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

    bl = busylight.BusyLight(tone=tone, vol=vol)
    bl.write()

@cli.command()
@click.argument('port', type=int)
def serve(port):
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