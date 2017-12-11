# Busylight

Python command line tool to interact with the  Kuando Busylight. This is a work in progress and real rough... so use at your own risk!

Drawing a lot of inspirtion from these sources:
  * [cython-hidapi](https://github.com/trezor/cython-hidapi/blob/master/try.py)
  * [js-busylight](https://github.com/porsager/busylight)
  * BusyLigt [Specs](https://github.com/porsager/busylight/files/273865/Busylight.API.rev.2.2.-.22052015.pdf)

#Setup

Needed to get the produt and vendor ID. Easist way to grab this was to `lsusb` before and after plugging in the busylight:
  * Vendor: 27bb
  * Product: 3bcd
  * ModelName: BusyLight UC Omega


## Non-Root Access

Need to add a udev rule:

```bash
echo "SUBSYSTEM==\"usb\", ATTRS{idVendor}==\"27bb\", ATTRS{idProduct}==\"3bcd\", GROUP=\"$(whoami)\", OWNER=\"$(whoami)\", MODE=\"0664\"" | sudo tee -a /etc/udev/rules.d/30-busylight.rules
```

## Dependencies

Need to install some things and setup an environment:

```bash
sudo apt install libusb-1.0-0-dev libudev-dev
conda env -f environment.yml
source activate busylight-env
```

# Writing to HID

Mimicking the methodology [here](https://github.com/porsager/busylight/blob/master/lib/busylight.js) buffer is constructed like:

  1. Init as `[0,16,0,0,0,0,0,0,128]`
  2. Add fifty zeros `[0]*50`
  3. Append this to end: `[255, 255, 255, 255, 6, 147]`

Buffer positions:
  * red   : 3
  * green : 4
  * blue  : 5
  * sound : 8

Color Values
  * Red: 0-255
  * Green: 0-255
  * Blue: 0-255

Sound Values:
  * OpenOffice        : 136
  * Quiet             : 144
  * Funky             : 152
  * FairyTale         : 160
  * KuandoTrain       : 168
  * TelephoneNordic   : 176
  * TelephoneOriginal : 184
  * TelephonePickMeUp : 192
  * Buzz              : 216

Volume is controlled by adding `1` to each tone: 0=MUTE, 7=MAX

The last two entries in the buffer are a checksum on the buffer:

```python
checksum = sum(self.buffer[0:63])
self.buffer[63] = (checksum >> 8) & 0xffff
self.buffer[64] = checksum % 256
```
