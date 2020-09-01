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

    swjTableSignal = QtCore.pyqtSignal(int, int, QTableWidgetItem)

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
        self.pollstopbtn.clicked.connect(self.pollstopbtnFn)

        self.swjTableSignal.connect(self.modbustable.setItem)

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

            self.modbustable.setItem(table_rownum,0,item_addr)
            self.modbustable.setItem(table_rownum,1,item_modbusaddr)

            table_rownum = table_rownum +1
        
        self.swjk = 0
        threadPoll = threading.Thread(target = self.thread_poll, args=([]))
        threadPoll.start()
        self.statuslabel.setText("Now Polling")
        
    
    def thread_poll(self) : 

        startaddr = self.input_startaddr.value()
        endaddr = self.input_endaddr.value()
        
        while self.swjk < 10 : 
            
            if self.swjk > 1 : 
                print('break ok')
                break
            
            else : 
            
                print('polling start')
                
                holdingRegisters_list=[]

                for addrlist in range(startaddr, endaddr+1) : 
                    holdingRegisters = self.modbusclient.read_holdingregisters(addrlist,1)
                    holdingRegisters_list.append(holdingRegisters[0])

                print(holdingRegisters_list)
                table_poll_rownum = 0

                for registersData in holdingRegisters_list :
                    # widgetName = 'swjTableWidgetItem'+str(registersData)
                    # locals()[widgetName] = QTableWidgetItem
                    # item_holdingRegistsers = locals()[widgetName](str(registersData))
                    item_holdingRegisters = QTableWidgetItem(str(registersData))
                    print(item_holdingRegisters)
                    
                    try : 
                        self.swjTableSignal.emit(table_poll_rownum, 2, item_holdingRegisters)                       
                    except: 
                        pass
                    
                    table_poll_rownum = table_poll_rownum +0.1
                    time.sleep(0.1)
                
            time.sleep(1)
        
        

    # def emit_table(self) : 
    #     self.modbustable.setItem(self.table_poll_rownum,2,self.item_holdingRegistsers)
        

    
    def pollstopbtnFn(self) : 
        self.swjk = 2
        print(str(self.swjk))


# app = QApplication(sys.argv)
# myWindow = WindowClass()
# myWindow.show()
# app.exec_()

if __name__ == "__main__" :
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()