from network import LoRa
import socket
import binascii
import struct
import time
import config
import pycom

from pysense import Pysense
from SI7006A20 import SI7006A20

# import cayenneLPP
from CayenneLPP import CayenneLPP

py = Pysense()
si = SI7006A20(py)

# turn of heartbeat
pycom.heartbeat(False)

# initialize LoRa in LORAWAN mode.
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.US915)

# create an ABP authentication params (from TTN)
dev_addr = struct.unpack(">l", binascii.unhexlify(device_address.replace(' ','')))[0]
nwk_swkey = binascii.unhexlify(NwkSKey.replace(' ',''))
app_swkey = binascii.unhexlify(AppSKey.replace(' ',''))

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
    pycom.rgbled(0x000014)
    lpp = CayenneLPP()

    # use PySense board's sensors to get temp and humidity
    lpp.add_temperature(1, si.temperature())
    lpp.add_relative_humidity(2, si.humidity())

    # send data via LoRaWAN to gateways
    s.send(bytes(lpp.get_buffer()))
    s.setblocking(False)
    # turn LED green to show idle
    pycom.rgbled(0x001400)
    time.sleep(300)
