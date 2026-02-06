# haptic.py

import smbus2

I2C_BUS_1 = 0  
I2C_BUS_2 = 1  
DRV2605_ADDR = 0x5A  

DRV2605_REG_MODE = 0x01
DRV2605_REG_LIBRARY = 0x03
DRV2605_REG_WAVESEQ1 = 0x04
DRV2605_REG_GO = 0x0C

bus1 = smbus2.SMBus(I2C_BUS_1)  
bus2 = smbus2.SMBus(I2C_BUS_2)  

def drv2605_init(bus, address, bus_number):
    bus.write_byte_data(address, DRV2605_REG_MODE, 0x00)  
    bus.write_byte_data(address, DRV2605_REG_LIBRARY, 0x01)  

def play_effect(bus, address, bus_number, effect_id):
    bus.write_byte_data(address, DRV2605_REG_WAVESEQ1, effect_id)  
    bus.write_byte_data(address, DRV2605_REG_WAVESEQ1 + 1, 0x00)  
    bus.write_byte_data(address, DRV2605_REG_GO, 0x01)  

# 장치 초기화 함수
def init_all():
    drv2605_init(bus1, DRV2605_ADDR, I2C_BUS_1)
    drv2605_init(bus2, DRV2605_ADDR, I2C_BUS_2)

# 진동 실행 함수
def vibrate(left_level=None, right_level=None):
    if left_level:
        play_effect(bus1, DRV2605_ADDR, I2C_BUS_1, left_level)
    if right_level:
        play_effect(bus2, DRV2605_ADDR, I2C_BUS_2, right_level)
