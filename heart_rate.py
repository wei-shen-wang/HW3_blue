from bluepy.btle import Peripheral, UUID
from bluepy.btle import Scanner, DefaultDelegate
import binascii

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)
    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            print("Discovered device",dev.addr)
        elif isNewData:
            print("Received new data from",dev.addr)

class NotifyDelegate(DefaultDelegate):
    def __init__(self, hndl):
        print("New delegate init")
        DefaultDelegate.__init__(self)
        self.hndl = hndl
    def handleNotification(self, cHandle, data):
        print("Handling Notification")

class IndicationDelegate(DefaultDelegate):
    def __init__(self, hndl):
        print("New delegate init")
        DefaultDelegate.__init__(self)
        self.hndl = hndl
    def handleNotification(self, cHandle, data):
        print("Handling indication")

def enable_notify(ch):
    setup_data = b"\x01\x00"
    cccd = ch.getHandle() + 1
    res = dev.writeCharacteristic(cccd, setup_data, withResponse=True)
    print(res)

def enable_indication(ch):
    setup_data = b"\x02\x00"
    cccd = ch.getHandle() + 1
    res = dev.writeCharacteristic(cccd, setup_data, withResponse=True)
    print(res)

scanner = Scanner().withDelegate(ScanDelegate())
devices = scanner.scan(30.0)
n = 0
number = 0
for dev in devices:
    print("%d:Device %s(%s), RSSI=%d dB" % (n,dev.addr,dev.addrType,dev.rssi))
    for(adtype, desc, value) in dev.getScanData():
        print(" %s = %s"%(desc,value))
        if desc == "Complete Local Name" and value == "Heart Rate":
            number = n
            break
    n+=1

print("Connecting...")
dev = Peripheral(devices[number].addr,'random')

print("Services...")
for svc in dev.services:
    print(str(svc))

try:
    HRService = dev.getServiceByUUID(UUID(0x123C))
    BP_char = HRService.getCharacteristics()
    for i in range(len(BP_char)):
        print(BP_char[i].propertiesToString())

    # NOTIFY
    Control = BP_char[2]

    dev.withDelegate(NotifyDelegate(Control.getHandle()))
    enable_notify(Control)

    while True:
        if dev.waitForNotifications(1.0):
            print("Notification received")
            break

    # INDICATE
    indicate = BP_char[3]
    dev.withDelegate(IndicationDelegate(indicate.getHandle()))
    enable_indication(indicate)

    while True:
        if dev.waitForNotifications(1.0):
            print("Indication received")
            break

    # READ
    Measure = BP_char[1]
    if Measure.supportsRead():
        feat = Measure.read()
        print("Measure feature : " + feat)

    # WRITE 
    write_char = BP_char[0]
    if "WRITE" in write_char.propertiesToString():
        res = write_char.write(b"@@", withResponse=True)
        print(res)
        
finally:
    dev.disconnect()
