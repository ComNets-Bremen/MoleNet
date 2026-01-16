"""
Library for SX1276 chipset

This library controls the SX1276 chipset. If your project uses another chipset, please add the according library.
pep8 drüber laufen lassen
"""
import utime

# SX1276 registers
_REG_FIFO = const(0x00)
_REG_OP_MODE = const(0x01)
_REG_FR_MSB = const(0x06)
_REG_FR_MID = const(0x07)
_REG_FR_LSB = const(0x08)
_REG_PA_CONFIG = const(0x09)
_REG_FIFO_ADDR_PTR = const(0x0D)
_REG_FIFO_RX_CURRENT_ADDR = const(0x10)
_REG_IRQ_FLAGS = const(0x12)
_REG_RX_NB_BYTES = const(0x13)
_REG_PKT_SNR = const(0x19)
_REG_PKT_RSSI = const(0x1A)
_REG_MODEM_CONFIG1 = const(0x1D)
_REG_MODEM_CONFIG2 = const(0x1E)
_REG_PAYLOAD_LENGHT = const(0x22)
_REG_MODEM_CONFIG3 = const(0x26)
_REG_INVERT_IQ = const(0x33)
_REG_SYNC_WORD = const(0x39)
_REG_INVERT_IQ2 = const(0x3B)
_REG_DIO_MAPPING_1 = const(0x40)
_REG_VERSION = const(0x42)
_REG_PA_DAC = const(0x4D)

# modes
_MODE_SLEEP = const(0x00)
_MODE_STDBY = const(0x01)
_MODE_FSTX = const(0x02)
_MODE_TX = const(0x03)
_MODE_FSRX = const(0x04)
_MODE_RXCONT = const(0x05)
_MODE_RX_SINGLE = const(0x06)
_MODE_LORA = const(0x80)

class Transceiver:
    """Transceiver class

    Here all functions regarding the transceiver are implemented
    """

    def __init__(self,spi,cs,rst,dio0):
        """
        Initializes SX1276
        
        Parameters
        ----------
        spi : spi object
            Micropython SPI object for communication with SX1276
        cs : pin object
            Micropython Pin object for chip select of SX1276
        rst : pin object
            Micropython Pin object for resetting SX1276
        dio0 : pin object
            Micropython Pin object connected to dio0
        """
        #variables
        self.spi = spi
        self.cs = cs
        self.rst = rst
        self.dio0 = dio0
        
        #set pin states
        self.rst.on()
        self.cs.on()
        
        #reset transceiver
        self.rst.off()
        utime.sleep(1)
        self.rst.on()

        #check communication
        if self.read(_REG_VERSION,2)[1] == 18:
            print("SPI working, version check passed")
            
        #initialize modem
        self.write(_REG_OP_MODE,_MODE_LORA) #LoRa sleep mode
        self.settings()

        
    def settings(self, power=17, sf=7, bw=125, cr=4/5, syn_word=0x12, inv_iq=False, crc=False, exp_header=True):
        """
        Parameters
        ----------
        power : int
            Transmission power in dBm, range: 2dBm to 17dBm and 20dBm
        sf : int
            Spreading factor, range 7 to 12
        bw : int, float
            Bandwidth of LoRa signal in kHz. Default: 125kHz. Valid values: 7.8, 10.4, 15.6, 20.8, 31.25, 41.7, 62.5, 125, 250, 500
        cr : float
            Code rate of LoRa signal. Default: 4/5. Valid values: 4/5, 4/6, 4/7, 4/8
        syn_word : int
            LoRa sync word. Default: 0x12. For LoRaWAN use 0x34
        inv_iq : bool
            Specify if I and Q should be inverted or not. Default: False
        crc : bool
            Enable CRC. Default: True
        exp_header : bool
            Explicit Header mode, if False Implicit Header mode is used.
        """
        #power mode
        if power < 2:
            power = 2
        if power <= 17:
            pval = 0xF0|(power-2)
            self.write(_REG_PA_CONFIG, pval) 
        elif power == 20:
            self.write(_REG_PA_CONFIG, 0xFF)
            self.write(_REG_PA_DAC, 0x87)
        
        #spreading factor sf7 by default
        if crc:
            self.crc = 0x04
        else:
            self.crc = 0x00
        if sf >= 7 and sf <= 12:
            self.write(_REG_MODEM_CONFIG2, (sf*0x10)|self.crc)
        if (bw == 125 and sf >=11 and sf <= 12) or (bw == 250 and sf == 12): #enable LDRO according to LoRaWAN regional parameters   
            self.write(_REG_MODEM_CONFIG3, 0x0C)
        
        #coding rate 4/5 by default, bw 125khz by default
        bandwidths = {
            7.8: 0x0,    # 7.8 kHz
            10.4: 0x10,   # 10.4 kHz
            15.6: 0x20,   # 15.6 kHz
            20.8: 0x30,   # 20.8 kHz
            31.25: 0x40,  # 31.25 kHz
            41.7: 0x50,   # 41.7 kHz
            62.5: 0x60,   # 62.5 kHz
            125: 0x70,    # 125 kHz
            250: 0x80,    # 250 kHz
            500: 0x90     # 500 kHz
        }
        code_rates = {
            4/5: 0x02,
            4/6: 0x04,
            4/7: 0x06,
            4/8: 0x08
        }
        try:
            bw_reg = bandwidths[bw]
        except KeyError:
            print("Invalid bandwidth, using 125kHz")
            bw_reg = 0x70
        try:
            cr_reg = code_rates[cr]
        except KeyError:
            print("Invalid code rate, using 4/5")
            cr_reg = 0x02
        if exp_header:
            self.exp_header = 0x00
        else:
            self.exp_header = 0x01
        self.write(_REG_MODEM_CONFIG1, bw_reg | cr_reg | self.exp_header)

              
        #sync word
        self.write(_REG_SYNC_WORD, syn_word) #LoRaWAN sync word is 0x34
        
        #invert IQ
        #For some reason RX or TX has to be inverted in order for the message to be received properly
        if inv_iq:
            self.write(_REG_INVERT_IQ, 0x66)#invert RX
            self.write(_REG_INVERT_IQ2, 0x19)
        else:
            self.write(_REG_INVERT_IQ, 0x27)#invert TX
            self.write(_REG_INVERT_IQ2, 0x1D)
        
        
    def set_freq(self, freq):
        """
        Parameters
        ----------
        freq : float, int
            Transmission frequency in MHz.
        """
        if freq < 137:
            raise ValueError("Invalid Frequency")
        
        freq = int(freq*(2**19)/32) #freq and osc both MHz
        lsb = freq & 0xFF
        mid = freq>>8 & 0xFF
        msb = freq>>16 & 0xFF
        #write freq to regs
        self.write(_REG_FR_MSB, msb)
        self.write(_REG_FR_MID, mid)
        self.write(_REG_FR_LSB, lsb)
        
    def send(self,msg,freq=868.1):
        """
        Parameters
        ----------
        msg : str
            Message to be sent via LoRa
        freq : float, int
            Transmission frequency in MHz. Default: 868.1 MHz
        """
        if (isinstance(msg,str) or isinstance(msg,bytes)) and (isinstance(freq,float) or isinstance(freq,int)):
            self.set_freq(freq)
            
            #set dio0 to TX done
            self.write(_REG_DIO_MAPPING_1, 0x40)
            
            #sleep -> standby
            self.write(_REG_OP_MODE, _MODE_LORA|_MODE_STDBY)
            #payload length
            self.write(_REG_PAYLOAD_LENGHT, len(msg))
            
            self.write(_REG_FIFO_ADDR_PTR, 0x80) #0x80 default base address of tx fifo data
            self.write(_REG_FIFO,msg) 
            #standby -> tx sends msg
            self.write(_REG_OP_MODE, _MODE_LORA|_MODE_TX)
            #wait for irq tx done
            tx_time = utime.ticks_us()
            while not self.dio0.value(): #dio0 always 1
                utime.sleep_ms(10)
            tx_duration = utime.ticks_us() - tx_time
            print(tx_duration)
            #changes automatically back to standby
            # -> sleep
            self.write(_REG_OP_MODE, _MODE_LORA|_MODE_SLEEP)
            print("transmission succesful")
        else:
            print("Wrong datatype: msg has to be str or bytes, freq has to be int or float")
            
    
    def receive(self, freq=868.1, timeout=0):
        """
        Receive LoRa message
        
        Parameters
        ----------
        freq : float
            Frequency to listen for new messages in MHz. Default: 868.1 MHz
        timeout : int
            Timeout in seconds, put 0 to disable timeout. Default: 0
            
        Returns
        -----
        msg : bytes
            Received message
        snr : float
            SNR in dB
        rssi : float
            RSSI in dBm
        """
        self.set_freq(freq)
        
        #set dio0 to RX done
        self.write(_REG_DIO_MAPPING_1, 0x00)
        
        #enter standby mode
        self.write(_REG_OP_MODE, _MODE_LORA|_MODE_STDBY)
        
        #Set FifoAddrPtr
        self.write(_REG_FIFO_ADDR_PTR, 0x00) #0x00 default base address of rx fifo data
        
        #enter rx continuous mode
        self.write(_REG_OP_MODE, _MODE_LORA|_MODE_RXCONT)
        
       #wait for irq
        print("waiting for IRQ")
        t_start = utime.ticks_ms()
        timed_out = False
        while not self.dio0.value(): #dio0 always 1
            if timeout:
                if utime.ticks_diff(utime.ticks_ms(),t_start) >= timeout*1000:
                    timed_out = True
                    break
            utime.sleep_ms(10)
        
        # if no_crc error: read data
        irq_flag = self.read(_REG_IRQ_FLAGS,2)[1]
        if not irq_flag & 0x20 and not timed_out:
            #get number of received bytes from RegRxNbBytes
            num_bytes = int(self.read(_REG_RX_NB_BYTES,2)[1])
            print("Num Bytes: {}".format(num_bytes))
            
            #get meta
            snr, rssi = self.get_meta()
            print("SNR:{}, RSSI:{}".format(snr,rssi))
            
            #read fifo
            curr_addr = self.read(_REG_FIFO_RX_CURRENT_ADDR,2)[1]
            print("current address: {}".format(curr_addr))
            self.write(_REG_FIFO_ADDR_PTR, curr_addr)
            
            #read message from FiFo
            msg = self.read(_REG_FIFO, num_bytes+1)[1:]
        else:
            msg = None
            snr = None
            rssi = None            
            
        #enter sleep mode
        self.write(_REG_OP_MODE, _MODE_LORA|_MODE_SLEEP)
        
        return msg, snr, rssi
    
    def get_meta(self):
        """
        Get metadata of last received message.
            
        Returns
        -----
        snr : float
            SNR in dB
        signal_power : float
            RSSI in dBm
        """
        #only returns proper val after start
        port_const = -157 #-164 for LF port
        snr = self.read(_REG_PKT_SNR, 2)[1] 
        if snr & 0x80: #if number is negative, substract 256
            snr = snr - 0x100
        snr_db=snr/4 #for dB, divide by 4
        packet_rssi = self.read(_REG_PKT_RSSI, 2)[1]
        if snr_db < 0:
            packet_rssi_db = port_const + packet_rssi + snr_db #datasheet p.87
        else:
            packet_rssi_db = port_const + packet_rssi
        return snr_db, packet_rssi_db
    
        
    def write(self,adress,msg):
        """
        Parameters
        ----------
        adress : int
            Register adress.
        msg : str, bytes, int
            Message to be written into register.
        """
        self.cs.off()
        utime.sleep_ms(5)
        if isinstance(msg,int):
            self.spi.write(bytes([adress|0x80,msg]))
        elif isinstance(msg, str):
            self.spi.write(bytes([adress|0x80]) + msg.encode())
        elif isinstance(msg, bytes):
            self.spi.write(bytes([adress|0x80]) + msg)
        utime.sleep_ms(5)
        self.cs.on()
        
    def read(self,adress,length):
        """
        Parameters
        ----------
        adress : int
            Register adress.
        length : int
            Number of bytes to read including adress.
        
        Returns
        -------
        rx_buf : bytes
            Bytes read
        """
        self.cs.off()
        utime.sleep_ms(5)
        val = self.spi.read(length,adress)
        utime.sleep_ms(5)
        self.cs.on()
        return val

if __name__ == "__main__":
    #from SX1276 import Transceiver
    from machine import SPI, Pin
    import machine
    import utime
    
    spi = machine.SoftSPI(baudrate=400000, sck=14, mosi=47, miso=21)
    cs = Pin(48, Pin.OUT, value=1)
    rst = Pin(45, Pin.OUT, value=1)
    dio0 = Pin(46, Pin.IN)

    sx1276 = Transceiver(spi, cs, rst, dio0)
    sx1276.settings(power=20, sf=7, bw=125, cr=4/5, syn_word=0x12, inv_iq=False, crc=False, exp_header=True)
    sx1276.send('Hello World',868.1)
    while True:
        print(sx1276.receive(868.1, timeout=5))
        utime.sleep_ms(10)
