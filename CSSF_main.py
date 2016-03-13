#coding=UTF-8
#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      lizhanhang
#
# Created:     22-03-2013
# Copyright:   (c) lizhanhang 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import re
import struct

from Queue import Queue
from PyQt4 import QtGui, QtCore
from time import strftime, gmtime, sleep

from MySerial import MySerial
from CSSF_UI import Ui_MainWindow
from TouchPad import FOV_view
class Widget(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.scene = FOV_view()
        self.scene.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)


        self.view = self.ui.graphicsView_axis
        self.view.setScene(self.scene)
        # self.view.setCacheMode(QtGui.QGraphicsView.CacheBackground)
        self.view.setViewportUpdateMode(QtGui.QGraphicsView.BoundingRectViewportUpdate)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.view.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        self.view.setResizeAnchor(QtGui.QGraphicsView.AnchorViewCenter)
        self.view.scale(1, 1)
        self.view.setMinimumSize(200, 200)



        # 通过程序初始化界面信息
        self.serial = MySerial()
        self.cmd = 'ilde'
        self.timer_cnt = 0
        self.dat_queue = Queue(-1)
        self.ui.comboBox_PortNO.addItems(self.serial.getPortList())
        self.flags = {'__isopen__': False, '__Erase_OK__': False}
        self.send_check_ok = True
        self.cmd_dat = [0x55,0xAA,
                        0x0C,
                        0x77,        # 工作状态
                        0x00, 0x00,  # 方位角 L+H 0.01度
                        0x00, 0x00,  # 俯仰角 L+H
                        0x00, 0x00,  # 方位搜索角/方位跟踪偏差 L+H 0.01度/秒
                        0x01, 0x00,  # 俯仰位搜索角/俯仰跟踪偏差 L+H 0.01度/秒
                        0x00,
                        0x00,
                        0x00,        # 帧计数
                        0x84,        # 校验和

        ]
        self.cur_set = ""
        self.do_cnt = 0
        self.ordinal = 0

        self.sec = 0

        #self.dat_file = open(r's_dat_%s.dat' % strftime('%y%m%d%H%M%S',gmtime()),'w+')
        self.exetimes = QtCore.QElapsedTimer()
        self.exetimes.start()
        self.OverTimer = QtCore.QTimer()
        self.connect(self.OverTimer, QtCore.SIGNAL("timeout()"), self.RCV_customer)

        self.DoTimer = QtCore.QTimer()

        # 信号 槽连接
        # 可以直接使用函数 on_help_bt.clicked() 不用上面的connect
        self.ui.Position_bt.clicked.connect(self.Position)
        self.ui.Search_bt.clicked.connect(self.Search)
        self.ui.Bias_bt.clicked.connect(self.Bias)

        # 错误码 dict
        self.Error_codes = {
            "R000E301BB" :  "No Target detected",
            "R000E302" :  "Target detected inside Range Gate",
            "R000E320" :  "DSP error (no APD check)",
            "R000E321" :  "APD error",
            "R000E322" :  "Critical low battery alarm"
        }

        # 测试选择框
        # self.ui.Md1_3s_cb.toggled.connect(self.continuous_measure)

        self.ui.help_bt.clicked.connect(self.HelpAbout)
        # self.connect(self.ui.comboBox_PortNO, QtCore.SIGNAL("currentIndexChanged(int)"), self.reopen)
        self.connect(self.serial.qtobj, QtCore.SIGNAL("NewData"), self.RCV_product)
        # self.connect(self.thread, QtCore.SIGNAL("RCV_unpack()"), self.RCV_unpack)
        PortList = self.serial.getPortList()
        if PortList != []:
            if "COM4" in PortList:
                self.ui.comboBox_PortNO.setCurrentIndex(PortList.index("COM4"))
            self.reopen()
        else:
            QtGui.QMessageBox.warning(self, u"温馨提示", u"没有发现串口！\n你用的是笔记本吧！")
        #print u"初始化完成"
        self.serial.start()

    def reopen(self):
        Port_str = '%s' % self.ui.comboBox_PortNO.currentText()
        if self.flags["__isopen__"] == True :
            self.serial.stop_rcv()
            sleep(0.02)
            self.serial.close()
            self.flags["__isopen__"] = False

        ret, msg = self.serial.open(Port_str)
        if ret:
            self.ui.statusbar.showMessage(u">> %s打开成功" % Port_str)
            self.flags["__isopen__"] = True
        else:
            self.ui.statusbar.showMessage(u"%s打开失败" % Port_str)
            self.flags["__isopen__"] = False
            QtGui.QMessageBox.critical(self, "Error", u"串口打开失败，系统提示：\n%s" % msg)

    def cmd_send(self):
        self.azimuth_angle_set = self.ui.lineEdit_azimuth_angle.text().toDouble()[0]
        self.pitch_angle_set = self.ui.lineEdit_pitch_angle.text().toDouble()[0]
        azimuth_velocity_set = self.ui.lineEdit_azimuth_velocity.text().toDouble()[0]
        pitch_velocity_set = self.ui.lineEdit_pitch_velocity.text().toDouble()[0]
        (self.cmd_dat[4], self.cmd_dat[5]) = struct.unpack('BB', struct.pack('h', self.azimuth_angle_set * 100))
        (self.cmd_dat[6], self.cmd_dat[7]) = struct.unpack('BB', struct.pack('h', self.pitch_angle_set * 100))
        (self.cmd_dat[8], self.cmd_dat[9]) = struct.unpack('BB', struct.pack('h', azimuth_velocity_set * 100))
        (self.cmd_dat[10], self.cmd_dat[11]) = struct.unpack('BB', struct.pack('h', pitch_velocity_set * 100))

        self.serial.send(self.cmd_dat)
        send_string = ''.join([("%02X" % dat) for dat in self.cmd_dat])
        self.ui.statusbar.showMessage(u"%s" % send_string)
        self.cmd_dat[3:8] = [0]*5

    def Position(self):
        # 伺服系统定位
        self.cmd_dat[3] = 0x11
        self.cmd = "Position"
        self.cmd_send()

    def Search(self):
        # 伺服系统搜索
        print self.scene.centerNode.x(),self.scene.centerNode.y()
        print self.scene.FOV_box.x(),self.scene.FOV_box.y()
        self.cmd_dat[3] = 0x33
        self.cmd = "Search"
        self.cmd_send()

    def Bias(self):
        # 伺服系统误差控制
        self.cmd_dat[3] = 0x77
        self.cmd = "Bias"
        self.cmd_send()

    def stop(self):
        #  停止在当前位置
        self.cmd_dat[3] = 0x00
        self.serial.send(self.cmd_dat)
        send_string = ''.join([("%02X" %dat) for dat in self.cmd_dat ])
        self.ui.statusbar.showMessage(u"%s" %send_string)
        sleep(0.02)
        self.cmd = 'ilde'

    def continuous_measure(self):
        if self.ui.Md1_3s_cb.isChecked():
            self.connect(self.DoTimer, QtCore.SIGNAL("timeout()"), self.Position)
            self.DoTimer.start(2000)
        else:
            self.disconnect(self.DoTimer, QtCore.SIGNAL("timeout()"), self.Position)
        if self.ui.Mq_1s_cb.isChecked():
            self.connect(self.DoTimer, QtCore.SIGNAL("timeout()"), self.Search)
            self.DoTimer.start(1000)
        else:
            self.disconnect(self.DoTimer, QtCore.SIGNAL("timeout()"), self.Search)
        if self.ui.stop_cb.isChecked():
            self.DoTimer.stop()
            self.disconnect(self.DoTimer, QtCore.SIGNAL("timeout()"), self.Position)
            self.disconnect(self.DoTimer, QtCore.SIGNAL("timeout()"), self.Search)

    def get_soft_ver(self):
        # >Iv1<CR>  SW-versions and module type in hex format
        # >Ir<CR>   The module responds with the current range gate settings
        self.serial.send("zhima")
        sleep(0.2)


    def RCV_product(self, data):
        # 独立的线程运行,GUI刷新需要单独控制，
        # 只负责读取数据,存入队列
        self.dat_queue.put(data)
        print "Time%s:%s" % (self.exetimes.elapsed(),data.replace('\r','_'))
        #self.sec +=1
        #print self.sec
        #self.ui.statusbar.showMessage(u" 计数器 %s"%self.sec)

    def RCV_customer(self):
        # 读取队列,对数据进行解析
       
        rawdat = ''
        while self.dat_queue.qsize() > 0:
            rawdat = rawdat + self.dat_queue.get()
        self.dat_file.write(rawdat)

        Find_Patt = re.compile(r"\x55\xAA\x0C.{13}", re.DOTALL)
        rcv_dat_list = Find_Patt.findall(rawdat)
        if rcv_dat_list == []:
            return
        else:
            rcv_dat = rcv_dat_list[-1]
        s_string = ''  
        for rcv_dat in rcv_dat_list:
            self.ordinal = self.ordinal + 1
            azimuth_angle_get =  (struct.unpack('h',rcv_dat[4:6])[0]*0.01)
            pitch_angle_get = (struct.unpack('h',rcv_dat[7:9])[0]*0.01)
            azimuth_velocity_get =  (struct.unpack('h',rcv_dat[10:12])[0]*0.01)
            pitch_velocity_get = (struct.unpack('h',rcv_dat[13:15])[0]*0.01)
            s_string = s_string + "%s,%s,%s,%s,%s\n"  % (   self.ordinal,
                                                            azimuth_angle_get,
                                                            pitch_angle_get,
                                                            azimuth_velocity_get,
                                                            pitch_velocity_get,) 

        # GUI show
        self.ui.label_azimuth_angle_show.setText(u"方位角度:%4s" % azimuth_angle_get)
        self.ui.label_pitch_angle_show.setText(u"俯仰角度:%4s" %  pitch_angle_get)
        self.ui.label_azimuth_velocity_show.setText(u"方位速度:%4s" %  azimuth_velocity_get)
        self.ui.label_pitch_velocity_show.setText(u"俯仰速度:%4s" %  pitch_velocity_get)
        self.ui.label_counter.setText(u"帧计数:%s" %  int(ord(rcv_dat[-1])))

        if self.current_state == "ilde":
            if not self.s_file.closed:
                self.s_file.close()

        # 新动作开始，生成文件，写文件的头
        if self.cmd != 'idle' and self.current_state == 'idle':
            self.current_state = self.cmd
            self.s_file = open(r'%s_%s.txt' % (self.cmd, strftime('%y%m%d%H%M%S',gmtime()),'w+'))
            self.ordinal = 0
            FormHeading = "%s,%s,%s,%s,%s\n"  % ( "ordinal",
                                                  "azimuth_angle_get",
                                                  "pitch_angle_get",
                                                  "azimuth_velocity_get",
                                                  "pitch_velocity_get",)

            self.s_file.write(FormHeading)


        # 在定位到限制角度时控制伺服进入ilde状态
        if (self.current_state == "Position" and  abs(azimuth_angle_get - self.azimuth_angle_set)<0.02
                                             and  abs(pitch_angle_get- self.pitch_angle_set)<0.02):

            self.stop()
            sleep(0.02)
            self.current_state = "ilde"
        # 在定位到限制角度时控制伺服进入ilde状态
        if (     (self.current_state == "Search" or self.current_state == "Search")
            and  (   abs(azimuth_angle_get - self.azimuth_angle_max)<0.02
                  or abs(pitch_angle_get- self.pitch_angle_max)<0.02)):

            self.stop()
            sleep(0.02)
            self.current_state = "ilde"


        if self.current_state != "ilde":
            self.s_file.write(s_string)

    def closeEvent(self, event):
        # 程序退出的时候自动执行
        self.serial.terminate()
        self.current_state = "ilde"
        sleep(1)
        self.DoTimer.stop()
        self.OverTimer.stop()

    def HelpAbout(self):
        QtGui.QMessageBox.about(self, u"伺服控制组合性能测试程序",
                                u"""<b>伺服控制组合性能测试程序</b>
                                <p>Copyright &copy; 2015 北京无线电测量研究所
                                <p>该程序用伺服系统定位，搜索，跟踪控制测试。
                                <p> """)

if __name__ == '__main__':
    import sys

    app = QtGui.QApplication(sys.argv)
    widget = Widget()
    widget.show()
    sys.exit(app.exec_())