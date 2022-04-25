import PyQt5
from umodbus import conf
from umodbus.client import tcp

from bitstring import BitArray

# import os
import socket
import time
import sys
import threading

from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtGui import *
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QMainWindow, QAction, qApp
from PyQt5.QtCore import QThread

from Ui_modbus_hunter import Ui_Dialog as swjUI

import time
import datetime
from datetime import timedelta

import copy
import json
import csv
from pprint import pprint as pp

# curpath = os.getcwd()

# form_class = uic.loadUiType("modbus_hunter.ui")[0]

form_class = swjUI # ui 파일을 PYQT Integration 익스텐션을 써서 Compile하여 python class로 변경 후 import한 버전

# form_class = uic.loadUiType(curpath+'\\modules\\modbus_comm\\modbus_hunter\\'+'modbus_hunter.ui')[0]  # VSCODE 작업중에만 사용(vscode는 working dir 기준으로 cur path가 잡힘..)


class WindowClass(QMainWindow, form_class) :

    swjTableSignal = QtCore.pyqtSignal(int, int, QTableWidgetItem)

    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        self.initMenubar()

        self.pollFnDict = {
            "01" : tcp.read_coils,
            "02" : tcp.read_discrete_inputs,
            "03" : tcp.read_holding_registers,
            "04" : tcp.read_input_registers
        }
        
        swjwidth = self.frameGeometry().width()
        swjheight = self.frameGeometry().height()

        # self.open_json.clicked.connect(self.open_btnFn)
        self.pollbtn.clicked.connect(self.pollbtnFn)
        self.pollstopbtn.clicked.connect(self.pollstopbtnFn)
        
        self.swjTableSignal.connect(self.modbustable.setItem)
        
        self.pollbtn.setEnabled(False)
        self.pollstopbtn.setEnabled(False)
        

    def initMenubar(self) : 
        '''awefawef'''
        exitAction = QAction('Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('종료')
        exitAction.triggered.connect(qApp.quit)
        

        openAction = QAction('Open TAGs', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('TAG List 파일 불러오기')
        openAction.triggered.connect(self.open_btnFn)

        self.statusBar()

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        menuFile = menubar.addMenu('&File')
        menuFile.addAction(exitAction)
        menuFile.addAction(openAction)

    
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
                    item_ttype = QTableWidgetItem(ed[equipcnt]["tags"][tagcnt]["ttype"])

                    list_infoitems = [item_equipname, item_equipaddr, item_tagname, item_tagid, item_ttype, item_mbaddr]
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


    ##### MODBUS Polling Thread 함수 
    def thread_poll(self) : 
        fnList = {"01":"00001", "02":"10001", "03":"40001", "04":"30001"}
                
        ed = self.equipdata
        trySet = set(range(0,len(ed))) # 일단은 접속 시도 대상 리스트 trySet에 모든 Equipment를 추가

        ### Initial Socket Starts - All Equipments
        ### 여기서 일단 Tag list의 모든 Equipment에 대해 Socket통신을 열고 접속 시도
        for equipcnt in list(trySet) : 
            
            print("Initializing Socket {0}".format(equipcnt))

            equip_ip = ed[equipcnt]["equipinfo"]["addr"]
            equip_port = int(ed[equipcnt]["equipinfo"]["port"])
            socketName = 'sock' + str(equipcnt)

            # Equip list의 Equip에 대해 소켓 접속 시도
            try : 
                locals()[socketName] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                locals()[socketName].settimeout(0.5)
                locals()[socketName].connect((equip_ip, equip_port))
                locals()[socketName].settimeout(0.1)

                trySet.remove(equipcnt) # 소켓 연결 성공한 Equipment는 Try set에서 삭제

                print(locals()[socketName])
            
            except (ConnectionRefusedError, TimeoutError, socket.timeout) :
                
                locals()[socketName].close() # 접속불가 대상 소켓은 일단 close하여 winsock 점유 포트를 반납하여 낭비를 방지함
                self.statuslabel.setText('Equip {0} is dead.'.format(ed[equipcnt]["equipinfo"]["name"]))
        
        ### Polling Loop Start
        while self.swjk < 10 : 

            if self.swjk > 1 : 
                
                #### 접송종료버튼을 누르면 모든 equipment의 소켓을 close하고 polling loop를 탈출
                for equipcnt in range(0,len(ed)) : 
                    equip_ip = ed[equipcnt]["equipinfo"]["addr"]
                    equip_port = int(ed[equipcnt]["equipinfo"]["port"])
                    socketNameForClose = 'sock'+str(equipcnt)
                    
                    try : 
                        locals()[socketNameForClose].close()
                    except :
                        pass
                
                print('break ok')
                break
            
            else : 

                ### Try set에 대한 socket comm. 재시도 부분
                ### 기존에 접속되어있는 소켓에 대해서는 socket open을 중복 실행하지 않기 위함(winsock 포트 낭비 방지)
                for equipcnt in list(trySet) : 
                    
                    print("Initializing Socket {0}".format(equipcnt))

                    equip_ip = ed[equipcnt]["equipinfo"]["addr"]
                    equip_port = int(ed[equipcnt]["equipinfo"]["port"])
                    socketName = 'sock' + str(equipcnt)

                    try : 
                        locals()[socketName] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        locals()[socketName].settimeout(0.5)
                        locals()[socketName].connect((equip_ip, equip_port))
                        locals()[socketName].settimeout(0.1)
                        # locals()[socketName].settimeout(None)

                        trySet.remove(equipcnt)
                    
                    except (ConnectionRefusedError, TimeoutError, socket.timeout) :
                        
                        locals()[socketName].close()
                        trySet.add(equipcnt)
                        
                        self.statuslabel.setText('Equip {0} is dead.'.format(ed[equipcnt]["equipinfo"]["name"]))
                ### socket open 재시도부분 끝

                print('polling start')
                holdingRegisters_list=[]
                
                ### 접속되어있는 각 equipment의 socket에 대해 modbus register 조회 부분 시작
                for equipcnt in range(0,len(ed)) : 
                    
                    socketName2 = 'sock' + str(equipcnt)
                    tagsize = len(ed[equipcnt]["tags"])
                    
                    for tagcnt in range(0,tagsize) : 
                        print("\n\n--------------------")
                        current_tag_dict = ed[equipcnt]["tags"][tagcnt]
                        fncode = current_tag_dict["fnCode"]
                        mbaddr = current_tag_dict["mbaddr"]
                        ttype = current_tag_dict["ttype"]
                        registerAddr = int(mbaddr) - int(fnList[fncode])

                        regLength = 1 if ttype[-2:]=='16' else 2 # 태그 타입에 따라 modbus register 조회 길이 결정
                        regType = ttype[:-2]
                        

                        try : 
                            
                            msg_adu = self.pollFnDict[fncode](1, registerAddr, regLength) # MODBUS message ADU 생성
                            msg_response = tcp.send_message(msg_adu, locals()[socketName2]) # MODBUS ADU 전송, response PDU 저장

                            holdingRegistersHex = ["{0:04x}".format(x) for x in msg_response] # "0x0000" 형식으로 각 register의 값을 HEX로 저장
                            print(holdingRegistersHex)
                            holdingRegistersHexJoined = "0x" + (("".join(holdingRegistersHex[:])).replace("0x","")) # 조회한 HEX를 하나의 HEX로 이어붙임
                            print("Joined HEX : " + holdingRegistersHexJoined)
                            print("Reg Type : " + regType)

                            holdingRegisters = int(holdingRegistersHexJoined, 16) if regType == 'UINT' else BitArray(holdingRegistersHexJoined).int
                            # 연결된 Register값(HEX)을 INT로 변환
                            
                        except Exception : 
                            holdingRegisters = -4111 # 접속 끊긴 기기의 TAG값은 -4111로 임의 지정
                            trySet.add(equipcnt)  # 접속 끊긴 Equipment를 Try set에 추가하여 socket comm. 재시도 목록에 추가
                            
                        holdingRegisters_list.append(holdingRegisters)
                        print("Tag {0}-{1} Poll End".format(equipcnt, tagcnt))
                    
                print(holdingRegisters_list)
                

                ########## Table Item Part #####################
                items_list = []
                for registersData in holdingRegisters_list :
                    item_holdingRegisters = QTableWidgetItem()
                    item_holdingRegisters.setText(str(registersData)) 
                    items_list.append(item_holdingRegisters)
                
                for item_num in range(0,len(items_list)) :
                    self.swjTableSignal.emit(item_num, 6, items_list[item_num])
                ########## Table Item Part #####################
                
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