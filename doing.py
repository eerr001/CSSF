from serial import Serial
from MySerial import MySerial

serial = MySerial()
print serial.getPortList()

PortList_str = []
for id in range(6):
    try:
        self.serial = Serial(id)
        print id,self.serial.portstr
        PortList_str.append(self.serial.portstr)
        self.serial.close()
    except Exception, msg:

        print "erro",id,msg.message.decode("gbk")

print PortList_str