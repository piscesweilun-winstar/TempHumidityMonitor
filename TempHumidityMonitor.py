"""
Temp/Humidity Monitor using Raspberry Pi and SmartDisplay RS485/Modbus.

Usage:
------
    python3 scriptname [-rtu] [-ascii] [-b115200] [-D/dev/ttyUSB0]

Arguments:
 * -b : baud rate
 * -D : port name

NOTE: There should be no space between the option switch and its argument.

Reference:
----------
    minimalmodbus:
        https://minimalmodbus.readthedocs.io/en/stable/index.html

    Adafruit DHT:
        https://www.freva.com/dht11-temperature-and-humidity-sensor-on-raspberry-pi/


SmartDisplay Specifications:
----------------------------
 * SlaveID
    0x7B

 * Registers
    Base idx for widget n: n * 100          for n in [0 ~ 9]
                           n * 100 + 10000  for n in [10 ~ 63]
    Offset (16-bit value each)
        0 Type
        2 PosX
        3 PosY
        4 Style
        6 Set Value (Value1)
        7 Get Value (Value2)
        8 - 57 String/Time

 * Value2 Mapping Address (16-bit)
    2000 - 2063

Widgets Setting:
---------------
    Layout for 3.5" SmartDisplay

    Widget   Type   PosX  PosY  Category     Contents
    =====   ======  ====  ====  ========  ================
      0      Text    30    16      4      Temperature: (*C)
      1     Number  130    45      0          (empty)
      2      Text    30   130      4      Humidity: (%)
      3     Number  130   160      0          (empty)
"""
import os
import sys
import time
import board
import adafruit_dht
from typing import Any, Dict, List, Optional, Tuple, Type, Union

sys.path.insert(0, "..")
import minimalmodbus

SLAVE_ADDRESS = 0x7B                # SmartDisplay ID
TIMEOUT = 0.3                       # seconds. At least 0.3 seconds required for 2400 bits/s ASCII mode.
VALUE_MAPPING_ADDRESS = 2000

DEFAULT_PORT_NAME = "/dev/ttyUSB0"  # Linux

DEFAULT_BAUDRATE = 115200           # SmartDisplay baudrate

DHT_PIN = board.D12                 # GPIO 12 / pin 32
TEMP_ADDRESS = 1 * 100 + 6
HUMIDITY_ADDRESS = 3 * 100 + 6

def show_current_values(instr: minimalmodbus.Instrument, temp, humidity) -> None:
    instr.write_register(TEMP_ADDRESS, temp)
    instr.write_register(HUMIDITY_ADDRESS, humidity)

def parse_commandline(argv: List[str]) -> Tuple[str, str, int]:
    mode = minimalmodbus.MODE_RTU
    baudrate = DEFAULT_BAUDRATE
    portname = DEFAULT_PORT_NAME

    for arg in argv:
        if arg.startswith("-ascii"):
            mode = minimalmodbus.MODE_ASCII

        elif arg.startswith("-rtu"):
            mode = minimalmodbus.MODE_RTU

        elif arg.startswith("-b"):
            if len(arg) < 3:
                print("Wrong usage of the -b option. Use -b9600")
                sys.exit()
            baudrate = int(arg[2:])

        elif arg.startswith("-D"):
            if len(arg) < 3:
                print("Wrong usage of the -D option. Use -D/dev/ttyUSB0 or -DCOM4")
                sys.exit()
            portname = arg[2:]

    return portname, mode, baudrate


def main() -> None:
    portname, mode, baudrate = parse_commandline(sys.argv)

    inst = minimalmodbus.Instrument(portname, SLAVE_ADDRESS, mode=mode)
    if inst.serial is None:
        print("Instrument.serial is None")
        return
    inst.serial.timeout = TIMEOUT
    inst.serial.baudrate = baudrate

    sensor = adafruit_dht.DHT11(DHT_PIN)
    while True:
        try:
            temp = sensor.temperature
            humidity = sensor.humidity
            show_current_values(inst, temp, humidity)
        except RuntimeError as error:
            continue
        except Exception as error:
            raise error
        time.sleep(2.0)

if __name__ == "__main__":
    main()

