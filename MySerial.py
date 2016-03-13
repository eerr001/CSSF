#-*- coding: utf-8 -*-

# 为串口创建独立线程，并对pySerial进行二次封装
import threading
from time import strftime, gmtime, sleep
from PyQt4.QtCore import QObject, SIGNAL
from serial import Serial


class MySerial(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.qtobj = QObject()
        self.serial = None
        self.__terminate = False
        self.__stop_rcv = False
        self.Send_CNT = 0x0000
        self.send_save_file = 'send_file%s.txt' % strftime('%y%m%d%H%M%S',gmtime())

    def getPortList(self):
        PortList_str = []
        for Port_id in range(6):
            try:
                iserial = Serial(Port_id)
                PortList_str.append(iserial.portstr)
                iserial.close()
            except Exception, msg:
                #print "erro",id,msg.message.decode("gbk")
                continue

        return PortList_str

    def open(self, port_str):
        try:
            self.serial = Serial(port_str, 115200)
            self.serial.timeout = 0.1
            self.serial.flushInput()
            self.serial.flushOutput()
            self.__stop_rcv = False
        except Exception, msg:
            return False, msg.message.decode("gbk")

        return True, "success"

    def resetArduino(self):
        self.serial.setDTR(0)
        sleep(0.1)
        self.serial.setDTR(1)

    def terminate(self):
        self.__terminate = True

    def send(self, data):
        #if self.Send_CNT == 0xFFFF:
        #    self.Send_CNT = 0x0000
        #else:
        #    self.Send_CNT += 1

        #data[12] = self.Send_CNT & 0xFF
        #data[13] = (self.Send_CNT >> 8) & 0xFF
        #data[13] = sum(data[2:-1]) & 0xFF
        #self.serial.write(''.join([chr(x) for x in data]))
        self.serial.write(data)
        # with open(self.send_save_file,'a+') as send_cmd_save:
        #     send_cmd_save.write(data)
        #     send_cmd_save.write('\n')

    def __recv(self):
        data, iquit = None, False
        while 1:
            if self.__terminate:
                break
            if self.__stop_rcv :
                break
            data = self.serial.read(1)
            if data == '':
                continue
            while not self.__stop_rcv:
                n = self.serial.inWaiting()
                if n > 0:
                    data = "%s%s" % (data, self.serial.read(n))
                    sleep(0.002)
                else:
                    iquit = True
                    break
            if iquit:
                break
        return data

    def close(self):
        if self.serial.isOpen():
            self.serial.close()

    def stop_rcv(self):
        self.__stop_rcv = True


    def run(self):
        while 1:

            if self.__terminate:
                break
            if not self.__stop_rcv :
                data = self.__recv()
                self.qtobj.emit(SIGNAL("NewData"), data)
                sleep(0.02)
            else:
                sleep(1)
                print u"停止接收",self.__stop_rcv

        self.serial.close()