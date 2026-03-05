/*******************************************************************************
   Copyright (c) 2015 Thomas Telkamp and Matthijs Kooijman

   Permission is hereby granted, free of charge, to anyone
   obtaining a copy of this document and accompanying files,
   to do whatever they want with them without any restriction,
   including, but not limited to, copying, modification and redistribution.
   NO WARRANTY OF ANY KIND IS PROVIDED.

   This example sends a valid LoRaWAN packet with payload "Hello,
   world!", using frequency and encryption settings matching those of
   the The Things Network.

   This uses OTAA (Over-the-air activation), where where a DevEUI and
   application key is configured, which are used in an over-the-air
   activation procedure where a DevAddr and session keys are
   assigned/generated for use with all further communication.

   Note: LoRaWAN per sub-band duty-cycle limitation is enforced (1% in
   g1, 0.1% in g2), but not the TTN fair usage policy (which is probably
   violated by this sketch when left running for longer)!

   To use this sketch, first register your application and device with
   the things network, to set or generate an AppEUI, DevEUI and AppKey.
   Multiple devices can use the same AppEUI, but each device has its own
   DevEUI and AppKey.

   Do not forget to define the radio type correctly in config.h.

 *******************************************************************************/

#include <lmic.h>
#include <hal/hal.h>
#include <SPI.h>

#include <RFM69.h>         //get it here: https://www.github.com/lowpowerlab/rfm69
#include <RFM69registers.h>
#include <RFM69_ATC.h>     //get it here: https://www.github.com/lowpowerlab/rfm69
#include <SPIFlash.h>      //get it here: https://www.github.com/lowpowerlab/spiflash

//////////////////Global vars LoRa/////////////////////////////////
bool isJoined = false;

// This EUI must be in little-endian format, so least-significant-byte
// first. When copying an EUI from ttnctl output, this means to reverse
// the bytes. For TTN issued EUIs the last bytes should be 0xD5, 0xB3,
// 0x70.
static const u1_t PROGMEM APPEUI[8] = { 0x0A, 0xA2, 0x01, 0xD0, 0x7E, 0xD5, 0xB3, 0x70 };
void os_getArtEui (u1_t* buf) {
  memcpy_P(buf, APPEUI, 8);
}

// This should also be in little endian format, see above.
static const u1_t PROGMEM DEVEUI[8] = { 0xD4, 0x5A, 0x8D, 0xB9, 0x4A, 0x92, 0x58, 0x00 };
void os_getDevEui (u1_t* buf) {
  memcpy_P(buf, DEVEUI, 8);
}

// This key should be in big endian format (or, since it is not really a
// number but a block of memory, endianness does not really apply). In
// practice, a key taken from ttnctl can be copied as-is.
// The key shown here is the semtech default key.
static const u1_t PROGMEM APPKEY[16] = { 0x2F, 0xF0, 0x03, 0xC1, 0x62, 0x1D, 0x12, 0x57, 0x93, 0x78, 0xF5, 0xE6, 0x93, 0x74, 0xB5, 0x9F };
void os_getDevKey (u1_t* buf) {
  memcpy_P(buf, APPKEY, 16);
}
//Save Network data in this variables
uint32_t  devaddr;
uint8_t  nwkKey[16];
uint8_t  artKey[16];
uint32_t seqnoUp;

static xref2u1_t mydata[40];

static osjob_t sendjob;

// Schedule TX every this many seconds (might become longer due to duty
// cycle limitations).
const unsigned TX_INTERVAL = 2;

// Pin mapping
const lmic_pinmap lmic_pins = {
  .nss = 18,
  .rxtx = LMIC_UNUSED_PIN,
  .rst = LMIC_UNUSED_PIN,
  .dio = {23, 23, 23},
};

///////////////Global Vars RFM69//////////////////////////
//*********************************************************************************************
//************ IMPORTANT SETTINGS - YOU MUST CHANGE/CONFIGURE TO FIT YOUR HARDWARE ************
//*********************************************************************************************
// Address IDs are 10bit, meaning usable ID range is 1..1023
// Address 0 is special (broadcast), messages to address 0 are received by all *listening* nodes (ie. active RX mode)
// Gateway ID should be kept at ID=1 for simplicity, although this is not a hard constraint
//*********************************************************************************************
#define NODEID        1    // keep UNIQUE for each node on same network
#define NETWORKID     42  // keep IDENTICAL on all nodes that talk to each other
#define GATEWAYID     1    // "central" node

//*********************************************************************************************
// Frequency should be set to match the radio module hardware tuned frequency,
// otherwise if say a "433mhz" module is set to work at 915, it will work but very badly.
// Moteinos and RF modules from LowPowerLab are marked with a colored dot to help identify their tuned frequency band,
// see this link for details: https://lowpowerlab.com/guide/moteino/transceivers/
// The below examples are predefined "center" frequencies for the radio's tuned "ISM frequency band".
// You can always set the frequency anywhere in the "frequency band", ex. the 915mhz ISM band is 902..928mhz.
//*********************************************************************************************
#define FREQUENCY   RF69_433MHZ
//#define FREQUENCY   RF69_868MHZ
//#define FREQUENCY     RF69_915MHZ
//#define FREQUENCY_EXACT 916000000 // you may define an exact frequency/channel in Hz
#define ENCRYPTKEY    "sampleEncryptKey" //exactly the same 16 characters/bytes on all nodes!
//#define IS_RFM69HW_HCW  //uncomment only for RFM69HW/HCW! Leave out if you have RFM69W/CW!
//*********************************************************************************************
//Auto Transmission Control - dials down transmit power to save battery
//Usually you do not need to always transmit at max output power
//By reducing TX power even a little you save a significant amount of battery power
//This setting enables this gateway to work with remote nodes that have ATC enabled to
//dial their power down to only the required level (ATC_RSSI)
//#define ENABLE_ATC    //comment out this line to disable AUTO TRANSMISSION CONTROL
#define ATC_RSSI      -80
//*********************************************************************************************
#define SERIAL_BAUD   115200

#if defined (MOTEINO_M0) && defined(SERIAL_PORT_USBVIRTUAL)
#define Serial SERIAL_PORT_USBVIRTUAL // Required for Serial on Zero based boards
#endif

int TRANSMITPERIOD = 5000; //transmit a packet to gateway so often (in ms)
char buff[20];
byte sendSize = 12;
boolean requestACK = false;
//SPIFlash flash(SS_FLASHMEM, 0xEF30); //EF30 for 4mbit  Windbond chip (W25X40CL)

#ifdef ENABLE_ATC
RFM69_ATC radio;
#else
RFM69 radio;
#endif

long lastPeriod = 0;

///////////////Lora Functions/////////////////////////////
void onEvent (ev_t ev) {
  Serial.print(os_getTime());
  Serial.print(": ");
  switch (ev) {
    case EV_SCAN_TIMEOUT:
      Serial.println(F("EV_SCAN_TIMEOUT"));
      break;
    case EV_BEACON_FOUND:
      Serial.println(F("EV_BEACON_FOUND"));
      break;
    case EV_BEACON_MISSED:
      Serial.println(F("EV_BEACON_MISSED"));
      break;
    case EV_BEACON_TRACKED:
      Serial.println(F("EV_BEACON_TRACKED"));
      break;
    case EV_JOINING:
      Serial.println(F("EV_JOINING"));
      break;
    case EV_JOINED:
      Serial.println(F("EV_JOINED"));
      // Disable link check validation (automatically enabled
      // during join, but not supported by TTN at this time).
      LMIC_setLinkCheckMode(0);
      //isJoined = true;
      break;
    case EV_RFU1:
      Serial.println(F("EV_RFU1"));
      break;
    case EV_JOIN_FAILED:
      Serial.println(F("EV_JOIN_FAILED"));
      break;
    case EV_REJOIN_FAILED:
      Serial.println(F("EV_REJOIN_FAILED"));
      break;
      break;
    case EV_TXCOMPLETE:
      Serial.println(F("EV_TXCOMPLETE (includes waiting for RX windows)"));
      if (LMIC.txrxFlags & TXRX_ACK)
        Serial.println(F("Received ack"));
      if (LMIC.dataLen) {
        Serial.println(F("Received "));
        Serial.println(LMIC.dataLen);
        Serial.println(F(" bytes of payload"));
      }
      isJoined = true;
      // Schedule next transmission
      //os_setTimedCallback(&sendjob, os_getTime() + sec2osticks(TX_INTERVAL), do_send);
      break;
    case EV_LOST_TSYNC:
      Serial.println(F("EV_LOST_TSYNC"));
      break;
    case EV_RESET:
      Serial.println(F("EV_RESET"));
      break;
    case EV_RXCOMPLETE:
      // data received in ping slot
      Serial.println(F("EV_RXCOMPLETE"));
      break;
    case EV_LINK_DEAD:
      Serial.println(F("EV_LINK_DEAD"));
      break;
    case EV_LINK_ALIVE:
      Serial.println(F("EV_LINK_ALIVE"));
      break;
    default:
      Serial.println(F("Unknown event"));
      break;
  }
}

void do_send(osjob_t* j) {
  // Check if there is not a current TX/RX job running
  if (LMIC.opmode & OP_TXRXPEND) {
    Serial.println(F("OP_TXRXPEND, not sending"));
  } else {
    // Prepare upstream data transmission at the next possible time.
    LMIC_setTxData2 ( 1, (xref2u1_t)mydata, 40, 0 ) ;
    Serial.println(F("Packet queued"));
  }

  // Next TX is scheduled after TX_COMPLETE event.
}

void setup() {
  Serial.begin(SERIAL_BAUD);

  //Resetting RFM69
  pinMode(25, OUTPUT);
  digitalWrite(25,HIGH);
  delayMicroseconds(10);
  digitalWrite(25,LOW);
  delay(5);

  //radio.setCS(26);
  radio.initialize(FREQUENCY, NODEID, NETWORKID, 26, 12, false);

#ifdef IS_RFM69HW_HCW
  radio.setHighPower(true); //must include this only for RFM69HW/HCW!
#endif

#ifdef ENCRYPTKEY
  radio.encrypt(ENCRYPTKEY);
#endif

#ifdef FREQUENCY_EXACT
  radio.setFrequency(FREQUENCY_EXACT); //set frequency to some custom frequency
#endif

  //Auto Transmission Control - dials down transmit power to save battery (-100 is the noise floor, -90 is still pretty good)
  //For indoor nodes that are pretty static and at pretty stable temperatures (like a MotionMote) -90dBm is quite safe
  //For more variable nodes that can expect to move or experience larger temp drifts a lower margin like -70 to -80 would probably be better
  //Always test your ATC mote in the edge cases in your own environment to ensure ATC will perform as you expect
#ifdef ENABLE_ATC
  radio.enableAutoPower(ATC_RSSI);
#endif

  char buff[50];
  sprintf(buff, "\nReceiving at %d Mhz...", FREQUENCY == RF69_433MHZ ? 433 : FREQUENCY == RF69_868MHZ ? 868 : 915);
  Serial.println(buff);



#ifdef ENABLE_ATC
  Serial.println("RFM69_ATC Enabled (Auto Transmission Control)\n");
#endif


  Serial.println(F("Starting"));
#ifdef VCC_ENABLE
  // For Pinoccio Scout boards
  pinMode(VCC_ENABLE, OUTPUT);
  digitalWrite(VCC_ENABLE, HIGH);
  delay(1000);
#endif
//  //Set NSS pin of RFM69 as output
//  pinMode(26, OUTPUT);
//  digitalWrite(26, HIGH);
//  delay(1000);

  memcpy(mydata, "Moin", 5);
  // LMIC init
  os_init();

  LMIC_reset();
  LMIC_startJoining();

  // }
  LMIC_setClockError(MAX_CLOCK_ERROR * 10 / 100);//fixing clock error

  do_send(&sendjob);
}

void loop() {
  os_runloop_once();

  if (isJoined) {
    if (!radio.receiveDone())
    {
      Serial.print("Mode: ");
      Serial.println(radio.readReg(REG_OPMODE));
      while(radio.readReg(REG_OPMODE) != 16 ){ //if not in rx mode, put it into rx_mode
        radio.writeReg(REG_OPMODE, (radio.readReg(REG_OPMODE) & 0xE3) | RF_OPMODE_RECEIVER);
        #ifdef IS_RFM69HW_HCW
          radio.setHighPowerRegs(false);
        #endif
      }
      Serial.println("Going into Lightsleep");
      //delay(1000);
      //esp_sleep_enable_timer_wakeup(100000000);
      esp_sleep_enable_ext0_wakeup(GPIO_NUM_13, 1);
      esp_light_sleep_start();
      Serial.println("AUFGEWACHT");
      //Serial.print("Wakeup cause: ");
      //Serial.println(esp_sleep_get_wakeup_cause());
      isJoined = false;
//      if (esp_sleep_get_wakeup_cause() == 4) { //Prevent errors caused by the timer
//        isJoined = true;
//      }
    } else {
//      if (esp_sleep_get_wakeup_cause() == 4) { //Prevent errors caused by the timer
//        isJoined = false;
//      }
      char tmpData[radio.DATALEN + 1 ];
      Serial.print('['); Serial.print(radio.SENDERID, DEC); Serial.print("] ");
      for (byte i = 0; i < radio.DATALEN; i++) {
        Serial.print((char)radio.DATA[i]);
        tmpData[i] = (char)radio.DATA[i];
      }
      Serial.print("   [RX_RSSI:"); Serial.print(radio.RSSI); Serial.print("]");
      if (radio.ACKRequested())
      {
        radio.sendACK();
        Serial.println(" - ACK sent");
      }
      memcpy(mydata, tmpData, sizeof(tmpData));
      do_send(&sendjob);

      Serial.println();
    }
  }

  if (radio.receiveDone()){ 
//    if (esp_sleep_get_wakeup_cause() == 4) { //Prevent errors caused by the timer
//      isJoined = false;
//    }
    char tmpData[radio.DATALEN + 1 ];
    Serial.print('['); Serial.print(radio.SENDERID, DEC); Serial.print("] ");
    for (byte i = 0; i < radio.DATALEN; i++) {
      Serial.print((char)radio.DATA[i]);
      tmpData[i] = (char)radio.DATA[i];
    }
    Serial.print("   [RX_RSSI:"); Serial.print(radio.RSSI); Serial.print("]");
    if (radio.ACKRequested())
    {
      radio.sendACK();
      Serial.println(" - ACK sent");
    }
    memcpy(mydata, tmpData, sizeof(tmpData));
    do_send(&sendjob);

    Serial.println();
  }
}
