from cryptolib import aes
from cmac import CMAC
import struct
import uos
import utime
import math
import random

class LoRaWAN:
    def __init__(self, transceiver, freqs):
        """
        Initializes LoRaWAN
                
        Parameters
        ----------
        transceiver : transceiver object
            Object of a transceiver chip. Should contain settings, send and receive functions.
        freqs : list of floats
            List containing standard frequencies of a region
        """
        self.freqs = freqs
        self.transceiver = transceiver
        self.joined = False
        if ".config.cfg" in uos.listdir():
            print("Read config")
            self.read_cfg()
            if self.NwkSKey != bytes(16):
                self.joined = True
        else:
            self.NwkSKey = bytes(16)
            self.AppSKey = bytes(16)
            self.DevAddr = bytes(4)
            self.DevEui = bytes(8)
            self.FCntUp = 0
            self.FCntDown = 0
            self.devNonce = 0
            self.rx1_delay = 5
            self.rx1_dr_offset = 0
            self.save_cfg()
            
    def setup_abp(self, NwkSKey, AppSKey, DevAddr, DevEui):
        """
        Sets the device up for ABP, saves the keys and resets counters
                
        Parameters
        ----------
        NwkSKey : list of 16 bytes
            NwkSKey, big endian
        AppSKey : list of 16 bytes
            AppSKey, big endian
        DevAddr : list of 4 bytes
            DevAddr, big endian
        DevEui : list of 8 bytes
            DevEui, big endian
        """
        # Reset counters and update keys if keys are new
        if not(self.NwkSKey == bytes(NwkSKey) and
               self.AppSKey == bytes(AppSKey) and
               self.DevAddr == bytes(DevAddr) and
               self.DevEui == bytes(DevEui)):
            self.NwkSKey = bytes(NwkSKey)
            self.AppSKey = bytes(AppSKey)
            self.DevAddr = bytes(DevAddr)
            self.DevEui = bytes(DevEui)
            self.FCntUp = 0
            self.FCntDown = 0
            self.joined = True 
            self.save_cfg()
            
    def reset(self):
        """
        Resets stored keys and counters except devNonce.
        """
        self.NwkSKey = bytes(16)
        self.AppSKey = bytes(16)
        self.DevAddr = bytes(4)
        self.DevEui = bytes(8)
        self.FCntUp = 0
        self.FCntDown = 0
        self.joined = False 
        self.save_cfg()

    def join_otaa(self, AppKey, joinEUI, devEUI, retries=3, sf=7):
        """
        Sets the device up for ABP, saves the keys and resets counters
                
        Parameters
        ----------
        AppKey : list of 16 bytes
            AppKey, big endian
        joinEUI : list of 8 bytes
            joinEUI, big endian, can be all zeros
        devEui : list of 8 bytes
            DevEui, big endian
        retries : int
            Number of join attempts.
        sf : int
            Spreading Factor for join attempts can be between 7 and 12. Default: 7
        """
        AppKey = bytes(AppKey)
        joinEUI = bytes(joinEUI)
        self.DevEui = bytes(devEUI)
        
        tries = 0
        while tries < retries:
            tries+=1
            self.transceiver.settings(power=20, sf=sf, bw=125, cr=4/5, syn_word=0x34, inv_iq=False, crc=True, exp_header=True)
            mhdr = bytes([0x00]) #join request(000), rfu (000), major(00)
            join_request = bytes(reversed(joinEUI)) + bytes(reversed(self.DevEui)) + int.to_bytes(self.devNonce,2,'little')
            self.devNonce += 1
            self.save_cfg()
            cmac = CMAC()
            mic = cmac.aes_cmac(AppKey, mhdr + join_request)[0:4]
            msg=mhdr+join_request+mic
            print(msg)
            rx_msg = self.transceiver.send(msg, self.freqs[0])
            self.transceiver.settings(power=20, sf=sf, bw=125, cr=4/5, syn_word=0x34, inv_iq=True, crc=False, exp_header=True)
            rx_msg,snr,rssi=self.transceiver.receive(self.freqs[0],timeout=self.rx1_delay+3) #see regional parameters
            
            print(rx_msg)
            if rx_msg != None:
                rx_mhdr = rx_msg[0]
            else:
                rx_mhdr = None
            if not rx_mhdr == 0x20: #check if received message is join accept
                utime.sleep(5)
                continue 
            join_accept_payload, mic_correct = self.decrypt_join_accept(AppKey, rx_msg[1:])
            print("JA PAyload",join_accept_payload)
            if not mic_correct:
                self.joined = False
                continue
            else:
                return
            
    def send(self,msg,power=20,sf=7,ack=False, adr=False, fport=b'\x01'):
        """
        Sends message to LoRaWAN network if joined.
                
        Parameters
        ----------
        msg : str or bytes
            Payload to be transmitted via LoRaWAN
        power : int
            Tx power. Default: 20
        ack : bool
            Request ack. Default: False
        adr : bool
            RFU. Default: False
        fport : byte
            LoRaWAN FPort. Default: 0x01
        """
        if self.joined:
            self.transceiver.settings(power=power, sf=sf, bw=125, cr=4/5, syn_word=0x34, inv_iq=False, crc=True, exp_header=True)
            utime.sleep_ms(1)
            #mac header
            mhdr = 0x00
            if ack:
                mhdr |= 0x80
            else:
                mhdr |= 0x40
            mhdr = bytes([mhdr])
                
            #mac payload
            #frame header
            devaddr = bytes(reversed(self.DevAddr))
            
            adr_bit = 0x80 if adr else 0x00
            adr_ack_req = 0x00
            ack_bit = 0x00
            classb = 0x00 #currently no class b support planed
            fopts_len = 0x00 #currently only payload, no mac        
            fctrl = bytes([adr_bit + adr_ack_req + ack_bit+ classb + fopts_len]) #ADR,adrackreq,ack,classb,foptslen
            
            fcnt = int.to_bytes(self.FCntUp,2,'little')
            
            fopts = bytes([])
            
            fhdr = devaddr + fctrl + fcnt + fopts
            
            #frame payload
            if isinstance(msg,str):
                frmpayload = self.encrypt_payload(msg.encode())
            elif isinstance(msg, bytes):
                frmpayload = self.encrypt_payload(msg)
            print("Encrypted Payload: {}".format(frmpayload))
            
            msg_no_mic = mhdr + fhdr + fport + frmpayload
            
            B0 = bytes([0x49, 0x00, 0x00, 0x00, 0x00, 0x00]) + devaddr + int.to_bytes(self.FCntUp, 4, 'little') + bytes([0x00, len(msg_no_mic)])
            print(B0)
            
            cmac = CMAC()
            mic = cmac.aes_cmac(self.NwkSKey, B0 + msg_no_mic)[0:4]
            
            payload = msg_no_mic + mic
            print("Payload: " + str(payload))
            freq=random.choice(self.freqs)
            self.transceiver.send(payload, freq)
            self.FCntUp+=1
            self.save_cfg()
            
            #rx1
            ack_received = False
            rx_msg = None
            if ack:
                sf_rx = sf+self.rx1_dr_offset if sf+self.rx1_dr_offset < 12 else 12
                self.transceiver.settings(power=20, sf=sf_rx, bw=125, cr=4/5, syn_word=0x34, inv_iq=True, crc=False, exp_header=True)
                rx_msg,snr,rssi=self.transceiver.receive(freq,timeout=self.rx1_delay+3) #see regional parameters
                if rx_msg != None:
                    if len(rx_msg) > 5 and bytes(reversed(rxmsg[1:5])) == self.DevAddr: #verify DevAddr
                        if rx_msg[5] & 0x20:
                            ack_received = True
            else:
                utime.sleep(self.rx1_delay+1)#wait until rx2 window is over
            return rx_msg, ack_received
        else:
            raise Exception("Not joined to a Network")
            return  None
    
    def encrypt_payload(self, msg):
        """
        Encrypts payload for LoRaWAN transmission
        
        Parameters
        ----------
        msg : bytes
            Payload to be encrypted
        """
        #Enter Keys in Big Endian, this code changes and transmitts as little endian
        K = self.AppSKey
        k = math.ceil(len(msg)/16)
        DevAddr = bytes(reversed(self.DevAddr))
        cipher = aes(K,1)

        S = b''
        for i in range(k):
            A = bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00]) + DevAddr + int.to_bytes(self.FCntUp, 4, 'little') + bytes([0x00]) + int.to_bytes(i+1, 1, 'little')
            S_tmp = cipher.encrypt(A)
            S+=S_tmp
        
        msg_pad = msg + bytes(k*16-len(msg)) #Append 0x00 so that padded length is multiple of 16
        #xor:
        msg_crypt = bytes([a ^ b for a, b in zip(msg_pad, S)])
        return msg_crypt[:len(msg)]
    
    def decrypt_join_accept(self, AppKey, join_accept):
        """
        Decrypts join accept message, calculates keys.
        If CF List of Type 0 is received, it saves the frequencies.
        
        Parameters
        ----------
        AppKey : list of bytes
            AppKey used to decrypt join accept message.
        join_accept : bytes
            Join accept message to be decrypted
        """
        K = AppKey
        cipher = aes(K,1)
        if len(join_accept)%16:
            join_accept = join_accept + bytes(16-len(join_accept)%16)
        print(join_accept)
        join_accept_dec = cipher.encrypt(join_accept) #message is encrypted, such that it can be decrypted by encrypt function
        mic_rx = join_accept_dec[-4:]
        cmac = CMAC()
        mic_calc= cmac.aes_cmac(AppKey, bytes([0x20])+join_accept_dec[:-4])[:4]
        print("RX MIC: {}, Calc MIC: {}".format(mic_rx,mic_calc))
        c = join_accept_dec[:6] + int.to_bytes(self.devNonce-1, 2, 'little') #-1 due to increment after transmission
        c_pad = c + bytes(15-len(c))
        self.NwkSKey = cipher.encrypt(bytes([0x01]) + c_pad)
        self.AppSKey = cipher.encrypt(bytes([0x02]) + c_pad)
        self.DevAddr = bytes(reversed(bytes(join_accept_dec[6:10])))
        self.rx1_delay = join_accept_dec[11]
        self.rx1_dr_offset = (join_accept_dec[10] & 0x70) >> 4
        print("NwkSKey: {}, AppSKey: {}, DevAddr: {}, rx1_delay: {}, DR_RX1: {}".format(self.NwkSKey,self.AppSKey,self.DevAddr,self.rx1_delay, self.rx1_dr_offset))
        
        cf_list = join_accept_dec[12:-4] #safe as freqs
        if len(cf_list) == 16:
            if cf_list[-1] == 0:
                for i in range(0,15,3):
                    print(cf_list[i:i+3])
                    tmp = int.from_bytes(cf_list[i:i+3],'little')
                    try:
                        tmp = tmp/10000
                        self.freqs.append(tmp)
                    except Exception as exc:
                        print(exc)
        if mic_calc == mic_rx:
            self.save_cfg()
            self.joined = True
            
            self.send("Joined")
        
        return join_accept_dec, mic_calc == mic_rx

    def save_cfg(self):
        """
        Saves configuration in hidden file ".config.cfg"
        """
        f_bytes = bytes(0)
        for freq in self.freqs:
            f_bytes += struct.pack('f',freq)
        cfg = struct.pack(">iiiii16s16s4s8s",self.FCntUp, self.FCntDown, self.devNonce, self.rx1_delay, self.rx1_dr_offset, self.NwkSKey, self.AppSKey, self.DevAddr, self.DevEui)
        with open(".config.cfg","wb") as f:
            f.write(cfg+f_bytes)
        
    def read_cfg(self):
        """
        Reads configuration from hidden file ".config.cfg"
        """
        with open(".config.cfg","rb") as f:
            cfg = f.read()
        self.FCntUp, self.FCntDown, self.devNonce, self.rx1_delay, self.rx1_dr_offset, self.NwkSKey, self.AppSKey, self.DevAddr, self.DevEui = struct.unpack(">iiiii16s16s4s8s",cfg)
        tmp_freqs = cfg[64:]
        for i in range(0,len(tmp_freqs),4):
            freq = struct.unpack('f',tmp_freqs[i:i+4])[0]
            if not freq in self.freqs:
                self.freqs.append(freq)

if __name__ == "__main__":
    import ubinascii
    from config_ABP import *
    from machine import SPI, Pin
    import machine
    import utime
    import EU868
    
    from SX1262 import Transceiver
    spi = machine.SoftSPI(baudrate=400000, sck=9, mosi=10, miso=11)
    cs = Pin(8, Pin.OUT, value=1)
    rst = Pin(12, Pin.OUT, value=1)
    busy = Pin(13, Pin.IN)
    dio1 = Pin(14, Pin.IN)

    sx1262 = Transceiver(spi, cs, rst, busy, dio1)
    
    lw = LoRaWAN(sx1262, EU868.FREQS)
    lw.setup_abp(NwkSKey, AppSKey, DevAddr, DevEUI)
    
    if not lw.joined:
        print(lw.join_otaa(1))
    else:
        print(lw.send("Hello World"))
    