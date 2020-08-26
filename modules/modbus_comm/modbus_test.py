from easymodbus.modbusClient import ModbusClient
from easymodbus.modbusClient import *

import time
import sys
import threading

from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtGui import *
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMessageBox

import time
import datetime
from datetime import timedelta

import urllib
from urllib.request import urlopen
from urllib.parse import urlencode, unquote, quote_plus

import copy
import json
import csv

form_class = uic.loadUiType("C:\\Users\\ECODA\\Desktop\\dhwtest\\pyapitest\\BASS-BEMS\\modules\\modbus_comm\\modbus_test.ui")[0]


class WindowClass(QMainWindow, form_class) :
    def __init__(self) :
        super().__init__()
        self.setupUi(self)

        swjwidth = self.frameGeometry().width()
        swjheight = self.frameGeometry().height()

        self.input_startaddr.valueChanged.connect(self.input_startaddrFn)
        self.input_endaddr.valueChanged.connect(self.input_endaddrFn)

        self.connectbtn.clicked.connect(self.connectbtnFn)
        self.disconnectbtn.clicked.connect(self.disconnectbtnFn)
        self.pollbtn.clicked.connect(self.pollbtnFn)

    def input_startaddrFn(self) : 
        self.addr_start_label.setText(str(self.input_startaddr.value()+40001))
        self.input_endaddr.setRange(self.input_startaddr.value(),9999)
    
    def input_endaddrFn(self) : 
        self.addr_end_label.setText(str(self.input_endaddr.value()+40001))

    def connectbtnFn(self) : 
        ipaddress = self.input_ip.text()
        portnum = self.input_port.value()
        self.modbusclient = ModbusClient(ipaddress, portnum)
        self.modbusclient.connect()
        self.statuslabel.setText(ipaddress + ":" + str(portnum) + " Modbus TCP Connected")
    
    def disconnectbtnFn(self) : 
        '''awefawef'''
        self.modbusclient.close()
        self.statuslabel.setText("Disonnected")

    def pollbtnFn(self) : 
        '''awefawfe'''
        
        startaddr = self.input_startaddr.value()
        endaddr = self.input_endaddr.value()

        self.modbustable.setRowCount(endaddr-startaddr+1)

        table_rownum = 0
        for addrlist in range(startaddr, endaddr+1) : 
            item_addr = QTableWidgetItem(str(addrlist))
            item_modbusaddr = QTableWidgetItem(str(addrlist+40001))

            holdingRegisters = self.modbusclient.read_holdingregisters(addrlist,1)

            item_holdingRegistsers = QTableWidgetItem(str(holdingRegisters[0]))

            self.modbustable.setItem(table_rownum,0,item_addr)
            self.modbustable.setItem(table_rownum,1,item_modbusaddr)
            self.modbustable.setItem(table_rownum,2,item_holdingRegistsers)
            table_rownum = table_rownum +1




if __name__ == "__main__" :
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()