import time
import smbus2


I2C_BUS_1 = 0  
I2C_BUS_2 = 1  
DRV2605_ADDR = 0x5A  

# 레지스터
DRV2605_REG_MODE = 0x01
DRV2605_REG_LIBRARY = 0x03
DRV2605_REG_WAVESEQ1 = 0x04
DRV2605_REG_GO = 0x0C

left = True
right = True

bus1 = smbus2.SMBus(I2C_BUS_1)  
bus2 = smbus2.SMBus(I2C_BUS_2)  

# 초기화
def drv2605_init(bus, address, bus_number):
    
    print(f"Initializing DRV2605 at address {hex(address)} on bus {bus_number}")
    bus.write_byte_data(address, DRV2605_REG_MODE, 0x00)  
    bus.write_byte_data(address, DRV2605_REG_LIBRARY, 0x01)  

# 진동 효과 발생
def play_effect(bus, address, bus_number, effect_id):
    
    print(f"Playing effect #{effect_id} on motor at address {hex(address)} on bus {bus_number}")
    bus.write_byte_data(address, DRV2605_REG_WAVESEQ1, effect_id)  
    bus.write_byte_data(address, DRV2605_REG_WAVESEQ1 + 1, 0x00)  
    bus.write_byte_data(address, DRV2605_REG_GO, 0x01)  

# 두 개의 DRV2605 장치 초기화
drv2605_init(bus1, DRV2605_ADDR, I2C_BUS_1)  # 첫 번째 장치 (버스 0)
drv2605_init(bus2, DRV2605_ADDR, I2C_BUS_2)  # 두 번째 장치 (버스 1)

while True:
    if left:
        play_effect(bus1, DRV2605_ADDR, I2C_BUS_1, 4
        )        # 첫 번째 모터
    if right :
        play_effect(bus2, DRV2605_ADDR, I2C_BUS_2, 1)   # 두 번째 모터
    #time.sleep(1)  # 100ms 간격으로 실행


# 1: 100%진동 2: 75%진동 3: 50%진동 4: 30%진동 5: 10%진동 6: 1%진동 
