from network import LoRa
import machine
import socket
import binascii
import struct
import time
import config
import pycom

from pysense import Pysense
from SI7006A20 import SI7006A20
from LTR329ALS01 import LTR329ALS01
from MPL3115A2 import MPL3115A2, ALTITUDE, PRESSURE

# import cayenneLPP
from CayenneLPP import CayenneLPP

py = Pysense()
mp = MPL3115A2(py, mode=ALTITUDE) # Returns height in meters. Mode may also be set to PRESSURE, returning a value in Pascals
si = SI7006A20(py)
lt = LTR329ALS01(py)

# turn of heartbeat
pycom.heartbeat(False)

# color combos for LED
blue = 0x000010
red = 0x100000
green = 0x001000

yellow = 0x101000
liteblue = 0x001010
magenta = 0x100010

white = 0x101010

# initialize LoRa in LORAWAN mode.
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.US915)

# create an ABP authentication params (from TTN)
dev_addr = struct.unpack(">l", binascii.unhexlify(config.device_address.replace(' ','')))[0]
nwk_swkey = binascii.unhexlify(config.NwkSKey.replace(' ',''))
app_swkey = binascii.unhexlify(config.AppSKey.replace(' ',''))

# remove all the channels
for channel in range(0, 72):
    lora.remove_channel(channel)

# set all channels to the same frequency (must be before sending the OTAA join request)
for channel in range(0, 72):
    lora.add_channel(channel, frequency=config.LORA_FREQUENCY, dr_min=0, dr_max=3)

# join a network using ABP (Activation By Personalization)
lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey))

# create a LoRa socket
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

# set the LoRaWAN data rate
s.setsockopt(socket.SOL_LORA, socket.SO_DR, config.LORA_NODE_DR)

# make the socket blocking
s.setblocking(False)

while True:
    s.setblocking(True)
    # turn LED blue to show sending
    pycom.rgbled(liteblue)

    # initialize LPP format
    lpp = CayenneLPP()

    b,r = lt.light()

    # use PySense board's sensors to get temp humidity light
    lpp.add_temperature(1, si.temperature())
    lpp.add_temperature(2, mp.temperature())
    lpp.add_luminosity(3, b)
    lpp.add_luminosity(4, r)
    lpp.add_relative_humidity(5, si.humidity())

    # send data via LoRaWAN to gateways
    s.send(bytes(lpp.get_buffer()))
    s.setblocking(False)

    # turn LED green to show idle
    pycom.rgbled(red)

    # time.sleep(30)

    # deeper sleep
    machine.deepsleep(1000*30) # milliseconds
