from easymodbus.modbusClient import ModbusClient
from easymodbus.modbusClient import *
import time

modbusclient = ModbusClient('127.0.0.1', 502)
modbusclient.connect()

# holdingRegisters = modbusclient.read_holdingregisters(0,5)
# holdingRegisters = modbusclient.write_single_register(0,22)

for awef in range(0,20) : 
    holdingRegisters = modbusclient.write_single_register(0,awef)
    holdingRegisters = modbusclient.write_single_register(1,awef+10)
    time.sleep(1)


print(holdingRegisters)

modbusclient.close()
