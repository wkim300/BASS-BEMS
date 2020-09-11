import time
import sys
import threading
import os
import json
import copy
from pprint import pprint as pp

from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtGui import *
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import Qt


form_class = uic.loadUiType("modbus_tagmaster.ui")[0]

class WindowClass(QMainWindow, form_class) :

    def __init__(self) :
        super().__init__()
        self.setupUi(self)

        swjwidth = self.frameGeometry().width()
        swjheight = self.frameGeometry().height()

        self.input_mbaddr.setInputMask("00000")

        self.equipdata=[]
        self.addrUsed={}
        self.empty_equipdata = [
            {
            "equipinfo": {
                "eid":"",
                "name":"",
                "addr":"",
                "port":""
            },
            "tags" : [
                {
                    "tid" : "",
                    "tname" : "",
                    "fnCode" : "",
                    "mbaddr" : "",
                    "ttype" : ""
                }
            ]
            }
        ]

        twHeader = self.tree1.header()
        twHeader.setSectionResizeMode(QHeaderView.ResizeToContents)
        twHeader.setStretchLastSection(False)

        self.tree1.setContextMenuPolicy(Qt.ActionsContextMenu)

        mod_action = QAction("수정", self.tree1)
        self.tree1.addAction(mod_action)
        mod_action.triggered.connect(self.modActionFn)

        del_action = QAction("삭제", self.tree1)
        self.tree1.addAction(del_action)
        del_action.triggered.connect(self.delActionFn)

        self.tree1.itemClicked.connect(self.treeFn)
        self.add_equip.clicked.connect(self.add_equipFn)
        self.add_tag.clicked.connect(self.add_tagFn)
        self.btn_save.clicked.connect(self.btn_saveFn)
        self.btn_load.clicked.connect(self.btn_loadFn)

        self.add_tag.setEnabled(False)

    def modActionFn(self) : 
        
        try : 
            self.item_selec = self.tree1.selectedItems()[0]
            self.parentitem = self.item_selec.parent()

            uid = self.item_selec.data(1,0)
            if uid.find('-') == -1 : 
                eid = uid
                tid = None
            else : 
                eid = uid[:uid.find('-')]
                tid = uid[uid.find('-')+1:]
            
        except IndexError : 
            pass

    def delActionFn(self) : 

        ed = copy.deepcopy(self.equipdata)

        try : 
            self.item_selec = self.tree1.selectedItems()[0]
            self.parentitem = self.item_selec.parent()

            uid = self.item_selec.data(1,0)

            if uid.find('-') == -1 : # Equip을 선택하고 삭제하면 해당 Equip과 하위 TAG가 모두 삭제됨
                eid = uid
                tid = None

                for eidcnt in range(0,len(ed)) : 
                    
                    current_eid = ed[eidcnt]['equipinfo']['eid']
                    
                    if current_eid == eid : 
                        
                        del ed[eidcnt]
                        try : 
                            del self.addrUsed[current_eid]
                        except KeyError : 
                            pass
                        break
                        
            
            else : # TAG를 선택하고 삭제를 누르면 TAG를 삭제하도록 하는 부분
                eid = uid[:uid.find('-')]
                tid = uid[uid.find('-')+1:]
                
                for eidcnt in range(0,len(ed)) : 
                    
                    current_eid = ed[eidcnt]['equipinfo']['eid']
                    for tidcnt in range(0,len(ed[eidcnt]['tags'])) :
                        
                        current_tid = ed[eidcnt]['tags'][tidcnt]['tid']

                        if (current_tid == tid)&(current_eid == eid) : 
                            
                            current_mbaddr = ed[eidcnt]['tags'][tidcnt]['mbaddr']
                            current_ttype = ed[eidcnt]['tags'][tidcnt]['ttype']
                            
                            mbaddr_list_toDel = [current_mbaddr] if current_ttype[-2:] == "16" else [current_mbaddr, str(int(current_mbaddr)+1)] # 삭제되는 태그의 modbus address 정리
                            
                            del ed[eidcnt]['tags'][tidcnt] # equipment data dictionary에서 대상 tag 삭제
                            
                            # used address 리스트에서 삭제대상 modbus address 함께 삭제
                            print(mbaddr_list_toDel)
                            for mbaddr_target in mbaddr_list_toDel : 

                                self.addrUsed[current_eid].remove(mbaddr_target)

                            break

            print(self.addrUsed)
            self.equipdata = copy.deepcopy(ed)
            self.fnListSet()
            self.add_tag.setEnabled(False)
        
        except IndexError : # TreeWidget이 비어있을 때 우클릭 후 삭제 선택했을 때 아무 동작 없게 하기 위해 예외처리함
            pass


    def fnListSet(self) : 
        
        self.tree1.clear()
        ed = self.equipdata
        for equipcnt in range(0, len(ed)) : 
            
            item_parent = 'equip'+str(equipcnt)
            locals()[item_parent] = QTreeWidgetItem(self.tree1)

            equipname = ed[equipcnt]['equipinfo']['name']
            equipaddr = ed[equipcnt]['equipinfo']['addr']
            equipport = ed[equipcnt]['equipinfo']['port']
            equipid = ed[equipcnt]['equipinfo']['eid']

            locals()[item_parent].setText(0,"{0}({1} : {2})".format(equipname, equipaddr, equipport))
            locals()[item_parent].setText(1,equipid)

            locals()[item_parent].setExpanded(True)

            for tagcnt in range(0,len(ed[equipcnt]['tags'])) : 
                
                current_tag = ed[equipcnt]['tags'][tagcnt]
                item_child = 'tag_'+str(equipcnt)+'_'+str(tagcnt)

                tagid = current_tag['tid']
                tagname = current_tag['tname']
                tagfncode = current_tag['fnCode']
                tagtype = current_tag['ttype']
                tagaddr = current_tag['mbaddr']

                locals()[item_child] = QTreeWidgetItem(locals()[item_parent], [tagname,'{0}-{1}'.format(equipid, tagid), tagfncode, tagtype, tagaddr])
                locals()[item_child].setExpanded(True)



    def treeFn(self) : 
        self.add_tag.setEnabled(True)



    def add_equipFn(self) : 
        eid_list = [0]
        
        ed = copy.deepcopy(self.equipdata) # Init에서 불러온 equipdata를 deepcopy(원본 변수 수정 방지)

        for equips in range(0,len(ed)) : 
            eid_list.append(int(ed[equips]["equipinfo"]["eid"])) # Equip ID 추가를 위해 전체 EID 검사 후 리스트화
            print(int(ed[equips]["equipinfo"]["eid"]))

        new_equipid = max(eid_list)+1 # 새로 추가되는 기기의 EID = 기존 마지막 번호+1
        new_equipname = self.input_equipname.text()
        new_equipip = self.input_ip.text()
        new_equipport = self.input_port.text()

        ed.append(self.empty_equipdata[0])
        
        ed[-1]["equipinfo"]["eid"] = str(new_equipid)
        ed[-1]["equipinfo"]["name"] = new_equipname
        ed[-1]["equipinfo"]["addr"] = new_equipip
        ed[-1]["equipinfo"]["port"] = new_equipport
        ed[-1]["tags"]=[]

        self.equipdata = copy.deepcopy(ed)
        # pp(self.equipdata)
        self.fnListSet()



    def add_tagFn(self) : 
        
        self.item_selec = self.tree1.selectedItems()[0]
        self.parentitem = self.item_selec.parent()
        fncode_list = {"4" : "03", "3" : "04", "0" : "01", "1" : "02"}

        ### tree widget에서 선택한 item의 parent 잡기
        target_equip = self.item_selec.data(1,0) if self.parentitem == None else self.parentitem.data(1,0)


        for swji in range(0,len(self.equipdata)) : 
            eid = self.equipdata[swji]["equipinfo"]["eid"]
            
            if int(eid) == int(target_equip) : 
                target_listIndex = swji
                target_eid = eid
                break
        
        new_mbaddr = "{0:05d}".format(int(self.input_mbaddr.text()))
        new_ttype = self.cb_type.currentText()
        new_tname = self.input_tagname.text()
        new_fncode = fncode_list[new_mbaddr[0]]
        
        ### 새로 추가되는 TAG의 tid는 마지막 TAG의 tid에서 +1이 되도록 설정
        try : 
            new_tid = str(int(self.equipdata[target_listIndex]["tags"][-1]["tid"])+1)
        except IndexError : 
            new_tid = str(1)

        
        ### TAG TYPE에 따라 사용된 modbus address 범위를 집계하고 기존 address와 중복일 경우 추가하지 않도록 하는 부분
        if new_ttype[-2:] == "32" : 
            added_mbaddr = [new_mbaddr, str(int(new_mbaddr)+1)]
        else: 
            added_mbaddr = [new_mbaddr]

        addrDuplicated = []
        if target_eid in self.addrUsed.keys() :
            
            for addrCheck in added_mbaddr : 
                
                if addrCheck in self.addrUsed[target_eid] : 
                    addrDuplicated.append(addrCheck)
            
            
        
        
        ### 중복이 있으면 알림메세지, 없으면 태그 추가
        if len(addrDuplicated) != 0 : 
        
            informMsg = "추가하려는 MODBUS 주소가 기존 목록의 주소 범위와 중복되어\n추가할 수 없습니다." \
                + "\n\n § 추가 대상 Equip. ID : {0}".format(target_eid) \
                + "\n\n § 중복된 주소 : {0}".format(addrDuplicated[0])
            
            QMessageBox.information(self,"알림", informMsg)
        
        else : 
            
            ### equipdata dictionary에 입력받은 TAG 정보 추가        
            self.equipdata[target_listIndex]["tags"].append({"tid":new_tid, "tname":new_tname, "fnCode":new_fncode, "mbaddr":new_mbaddr, "ttype":new_ttype})
            
            ### 사용된 modbus address 집계 리스트에 현재 추가된 address를 추가함
            if target_eid in self.addrUsed.keys() : 
                self.addrUsed[target_eid] += added_mbaddr
            else : 
                self.addrUsed[target_eid] = added_mbaddr
            
            
            print(self.addrUsed)
            self.fnListSet() # tree widget display 업데이트
            self.add_tag.setEnabled(False) # TAG추가버튼은 일단 비활성화하도록



    def btn_saveFn(self) : 
        
        try : 
            file_ed_save = QFileDialog.getSaveFileName(self, "Save file", "", "JSON (*.json)")
            with open(file_ed_save[0], 'w') as myjson_new : 
                json.dump(self.equipdata, myjson_new, indent=4)
        
        except FileNotFoundError : 
            pass



    def btn_loadFn(self) : 
        
        try : 
            file_ed = QFileDialog.getOpenFileName(self, "Open file", "", "JSON (*.json)")
            
            with open(file_ed[0],'r') as myjsonfile : 
                self.equipdata = json.load(myjsonfile)

            ed = self.equipdata
            
            for equipcnt in range(0, len(ed)) : 
                current_eid = ed[equipcnt]["equipinfo"]["eid"]

                addr_used_thisEquip = []
                for tagcnt in range(0, len(ed[equipcnt]["tags"])) : 
                    current_tag = ed[equipcnt]["tags"][tagcnt]

                    if current_tag["ttype"][-2:] == "16" :
                        addr_used_thisEquip.append(current_tag["mbaddr"])
                        
                    else : 
                        addr_used_thisEquip.append(current_tag["mbaddr"])
                        addr_used_thisEquip.append(str(int(current_tag["mbaddr"])+1))
                        
                self.addrUsed[current_eid] = addr_used_thisEquip
            self.fnListSet()
            print(self.addrUsed)
        
        except : 
            pass



if __name__ == "__main__" :
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()