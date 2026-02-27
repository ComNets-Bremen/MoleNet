"""
Library for SX1262 chipset

This library controls the SX1262chipset.
"""
import utime
# SX1262 commands
_CLEAR_IRQ = const(0x02)
_CLEAR_DEV_ERRS = const(0x07)
_SET_DIO_IRQ = const(0x08)
_WRITE_REG = const(0x0D)
_WRITE_BUFFER = const(0x0E)
_GET_IRQ_STATUS = const(0x12)
_GET_RX_BUFFER_STATUS = const(0x13)
_GET_PKT_STATUS = const(0x14)
_GET_DEV_ERRS = const(0x17)
_READ_REGISTER = const(0x1D)
_READ_BUFFER = const(0x1E)
_SET_STANDBY = const(0x80)
_SET_RX = const(0x82)
_SET_TX = const(0x83)
_SET_SLEEP = const(0x84)
_SET_RF_FREQ = const(0x86)
_SET_PACKET_TYPE = const(0x8A)
_SET_MOD_PARAMS = const(0x8B)
_SET_PKT_PARAMS = const(0x8C)
_SET_TX_PARAMS = const(0x8E)
_SET_BUFFER_BASE_ADDRESS = const(0x8F)
_SET_PA_CONFIG = const(0x95)
_SET_DIO3_TXCO_CTRL = const(0x97)
_CAL_IMG = const(0x98)
_SET_DIO2_RFSWITCH = const(0x9D)
_GET_STATUS = const(0xC0)

#Errors
_ERR_CMD_TIMEOUT = const(0x06)
_ERR_CMD_PROCESSING = const(0x08)
_ERR_FAIL_EXEC_CMD = const(0x0A)

class Transceiver:
    """Transceiver class

    Here all functions regarding the transceiver are implemented
    """

    def __init__(self,spi,cs,rst,busy,dio1):
        """
        Initializes SX1262
        
        Parameters
        ----------
        spi : spi object
            Micropython SPI object for communication with SX1276
        cs : pin object
            Micropython Pin object for chip select of SX1276
        rst : pin object
            Micropython Pin object for resetting SX1276
        busy : pin object
            Micropython Pin object connected to busy
        """
        #variables
        self.spi = spi
        self.cs = cs
        self.rst = rst
        self.busy = busy
        self.dio1 = dio1
        
        #set pin states
        self.rst.on()
        self.cs.on()
        
        #reset transceiver
        self.rst.off()
        utime.sleep_ms(1)
        self.rst.on()

        #Enter Standby_RC
        self.write(bytes([_SET_STANDBY, 0x00]))
                
        #Set LoRa mode
        self.write(bytes([_SET_PACKET_TYPE, 0x01]))
        
        #self.write(bytes([_SET_DIO3_TXCO_CTRL, 0x02, 0x0, 0x02, 0x80])) #1.8 V for TXCO, delay: 640*15.625us=10ms
        self.write(bytes([_SET_DIO2_RFSWITCH, 0x01]))#Enable ANT_SW
        #_SET_REGULATOR_MODE = const(0x96)
        #self.write(bytes([_SET_REGULATOR_MODE, 0x01])) #doesnt help
        
        self.settings()
        self.write(bytes([_SET_SLEEP, 0x04]))#put to sleep mode for saving energy
        
    def settings(self, power=17, sf=7, bw=125, cr=4/5, syn_word=0x12, inv_iq=False, crc=True, exp_header=True):
        """
        Parameters
        ----------
        power : int
            Transmission power in dBm, range: -9dBm to 22dBm. Default: 17
        sf : int
            Spreading factor, range 7 to 12. Default: 7
        bw : int, float
            Bandwidth of LoRa signal in kHz. Default: 125kHz. Valid values: 7.8, 10.4, 15.6, 20.8, 31.25, 41.7, 62.5, 125, 250, 500
        cr : float
            Code rate of LoRa signal. Default: 4/5. Valid values: 4/5, 4/6, 4/7, 4/8
        syn_word : int
            LoRa sync word. One or two byte values possible, for one byte, a 4 is appended after each hex-digit. Default: 0x1424. For LoRaWAN use 0x3444
        inv_iq : bool
            Specify if I and Q should be inverted or not. Default: False
        crc : bool
            Enable CRC. Default: True
        exp_header : bool
            Explicit Header mode, if False Implicit Header mode is used.
        """
        
        self.write(bytes([_SET_STANDBY, 0x00]))
        utime.sleep_ms(1)
        
        if crc:
            self.crc = 0x01
        else:
            self.crc = 0x00
            
        if exp_header:
            self.exp_header = 0x00
        else:
            self.exp_header = 0x01
        
        #power mode
        self.write(bytes([_SET_PA_CONFIG,0x04,0x07,0x00,0x01])) #see p.79
        
        #set tx params
        if not (power >= -9 and power <= 22 and isinstance(power, int)):
            power = 17
        if power < 0:
            power = power+0x100 #2s complement
        self.write(bytes([_SET_TX_PARAMS, power, 0x04])) #ramp time 200us
                
        #define payload storage
        self.write(bytes([_SET_BUFFER_BASE_ADDRESS, 0x00, 0x00]))
        
        #Workaround PA clamping
        val = self.read(bytes([_READ_REGISTER, 0x08, 0xD8, 0x00,0x00]))[4]
        self.write(bytes([_WRITE_REG, 0x08, 0xD8, val|0x1E]))
        
        #optimize Inverted IQ
        val = self.read(bytes([_READ_REGISTER, 0x07, 0x36, 0x00, 0x00]))[4]
        #print("Current inverted IQ status (0 means inverted IQ polarity, 1 means standard IQ polarity):", (val & 0x04)>>2)
        if inv_iq:
            self.write(bytes([_WRITE_REG, 0x07, 0x36, val&0xFB])) # clear the bit: inverted IQ polarity 
            self.inv_iq = 0x01
        else:
            self.write(bytes([_WRITE_REG, 0x07, 0x36, val|0x04])) # set the bit: standard IQ polarity
            self.inv_iq = 0x00
        
        #set mod parameters
        if sf >= 7 and sf <=12 and isinstance(sf,int):
            sf = sf
        else:        
            sf = 7
        if bw in [7.8, 10.4, 15.6, 20.8, 31.25, 41.7, 62.5, 125, 250, 500]:
            if bw == 500: #improve modulation quality
                val = self.read(bytes([_READ_REGISTER, 0x08, 0x89, 0x00,0x00]))[4]
                self.write(bytes([_WRITE_REG, 0x08, 0x89, val&0xFB]))
            else:
                val = self.read(bytes([_READ_REGISTER, 0x08, 0x89, 0x00,0x00]))[4]
                self.write(bytes([_WRITE_REG, 0x08, 0x89, val|0x04]))
            t_sym = 2**sf/bw
            bw = [7.8,15.6,31.25,62.5,125,250,500,float("nan"),10.4,20.8,41.7].index(bw)
        else:
            val = self.read(bytes([_READ_REGISTER, 0x08, 0x89, 0x00,0x00]))[4]
            self.write(bytes([_WRITE_REG, 0x08, 0x89, val|0x04]))
            t_sym = 2**sf/125
            bw = 0x04 #125kHz
        if cr in [4/5, 4/6, 4/7, 4/8]:
            cr = [4/5, 4/6, 4/7, 4/8].index(cr) + 1
        else:
            cr = 0x01 #4/5
        if t_sym < 16.38: #low datarate optimization
            self.write(bytes([_SET_MOD_PARAMS, sf, bw, cr,0x00]))
        else:
            self.write(bytes([_SET_MOD_PARAMS, sf, bw, cr,0x01]))
        
        #set sync word
        if isinstance(syn_word,int):
            if syn_word <= 0xFF:
                sw = bytes([(syn_word&0xF0)+4,((syn_word&0x0F)<<4)+4]) #append 4s according to
            elif syn_word <= 0xFFFF:
                sw = int.to_bytes(syn_word,2,'big')
            else:
                sw = bytes([0x14, 0x24])
            self.write(bytes([_WRITE_REG, 0x07, 0x40]) + sw)
        else:
            self.write(bytes([_WRITE_REG, 0x07, 0x40, 0x14, 0x24]))
        self.write(bytes([_SET_SLEEP, 0x04]))#put to sleep mode for saving energy

        
    def set_freq(self, freq):
        """
        Parameters
        ----------
        freq : float, int
            Transmission frequency in MHz.
        """
        self.write(bytes([_SET_STANDBY, 0x00]))
        utime.sleep_ms(1)
        
        #calibrate
        if freq > 430 and freq < 440:
            self.write(bytes([_CAL_IMG, 0x6B,0x6F]))
        elif freq > 470 and freq < 510:
            self.write(bytes([_CAL_IMG, 0x75,0x81]))
        elif freq > 779 and freq < 787:
            self.write(bytes([_CAL_IMG, 0xC1,0xC5]))    
        elif freq > 863 and freq < 870:
            self.write(bytes([_CAL_IMG, 0xD7,0xDB]))
        elif freq > 902 and freq < 928:
            self.write(bytes([_CAL_IMG, 0xE1,0xE9]))
        else:
            raise ValueError("Invalid Frequency")
            
        #Set freq
        rf_freq = int(freq*(2**25)/32)
        self.write(bytes([_SET_RF_FREQ]) + int.to_bytes(rf_freq,4,'big')) #Datasheet p.85 (868.1*2**25)/32=910268826=0x3641999A
        utime.sleep_ms(1)
  
        
    def send(self,msg,freq=868.1, blocking=True):
        """
        Parameters
        ----------
        msg : str,bytes
            Message to be sent via LoRa.
        freq : float, int
            Transmission frequency in MHz. Default: 868.1 MHz
        blocking : bool
            Waits for TxDone flag and clears Irq if True. Default: True
        """
        if (isinstance(msg,str) or isinstance(msg,bytes)) and (isinstance(freq,float) or isinstance(freq,int)):
            self.set_freq(freq)
            
            self.write(bytes([_CLEAR_IRQ, 0x03, 0xFF])) #clear possibly remaining IRQ flags
            self.write(bytes([_CLEAR_DEV_ERRS, 0x00, 0x00]))   
            
            if len(msg) > 255:
                msg = msg[:255]
            
            if isinstance(msg,str):
                msg = msg.encode()
            
            #write payload
            self.write(bytes([_WRITE_BUFFER, 0x00]) + msg)
            utime.sleep_ms(1)
            
            #define frame format
            self.write(bytes([_SET_PKT_PARAMS, 0x00,0x08,self.exp_header,len(msg),self.crc,self.inv_iq])) #preamble length 0x00 0x08,explicit header 0x00, payload length, crc off 0x00, iq invert false 0x00
            
            #config dio
            self.write(bytes([_SET_DIO_IRQ, 0x02, 0x01, 0x02, 0x01, 0x00, 0x00, 0x00, 0x00])) #IRQ Mask, DIO1 Mask, DIO2 Mask, DIO3 Mask
            
            #transmit
            utime.sleep_ms(10)
            self.write(bytes([_SET_TX, 0x62, 0x98, 0x00])) #3.840.000 for 1 min timeout
            utime.sleep_ms(100)
            tx_err = False 
            if blocking:
                while self.dio1.value() == 0:
                    utime.sleep_us(100)
                    if self.read(bytes([_GET_STATUS,0x00]))[1]&0x0E in (_ERR_CMD_TIMEOUT,_ERR_CMD_PROCESSING,_ERR_FAIL_EXEC_CMD):
                        self.write(bytes([_SET_STANDBY, 0x00]))
                        utime.sleep_ms(1)
                        tx_err = True
                        print("TX Error")
                        ret=self.read(bytes([_GET_DEV_ERRS, 0x00, 0x00, 0x00])) 
                        err=ret[-1]
                        print("Error code " + hex(err))
                        print("RFU " + hex(ret[0])) # Reserved for Future Use (RFU?)
                        print("Status " + hex(ret[1]))
                        print("OpError(15:8) " + hex(ret[2]))
                        print("OpError(7:0) " + hex(ret[3]))
                        if err&0x20:
                            print("XOSC failed to start")
                        if err&0x40:
                            print("PLL failed to lock")
                        self.write(bytes([_CLEAR_DEV_ERRS, 0x00, 0x00]))                    
                        break
                    
                self.write(bytes([_CLEAR_IRQ, 0x02, 0x01]))
            utime.sleep_ms(1)
            self.write(bytes([_SET_SLEEP, 0x04]))#put to sleep mode for saving energy
            return not tx_err    
        
    def receive(self, freq=868.1, timeout=10):
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
        payload : bytes
            Received messageer(SX126X_REG_RTC_EVENT, rtcEvent_mv, 1)
            rtcEvent_mv[0] |= 0x02
            self.writeRegister(SX126X_REG_RTC_EVENT, rtcEvent, 1)

        snr : float
            SNR in dB
        rssi : float
            RSSI in dBm
        """
        self.write(bytes([_SET_STANDBY, 0x00]))
        utime.sleep_ms(1)
        self.write(bytes([_CLEAR_IRQ, 0x02, 0x43])) #clear possibly remaining RXDone, TXDone or Timeout flags
        self.set_freq(freq)
        #packet params
        self.write(bytes([_SET_PKT_PARAMS, 0x00, 0x08, self.exp_header, 0xFF, self.crc, self.inv_iq])) #preamble length 0x00 0x08,explicit header 0x00, max. payload length, crc off 0x00, iq invert false 0x00
        #set dio irq params
        self.write(bytes([_SET_DIO_IRQ, 0x02, 0x02, 0x02, 0x02, 0x00, 0x00, 0x00, 0x00])) #IRQ Mask, DIO1 Mask, DIO2 Mask, DIO3 Mask

        #set rx
        to_factor = 0x000000 #No timeout
        self.write(bytes([_SET_RX, 0x00, 0x00, 0x00]))
        t_rx = utime.ticks_ms()
        print("Receiving...")
        #wait for rxdone
        rx_err=False
        while self.dio1.value() == 0:
            utime.sleep_us(100)
            #print(utime.ticks_diff(utime.ticks_ms(),t_rx)/1000)
            if utime.ticks_diff(utime.ticks_ms(),t_rx)/1000 > timeout and timeout > 0:
                print("Start: " + str(t_rx) + " End: " + str(utime.ticks_ms()))
                rx_err = True
                break
            #if self.read(bytes([_GET_STATUS,0x00]))[1]&0x0E in (_ERR_CMD_TIMEOUT,_ERR_CMD_PROCESSING,_ERR_FAIL_EXEC_CMD):
            #    rx_err = True
            #    print("Error while receiving")
            #    break
        #if rx done, getirqstatus to check crc
        utime.sleep_ms(1)
        irq_status = self.read([_GET_IRQ_STATUS, 0x00, 0x00, 0x00])
        print(self.read(bytes([_GET_STATUS,0x00])))
        print("IRQ: ",irq_status)
        if not (irq_status[3] & 0x40) and not(irq_status[2] & 0x02) and not rx_err: #if crc correct and no timeout
            #GetRxBufferStatus
            buffer_status = self.read(bytes([_GET_RX_BUFFER_STATUS, 0x00, 0x00, 0x00]))
            payload_len = buffer_status[2]
            buf_start = buffer_status[3]
            #read packet
            payload = self.read(bytes([_READ_BUFFER,buf_start,0x00]) + bytes(payload_len))[3:]
            snr,rssi = self.get_meta()
        else:
            payload = None
            snr = None
            rssi = None
        
        #RX Workaround
        #self.write(bytes([_WRITE_REG, 0x09, 0x20, 0x00]))
        #val = self.read(bytes([_READ_REGISTER, 0x09, 0x44, 0x00,0x00]))[4]
        #self.write(bytes([_WRITE_REG, 0x09, 0x44, val|0x02]))
        #clear irq
        self.write(bytes([_CLEAR_IRQ, 0x02, 0x43]))
        self.write(bytes([_SET_STANDBY, 0x00]))
        utime.sleep_ms(1)
        self.write(bytes([_SET_SLEEP, 0x04]))#put to sleep mode for saving energy
        return payload, snr, rssi
        
        
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
        pkt_status = self.read(bytes([_GET_PKT_STATUS, 0x00, 0x00, 0x00, 0x00]))
        signal_power = pkt_status[2]/-2 #dBm
        snr_twos = pkt_status[3]
        if snr_twos & 0x80:
            snr_twos -= 0x100
        snr = snr_twos/4 #dB
        rssi = pkt_status[4]/-2 #dB
        return snr, signal_power
        
    def write(self,msg, retries=3):
        """
        Parameters
        ----------
        msg : bytes
            Command in bytes to be written via SPI
        retries : int
            number of retries after failed write attempt. Default: 3
        """
        for i in range(retries): #in case of error try again
            utime.sleep_ms(1)
            self.cs.off()
            utime.sleep_us(150)
            while True:
                utime.sleep_us(100)
                if self.busy.value() == 0:
                    break
            self.spi.write(msg)
            utime.sleep_ms(1)
            status = self.spi.read(1)
            utime.sleep_ms(1)
            self.cs.on()
            utime.sleep_us(600)
            if (status[0] & 0x0E) not in (_ERR_CMD_TIMEOUT,_ERR_CMD_PROCESSING,_ERR_FAIL_EXEC_CMD):
                break
            else:
                print(str(i) + ": writing failed, trying again")
        
        
    def read(self,buf, retries=3):
        """
        Parameters
        ----------
        buf : bytes
            Bytes to send while reading.
        retries : int
            number of retries after failed write attempt. Default: 3
            
        Returns
        -------
        rx_buf : bytes
            Bytes read
        """
        tx_buf = bytearray(buf)
        rx_buf = bytearray(len(tx_buf))
        self.cs.off()
        utime.sleep_us(150)
        while True:
                utime.sleep_us(100)
                if self.busy.value() == 0:
                    break
        self.spi.write_readinto(tx_buf,rx_buf)
        status = rx_buf[1]
        utime.sleep_ms(1)
        self.cs.on()
        utime.sleep_us(600)
        if (status & 0x0E) in (_ERR_CMD_TIMEOUT,_ERR_CMD_PROCESSING,_ERR_FAIL_EXEC_CMD):
            print("reading failed, buf: " + str(buf) + " rx: " + str(rx_buf))
        return bytes(rx_buf)

if __name__ == "__main__":
    from machine import SPI, Pin
    import machine
    import utime
    import random

    spi = machine.SoftSPI(baudrate=400000, sck=9, mosi=10, miso=11)
    cs = Pin(8, Pin.OUT, value=1)
    rst = Pin(12, Pin.OUT, value=1)
    busy = Pin(13, Pin.IN)
    dio1 = Pin(14, Pin.IN)

    sx1262 = Transceiver(spi, cs, rst, busy, dio1)
    sx1262.settings(power=17, sf=7, bw=125, cr=4/5, syn_word=0x12, inv_iq=False, crc=True, exp_header=True)

    sx1262.send("Hello World!")

    while True:
        print(sx1262.receive())