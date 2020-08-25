from easymodbus.modbusClient import ModbusClient
from easymodbus.modbusClient import *

modbusclient = ModbusClient('127.0.0.1', 502)
modbusclient.connect()

# holdingRegisters = modbusclient.read_holdingregisters(0,5)
holdingRegisters = modbusclient.write_single_register(0,6721)


print(holdingRegisters)

modbusclient.close()
