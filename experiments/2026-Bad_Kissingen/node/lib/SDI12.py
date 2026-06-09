from machine import UART, Pin
import utime

class SDI12:
    def __init__(self, rx, tx, marking, rx_enable, tx_enable):
        print("Init SDI12")
        
        #define pins, start with TX activated
        self.RX = Pin(18)
        self.TX = Pin(17)
        self.SDI_Marking = Pin(37, Pin.OUT, value=1)
        self.RX_Enable = Pin(36, Pin.OUT, value=0)
        self.TX_Enable = Pin(35, Pin.OUT, value=0)

        #define UART
        self.sdi12 = UART(1, baudrate=1200, bits=7, parity=0, stop=1, tx=self.TX, rx=self.RX, invert=UART.INV_RX)
        utime.sleep_ms(500)
        self.sdi12.read() # Discard the boot message from sensor
        
    def measure(self,addr):
        self.command("{}M!".format(addr))
        utime.sleep_ms(50)
        response = self.command("{}D0!".format(addr)) # Data collect command for sensor address 1
        return response
        
    def write(self, msg):
        print("writing")
        #enter write mode
        self.RX_Enable.value(0)
        self.TX_Enable.value(0)
        #12ms break
        self.SDI_Marking.value(0)
        utime.sleep_ms(13)
        #8.33ms marking
        self.SDI_Marking.value(1)
        utime.sleep_ms(9)
        #transmit command
        self.sdi12.write(msg)
        self.sdi12.flush() #wait for all data to be sent, if errors occur, try utime.sleep_ms(50)
        
    def read(self):
        print("reading")
        #enter reading mode
        self.RX_Enable.value(1)
        self.TX_Enable.value(1)
        utime.sleep_ms(500)
        #read
        response = self.sdi12.read()
        print(response)
        return response

    def command(self, command = "1M!"): # By default, take measurements command for sensor address 1
        #send SDI12 command
        self.write(command)
        #read sensor answer
        return self.read()
