from easymodbus.modbusClient import ModbusClient
from easymodbus.modbusClient import *

from umodbus import conf
from umodbus.client import tcp

import socket
import time
import sys
import threading

from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtGui import *
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QThread

import time
import datetime
from datetime import timedelta

import urllib
from urllib.request import urlopen
from urllib.parse import urlencode, unquote, quote_plus

import copy
import json
import csv
from pprint import pprint as pp



# try : 
#     form_class = uic.loadUiType("modbus_hunter.ui")[0]
# except : 
#     form_class = uic.loadUiType("modbus_hunter.ui")[0]

form_class = uic.loadUiType("modbus_hunter.ui")[0]


class WindowClass(QMainWindow, form_class) :

    swjTableSignal = QtCore.pyqtSignal(int, int, QTableWidgetItem)

    def __init__(self) :
        super().__init__()
        self.setupUi(self)

        swjwidth = self.frameGeometry().width()
        swjheight = self.frameGeometry().height()

        self.fncodeList = ['00001', '10001', '40001', '30001']
        self.fncode = '00001'
        
        self.open_json.clicked.connect(self.open_btnFn)
        self.pollbtn.clicked.connect(self.pollbtnFn)
        self.pollstopbtn.clicked.connect(self.pollstopbtnFn)
        
        self.swjTableSignal.connect(self.modbustable.setItem)
        
        self.pollbtn.setEnabled(False)
        self.pollstopbtn.setEnabled(False)

    
    def open_btnFn(self) : 
        
        try : 
            json_fid = QFileDialog.getOpenFileName(self, "Select JSON", "", "JSON (*.JSON)")
            with open(json_fid[0], "r") as myjson : 
                self.equipdata = json.load(myjson)

            rowCounts = sum(list([len(self.equipdata[swji]["tags"]) for swji in range(0,len(self.equipdata))]))
            self.modbustable.setRowCount(rowCounts+1)

            ed = self.equipdata
            table_rownum = 0
            for equipcnt in range(0,len(self.equipdata)) : 
                '''awefawef'''
                tagSize = len(self.equipdata[equipcnt]["tags"])
                for tagcnt in range(0,tagSize) : 
                    '''awefawef'''
                    item_equipname = QTableWidgetItem(ed[equipcnt]["equipinfo"]["name"])
                    item_equipaddr = QTableWidgetItem(ed[equipcnt]["equipinfo"]["addr"])
                    item_tagname = QTableWidgetItem(ed[equipcnt]["tags"][tagcnt]["tname"])
                    item_tagid = QTableWidgetItem(str(ed[equipcnt]["tags"][tagcnt]["tid"]))
                    item_mbaddr = QTableWidgetItem(ed[equipcnt]["tags"][tagcnt]["mbaddr"])

                    list_infoitems = [item_equipname, item_equipaddr, item_tagname, item_tagid, item_mbaddr]
                    for table_info_cols in range(0,len(list_infoitems)) : 
                        '''awefawef'''
                        self.modbustable.setItem(table_rownum, table_info_cols, list_infoitems[table_info_cols])
                    table_rownum = table_rownum+1
            
            # pp(self.equipdata)
            self.pollbtn.setEnabled(True)

        except FileNotFoundError : 
            pass

    def pollbtnFn(self) : 
        self.swjk = 0
        threadPoll = threading.Thread(target = self.thread_poll, args=([]))
        threadPoll.start()

        self.statuslabel.setText('Now Polling..')

        self.pollstopbtn.setEnabled(True)
        self.pollbtn.setEnabled(False)
        
    def thread_poll(self) : 
        

        fnList = {"01":"00001", "02":"10001", "03":"40001", "04":"30001"}
        
        pollFnDict = {
            "01" : tcp.read_coils,
            "02" : tcp.read_discrete_inputs,
            "03" : tcp.read_holding_registers,
            "04" : tcp.read_input_registers
        }
        
        ed = self.equipdata
        while self.swjk < 10 : 
             
            if self.swjk > 1 : 
                print('break ok')
                break
            
            else : 
            
                print('polling start')
                
                holdingRegisters_list=[]

                for equipcnt in range(0,len(ed)) : 
                    
                    tagsize = len(ed[equipcnt]["tags"])
                    equip_ip = ed[equipcnt]["equipinfo"]["addr"]
                    equip_port = int(ed[equipcnt]["equipinfo"]["port"])
                    
                    # self.modbusclient = ModbusClient(equip_ip, equip_port)
                    
                    try : 
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.connect((equip_ip, equip_port))    
                    except socket.timeout : 
                        pass

                    for tagcnt in range(0,tagsize) : 
                        '''awefawef'''
                        current_tag_dict = ed[equipcnt]["tags"][tagcnt]
                        fncode = current_tag_dict["fnCode"]
                        mbaddr = current_tag_dict["mbaddr"]
                        registerAddr = int(mbaddr) - int(fnList[fncode])

                        # holdingRegisters = pollFnDict[fncode](registerAddr,1)

                        try : 
                            msg_adu = pollFnDict[fncode](1,registerAddr,1)
                            holdingRegisters = tcp.send_message(msg_adu, sock)
                            
                            
                        except Exception : 
                            holdingRegisters = [-1]
                        

                        
                        holdingRegisters_list.append(holdingRegisters[0])
                        print("Tag {0}-{1} Poll".format(equipcnt, tagcnt))
                    
                    try : 
                        sock.close()
                    except : 
                        pass

                print(holdingRegisters_list)
                
                items_list = []
                for registersData in holdingRegisters_list :
                    item_holdingRegisters = QTableWidgetItem()
                    item_holdingRegisters.setText(str(registersData)) 
                    items_list.append(item_holdingRegisters)
                    

                for item_num in range(0,len(items_list)) :
                    self.swjTableSignal.emit(item_num, 5, items_list[item_num])

            time.sleep(1)
        
    def pollstopbtnFn(self) : 
        self.swjk = 2
        self.pollstopbtn.setEnabled(False)
        self.pollbtn.setEnabled(True)
        self.statuslabel.setText('Polling End')
        
if __name__ == "__main__" :
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()