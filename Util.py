#-*- coding: utf-8 -*-

import re
from PyQt4 import QtGui,QtCore
from PaoZhao_UI  import Ui_MainWindow

ex_str ='122aa8993122aa8993122aai993'
Find_Patt = re.compile(r'aa.',re.DOTALL)
rcv_dat = Find_Patt.findall(ex_str)
if rcv_dat == []:
    print "ddddsads"
else:
    print rcv_dat[-1]

#print rcv_dat

def checkData(data, _type):
    if data == '':
        return False, u"数据不能为空"

    errch, msg = None, "success"
    if _type == "hex":
        data = ''.join(data.split())
        if len(data) % 2 != 0:
            errch, msg = True, u"HEX模式下，数据长度必须为偶数"
        else:
            for ch in data.upper():
                if not ('0' <= ch <= '9' or 'A' <= ch <= 'F'):
                    errch, msg = ch, u"数据中含有非法的HEX字符"
                    break

    return not errch, msg