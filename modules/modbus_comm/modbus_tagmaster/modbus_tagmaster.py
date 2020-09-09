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

        # with open('myjson_new.json','r') as myjsonfile : 
        #     self.equipdata = json.load(myjsonfile)
        self.equipdata=[]
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
                    "mbaddr" : ""
                }
            ]
            }
        ]

        # self.fnListSet()

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

            print("Equip id : {0} // Tag id : {1}".format(eid, tid))
        except IndexError : 
            pass

    def delActionFn(self) : 
        
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

            print("Equip id : {0} // Tag id : {1}".format(eid, tid))
        except IndexError : 
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
                tagaddr = current_tag['mbaddr']

                locals()[item_child] = QTreeWidgetItem(locals()[item_parent], [tagname,'{0}-{1}'.format(equipid, tagid), tagfncode, tagaddr])
                locals()[item_child].setExpanded(True)


        
        

    def treeFn(self) : 
        
        # self.item_selec = self.tree1.selectedItems()[0]
        # self.parentitem = self.item_selec.parent()

        # # print(self.parentitem.data(0,0))
        # uid = self.item_selec.data(1,0)
        # if uid.find('-') == -1 : 
        #     eid = uid
        #     tid = None
        # else : 
        #     eid = uid[:uid.find('-')]
        #     tid = uid[uid.find('-')+1:]

        # # print(self.item_selec.data(1,0))
        # print("Equip id : {0} // Tag id : {1}".format(eid, tid))

        self.add_tag.setEnabled(True)





    def add_equipFn(self) : 
        eid_list = [0]
        
        ed = copy.deepcopy(self.equipdata) # Init에서 불러온 equipdata를 deepcopy(원본 변수 수정 방지)

        for equips in range(0,len(ed)) : 
            # ed = self.equipdata
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

        if self.parentitem == None : 
            # print(self.item_selec.data(1,0))
            target_equip = self.item_selec.data(1,0)
        else : 
            # print(self.parentitem.data(1,0))
            target_equip = self.parentitem.data(1,0)

        # print(target_equip)
        # print(type(target_equip))

        for swji in range(0,len(self.equipdata)) : 
            
            eid = self.equipdata[swji]["equipinfo"]["eid"]
            # print(eid)
            
            if int(eid) == int(target_equip) : 
                target_listIndex = swji
                break
        
        try : 
            new_tid = str(int(self.equipdata[target_listIndex]["tags"][-1]["tid"])+1)
        except IndexError : 
            new_tid = str(1)
        
        new_tname = self.input_tagname.text()
        new_mbaddr = self.input_mbaddr.text()
        fncode_list = {"4" : "03", "3" : "04", "0" : "01", "1" : "02"}
        new_fncode = fncode_list[new_mbaddr[0]]
        self.equipdata[target_listIndex]["tags"].append({"tid":new_tid, "tname":new_tname, "fnCode":new_fncode, "mbaddr":new_mbaddr})

        # pp(self.equipdata)
        
        self.fnListSet()
        self.add_tag.setEnabled(False)






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

            self.fnListSet()
        except : 
            pass





if __name__ == "__main__" :
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()