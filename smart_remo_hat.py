# KSY Smart Remote Control HAT
# Sample Test Code

import RPi.GPIO as GPIO
import time
import datetime
import board
import busio
import smbus2                  #require pip install

#Ir Remo 
#sudo systemctl enable pigpiod
#sudo systemctl start pigpiod


#I2C   
#Ambient Light Sensor: VEML7700 0x10
#Humidity and Temperature Sensor: SHT30-DIS-B2.5KS 0x44    
#Barometric Pressure Sensor: 2SMPB-02E 0x70
#I2C EEPROM: 24FC256T-I/ST 0x50 (DNP)    
    
#GPIO
#GPIO4 Ir_RX(IN)
#GPIO9 T_OUT(IN) Moving detection output
#GPIO10 D_OUT(IN) Comparator output   
#GPIO11 Ir_Tx(Out)
#GOIO14 SW (IN)
#GPIO27 Red LED(Out)
#GPIO17 Green LED(Out)
#GPIO15 Blue  LED(Out)

#GPIOの定義
LED_RED :int  = 27  
LED_GREEN :int  = 17
LED_BLUE :int = 15
PORT_SW :int  = 14
PORT_T :int = 10
PORT_D :int = 9
Ir_TX :int = 11
Ir_RX :int = 4

# i2cのアドレス
#
addr_veme7700 = 0x10
addr_SHT3x = 0x44
addr_2SMPB = 0x70



# Callback SW
# 
def callback_SW(pin):
    # Check SW
    if GPIO.input(PORT_SW) == GPIO.LOW:
        GPIO.output(LED_RED, GPIO.LOW) # 消灯
        GPIO.output(LED_GREEN, GPIO.LOW) # 消灯
        GPIO.output(LED_BLUE, GPIO.HIGH) # 点灯
        print("Switch ON")
    else:    
        GPIO.output(LED_GREEN, GPIO.LOW) # 消灯
        GPIO.output(LED_RED, GPIO.LOW) # 消灯
        GPIO.output(LED_BLUE, GPIO.LOW) # 消灯    
    return

#Callback Pyroelectric Infrared Sensor
def callback_TOUT(pin):
    #Check Pyroelectric Infrared Sensor
    if GPIO.input(PORT_T) == GPIO.HIGH:
        print("T OUT = ON")
        GPIO.output(LED_RED, GPIO.HIGH) # 点灯
    else:
        print("T OUT = OFF")
        GPIO.output(LED_RED, GPIO.LOW) # 消灯
  
    return

def callback_DOUT(pin):
    #Check Pyroelectric Infrared Sensor            
    if GPIO.input(PORT_D) == GPIO.HIGH:
        print("D OUT = ON")
    else:
        print("D OUT = OFF")      
    return



#VEML7700
class VEML7700:

    #クラス変数
    I2C_ADDR = 0x70
    
    #VEML7700 regidters
    ALS_CONF_0 = 0x00 #ALS gain, integration time, interrupt, and shutdown
    ALS_WH = 0x01     #ALS high threshold window setting
    ALS_WL = 0x02     #ALS low threshold window setting
    POW_SAV = 0x03    #Set (15 : 3) 0000 0000 0000 0b
    ALS = 0x04        #ALS 16 bits(R) 
    WHITE = 0x05      #White 16 bits(R) 
    INTERRUPT = 0x06  #ALS INT trigger event(R)  

    # These settings will provide the max range for the sensor (0-120Klx)
    # but at the lowest precision:
    #              LSB   MSB
    confValues = [0x00, 0x13] # 1/8 gain, 25ms IT (Integration Time)
    #Reference data sheet Table 1 for configuration settings

    interrupt_high = [0x00, 0x00] # Clear values
    #Reference data sheet Table 2 for High Threshold

    interrupt_low = [0x00, 0x00] # Clear values
    #Reference data sheet Table 3 for Low Threshold

    power_save_mode = [0x00, 0x00] # Clear values
    #Reference data sheet Table 4 for Power Saving Modes
    def __init__(self, address=0x70):
        
        self.I2C_ADDR = address
        
        bus.write_i2c_block_data(self.I2C_ADDR , self.ALS_CONF_0, self.confValues)
        bus.write_i2c_block_data(self.I2C_ADDR , self.ALS_WH, self.interrupt_high)
        bus.write_i2c_block_data(self.I2C_ADDR , self.ALS_WL, self.interrupt_low)
        bus.write_i2c_block_data(self.I2C_ADDR , self.POW_SAV, self.power_save_mode)
    
    def readData(self):
        time.sleep(0.04) # 40ms 

        word = bus.read_word_data(self.I2C_ADDR ,self.ALS)

        gain = 1.8432 #Gain for 1/8 gain & 25ms IT
        #Reference www.vishay.com/docs/84323/designingveml7700.pdf
        # 'Calculating the LUX Level'

        val = word * gain
        val = round(val,1) #Round value for presentation
        return (val)


# (c) Copyright 2019 Sensirion AG, Switzerland
#0x31(0x131)（x^8 + x^5 + x^4 + 1）
class CrcCalculator(object):

    def __init__(self, width=8, polynomial=0x31, init_value=0xFF, final_xor=0x00):

        super(CrcCalculator, self).__init__()
        self._width = width
        self._polynomial = polynomial
        self._init_value = init_value
        self._final_xor = final_xor

    def calc(self, data):

        crc = self._init_value
        for value in data:
            crc ^= value
            for i in range(self._width):
                if crc & (1 << (self._width - 1)):
                    crc = (crc << 1) ^ self._polynomial
                else:
                    crc = crc << 1
                crc &= (1 << self._width) - 1
        return crc ^ self._final_xor


# SHT30(温湿度センサ)の測定
class SHT3x:

    #SHT3x command
    CMD_READ_SERIALNBR  = [0x37, 0x80]  # read serial number
    CMD_READ_STATUS     = [0xF3, 0x2D]  # read status register
    CMD_CLEAR_STATUS    = [0x30, 0x41]  # clear status register
    CMD_HEATER_ENABLE   = [0x30, 0x6D]  # enabled heater
    CMD_HEATER_DISABLE  = [0x30, 0x66]  # disable heater
    CMD_SOFT_RESET      = [0x30, 0xA2]  # soft reset
    CMD_MEAS_CLOCKSTR_H = [0x2C, 0x06]  # measurement: clock stretching  high repeatability
    CMD_MEAS_CLOCKSTR_M = [0x2C, 0x0D]  # measurement: clock stretching  medium repeatability
    CMD_MEAS_CLOCKSTR_L = [0x2C, 0x10]  # measurement: clock stretching  low repeatability
    CMD_MEAS_POLLING_H  = [0x24, 0x00]  # measurement: polling  high repeatability
    CMD_MEAS_POLLING_M  = [0x24, 0x0B]  # measurement: polling  medium repeatability
    CMD_MEAS_POLLING_L  = [0x24, 0x16]  # measurement: polling  low repeatability
    CMD_MEAS_PERI_05_H  = [0x20, 0x32]  # measurement: periodic 0.5 mps  high repeatability
    CMD_MEAS_PERI_05_M  = [0x20, 0x24]  # measurement: periodic 0.5 mps  medium repeatability
    CMD_MEAS_PERI_05_L  = [0x20, 0x2F]  # measurement: periodic 0.5 mps  low repeatability
    CMD_MEAS_PERI_1_H   = [0x21, 0x30]  # measurement: periodic 1 mps  high repeatability
    CMD_MEAS_PERI_1_M   = [0x21, 0x26]  # measurement: periodic 1 mps  medium repeatability
    CMD_MEAS_PERI_1_L   = [0x21, 0x2D]  # measurement: periodic 1 mps  low repeatability
    CMD_MEAS_PERI_2_H   = [0x22, 0x36]  # measurement: periodic 2 mps  high repeatability
    CMD_MEAS_PERI_2_M   = [0x22, 0x20]  # measurement: periodic 2 mps  medium repeatability
    CMD_MEAS_PERI_2_L   = [0x22, 0x2B]  # measurement: periodic 2 mps  low repeatability
    CMD_MEAS_PERI_4_H   = [0x23, 0x34]  # measurement: periodic 4 mps  high repeatability
    CMD_MEAS_PERI_4_M   = [0x23, 0x22]  # measurement: periodic 4 mps  medium repeatability
    CMD_MEAS_PERI_4_L   = [0x23, 0x29]  # measurement: periodic 4 mps  low repeatability
    CMD_MEAS_PERI_10_H  = [0x27, 0x37]  # measurement: periodic 10 mps  high repeatability
    CMD_MEAS_PERI_10_M  = [0x27, 0x21]  # measurement: periodic 10 mps  medium repeatability
    CMD_MEAS_PERI_10_L  = [0x27, 0x2A]  # measurement: periodic 10 mps  low repeatability
    CMD_FETCH_DATA      = [0xE0, 0x00]  # readout measurements for periodic mode
    CMD_R_AL_LIM_LS     = [0xE1, 0x02]  # read alert limits  low set
    CMD_R_AL_LIM_LC     = [0xE1, 0x09]  # read alert limits  low clear
    CMD_R_AL_LIM_HS     = [0xE1, 0x1F]  # read alert limits  high set
    CMD_R_AL_LIM_HC     = [0xE1, 0x14]  # read alert limits  high clear
    CMD_W_AL_LIM_HS     = [0x61, 0x1D]  # write alert limits  high set
    CMD_W_AL_LIM_HC     = [0x61, 0x16]  # write alert limits  high clear
    CMD_W_AL_LIM_LC     = [0x61, 0x0B]  # write alert limits  low clear
    CMD_W_AL_LIM_LS     = [0x61, 0x00]  # write alert limits  low set
    CMD_NO_SLEEP        = [0x30, 0x3E]  #

    I2C_ADDR = 0x44
    
    def __init__(self,address=0x44):
        self.I2C_ADDR = address
        #SHT30 繰り返し精度=高 測定頻度=1mps 
        bus.write_byte_data(self.I2C_ADDR, *self.CMD_MEAS_PERI_1_H)
        
    def stopMeasure(self):
        bus.write_byte_data(self.I2C_ADDR, 0x30, 0x93)
    
    def softReset(self):
        bus.write_byte_data(self.I2C_ADDR, *self.CMD_SOFT_RESET)
        
    def readStatus(self):
        #ステータスレジスタの読出しコマンド
        bus.write_byte_data(self.I2C_ADDR, *self.CMD_READ_STATUS)
        time.sleep(0.01)
        data = bus.read_i2c_block_data(self.I2C_ADDR, 0x00, 3) #ステータスレジスタ


    def readData(self):
        #測定データ取込みコマンド
        bus.write_byte_data(self.I2C_ADDR, *self.CMD_FETCH_DATA)
        time.sleep(0.1)
        data = bus.read_i2c_block_data(self.I2C_ADDR, 0x00, 6) #測定データ

        crc1 = data[2]
        crc2 = data[5]
        calc1= crc8.calc(data[0:2])
        calc2= crc8.calc(data[3:5])
        if crc1 == calc1 and crc2 == calc2:
            # 温度計算
            # T[℃] = -45 +175*St/(2^16-1)
            temp_mlsb = ((data[0] << 8) | data[1])
            temp = -45 + 175 * int(str(temp_mlsb), 10) / (pow(2, 16) - 1)

            # 湿度計算
            # RH = 100*Srh/(2^16-1)
            humi_mlsb = ((data[3] << 8) | data[4])
            humi = 100 * int(str(humi_mlsb), 10) / (pow(2, 16) - 1)
        else:
            print ("CRC Error")
            temp = -300
            humi = -300
        return [temp, humi]


# Driver for 2SMPD-02E
# https://github.com/omron-devhub/2smpb02e-grove-raspberrypi
# Copyright (c) OMRON Corporation. All rights reserved.
class Omron2smpd02e:

    I2C_ADDR = 0x70
     
    REG_TEMP_TXD0       = 0xfc
    REG_TEMP_TXD1       = 0xfb
    REG_TEMP_TXD2       = 0xfa
    REG_PRESS_TXD0      = 0xf9
    REG_PRESS_TXD1      = 0xf8
    REG_PRESS_TXD2      = 0xf7
    REG_IO_SETUP        = 0xf5
    REG_CTRL_MEAS       = 0xf4
    REG_DEVICE_STAT     = 0xd3
    REG_I2C_SET         = 0xf2
    REG_IIR_CNT         = 0xf1
    REG_RESET           = 0xe0
    REG_CHIP_ID         = 0xd1
    REG_COE_b00_a0_ex   = 0xb8
    REG_COE_a2_0        = 0xb7
    REG_COE_a2_1        = 0xb6
    REG_COE_a1_0        = 0xb5
    REG_COE_a1_1        = 0xb4
    REG_COE_a0_0        = 0xb3
    REG_COE_a0_1        = 0xb2
    REG_COE_bp3_0       = 0xb1
    REG_COE_bp3_1       = 0xb0
    REG_COE_b21_0       = 0xaf
    REG_COE_b21_1       = 0xae
    REG_COE_b12_0       = 0xad
    REG_COE_b12_1       = 0xac
    REG_COE_bp2_0       = 0xab
    REG_COE_bp2_1       = 0xaa
    REG_COE_b11_0       = 0xa9
    REG_COE_b11_1       = 0xa8
    REG_COE_bp1_0       = 0xa7
    REG_COE_bp1_1       = 0xa6
    REG_COE_bt2_0       = 0xa5
    REG_COE_bt2_1       = 0xa4
    REG_COE_bt1_0       = 0xa3
    REG_COE_bt1_1       = 0xa2
    REG_COE_b00_0       = 0xa1
    REG_COE_b00_1       = 0xa0
 
    AVG_SKIP    = 0x0
    AVG_1       = 0x1
    AVG_2       = 0x2
    AVG_4       = 0x3
    AVG_8       = 0x4
    AVG_16      = 0x5
    AVG_32      = 0x6
    AVG_64      = 0x7
 
    MODE_SLEEP  = 0x0
    MODE_FORCED = 0x1
    MODE_NORMAL = 0x3
 
    def __init__(self,address=0x70):
        self.I2C_ADDR = address
        self.writeByteData(0xf5, 0x00)
        time.sleep(0.5)
        self.setAverage(self.AVG_1,self.AVG_1)
 
    def writeByteData(self,address,data):
        bus.write_byte_data(self.I2C_ADDR, address, data)
 
    def readByte(self,addr):
        data = bus.read_i2c_block_data(self.I2C_ADDR, addr, 1)
        return data[0]
 
    def readByteData(self,addr,num):
        data = bus.read_i2c_block_data(self.I2C_ADDR, addr, num)
        return data
 
    def setAverage(self,avg_tem,avg_pressure):
        bus.write_byte_data(self.I2C_ADDR, self.REG_CTRL_MEAS, 0x27)
 
    def readRawTemp(self):
        temp_txd2 = self.readByte(self.REG_TEMP_TXD2)
        temp_txd1 = self.readByte(self.REG_TEMP_TXD1)
        temp_txd0 = self.readByte(self.REG_TEMP_TXD0)
        Dt = (temp_txd2 << 16 | temp_txd1 << 8 | temp_txd0) - pow(2,23)
        return Dt
 
    def readRawPress(self):
        press_txd2 = self.readByte(self.REG_PRESS_TXD2)
        press_txd1 = self.readByte(self.REG_PRESS_TXD1)
        press_txd0 = self.readByte(self.REG_PRESS_TXD0)
        Dp = (press_txd2 << 16 | press_txd1 << 8 | press_txd0) - pow(2,23)
        return Dp
 
    def readTr(self):
        Dt = self.readRawTemp()
        coe_a0 = self.readByteData(self.REG_COE_a0_1, 2)
        b00_a0_ex = self.readByteData(self.REG_COE_b00_a0_ex, 1)
        a0 = (coe_a0[0] << 12 | coe_a0[1] << 4 | b00_a0_ex[0] & 0x0f)
        a0 = -(a0 & 0b10000000000000000000) | (a0 & 0b01111111111111111111)
        a0 = self.conv_K1(a0)
 
        data = self.readByteData(self.REG_COE_a1_1, 2)
        a1 = (data[0] << 8 | data[1])
        a1 = -(a1 & 0b1000000000000000) | (a1 & 0b0111111111111111)
        a1 = self.conv_K0(a1, -6.3e-3, 4.3e-4)
 
        data = self.readByteData(self.REG_COE_a2_1, 2)
        a2 = (data[0] << 8 | data[1])
        a2 = -(a2 & 0b1000000000000000) | (a2 & 0b0111111111111111)
        a2 = self.conv_K0(a2, -1.9e-11, 1.2e-10)       
 
        Tr = a0 + (a1 + a2 * Dt) * Dt
        return Tr
 
    def readData(self):
        Dp = self.readRawPress()
        Tr = self.readTr()
 
        coe_b00 = self.readByteData(self.REG_COE_b00_1, 2)
        b00_a0_ex = self.readByteData(self.REG_COE_b00_a0_ex, 1)
        b00 = (coe_b00[0] << 12 | coe_b00[1] << 4 | b00_a0_ex[0] >> 4)
        b00 = -(b00 & 0b10000000000000000000) | (b00 & 0b01111111111111111111)
        b00 = self.conv_K1(b00)
 
        data = self.readByteData(self.REG_COE_bt1_1, 2)
        bt1 = (data[0] << 8 | data[1])
        bt1 = -(bt1 & 0b1000000000000000) | (bt1 & 0b0111111111111111)
        bt1 = self.conv_K0(bt1, 1.0e-1, 9.1e-2)
         
        data = self.readByteData(self.REG_COE_bt2_1, 2)
        bt2 = (data[0] << 8 | data[1])
        bt2 = -(bt2 & 0b1000000000000000) | (bt2 & 0b0111111111111111)
        bt2 = self.conv_K0(bt2, 1.2e-8, 1.2e-6)
 
        data = self.readByteData(self.REG_COE_bp1_1, 2)
        bp1 = (data[0] << 8 | data[1])
        bp1 = -(bp1 & 0b1000000000000000) | (bp1 & 0b0111111111111111)
        bp1 = self.conv_K0(bp1, 3.3e-2, 1.9e-2)
 
        data = self.readByteData(self.REG_COE_b11_1, 2)
        b11 = (data[0] << 8 | data[1])
        b11 = -(b11 & 0b1000000000000000) | (b11 & 0b0111111111111111)
        b11 = self.conv_K0(b11, 2.1e-7, 1.4e-7)
 
        data = self.readByteData(self.REG_COE_bp2_1, 2)
        bp2 = (data[0] << 8 | data[1])
        bp2 = -(bp2 & 0b1000000000000000) | (bp2 & 0b0111111111111111)
        bp2 = self.conv_K0(bp2, -6.3e-10, 3.5e-10)
 
        data = self.readByteData(self.REG_COE_b12_1, 2)
        b12 = (data[0] << 8 | data[1])
        b12 = -(b12 & 0b1000000000000000) | (b12 & 0b0111111111111111)
        b12 = self.conv_K0(b12, 2.9e-13, 7.6e-13)
 
        data = self.readByteData(self.REG_COE_b21_1, 2)
        b21 = (data[0] << 8 | data[1])
        b21 = -(b21 & 0b1000000000000000) | (b21 & 0b0111111111111111)
        b21 = self.conv_K0(b21, 2.1e-15, 1.2e-14)
 
        data = self.readByteData(self.REG_COE_bp3_1, 2)
        bp3 = (data[0] << 8 | data[1])
        bp3 = -(bp3 & 0b1000000000000000) | (bp3 & 0b0111111111111111)
        bp3 = self.conv_K0(bp3, 1.3e-16, 7.9e-17)
 
        Pr = b00 + bt1 * Tr + bp1 * Dp + b11 * Dp * Tr + bt2 * pow(Tr,2) + bp2 * pow(Dp,2) + b12 * Dp * pow(Tr,2) + b21 * pow(Dp,2) * Tr + bp3 * pow(Dp,3)
 
        press = Pr / 100.0
        temp = Tr / 256.0
 
        return press, temp
 
    def conv_K0(self,x,a,s):
        return (a + (((s * float(x)) / 32767.0)))
 
    def conv_K1(self,x):
        return (float(x) / 16.0)





# GPIO init
GPIO.setmode(GPIO.BCM)

GPIO.setup(LED_RED, GPIO.OUT)  
GPIO.setup(LED_GREEN, GPIO.OUT)
GPIO.setup(LED_BLUE, GPIO.OUT)
GPIO.setup(Ir_TX, GPIO.OUT)

GPIO.output(LED_BLUE, GPIO.LOW)
GPIO.output(LED_RED, GPIO.LOW)
GPIO.output(LED_GREEN, GPIO.LOW)
GPIO.output(Ir_TX, GPIO.LOW)

GPIO.setup(PORT_SW, GPIO.IN)
GPIO.setup(PORT_T, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(PORT_D, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(Ir_RX, GPIO.IN, pull_up_down = GPIO.PUD_UP)


GPIO.add_event_detect(PORT_SW, GPIO.BOTH, callback=callback_SW,bouncetime=300)  #立ち下りエッジ
GPIO.add_event_detect(PORT_T, GPIO.BOTH, callback=callback_TOUT)  #両エッジ
GPIO.add_event_detect(PORT_D, GPIO.BOTH, callback=callback_DOUT)  #両エッジ






# SMBusモジュールの設定
bus = smbus2.SMBus(1)
# i2c通信の設定     


sensor = Omron2smpd02e(addr_2SMPB)

bus.write_byte_data(0x70, 0x21, 0x30) #2SMPB
veml7700 = VEML7700(addr_veme7700) #VEML7700 init
sht3x = SHT3x(addr_SHT3x) #SHT3x init
crc8 = CrcCalculator()
time.sleep(1)


def main():
 
 
 
 
    print ("start")


    while True:
        print ("--------")
        press, temp = sensor.readData()
        print(datetime.datetime.today().strftime("[%Y/%m/%d %H:%M:%S]"))
        print("Pressure = %.1f[hPa] temp. = %.1f[℃]" %(press,temp))
        
       
        data = sht3x.readData()
        print( str("Temp. = {:.1f}".format(data[0])) + "[℃]" )
        print( str("Humidity = {:.1f}".format(data[1])) + "[%]" )
        

        val = veml7700.readData()    
        print ("Ambient light = " + str(val) + "[lx]" )       
        

        

            
            
        GPIO.output(LED_GREEN, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(LED_GREEN, GPIO.LOW)  
        time.sleep(0.9)

    
if __name__ == '__main__':
    main()
    # 測定終了
    GPIO.cleanup()  
 

    
