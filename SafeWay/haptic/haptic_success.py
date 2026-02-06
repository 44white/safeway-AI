import time
import smbus2

# I2C 설정
I2C_BUS_1 = 0  # 첫 번째 I2C 버스 (버스 0)
I2C_BUS_2 = 1  # 두 번째 I2C 버스 (버스 1)
DRV2605_ADDR = 0x5A  # DRV2605의 기본 I2C 주소 (두 장치 모두 0x5A로 가정)

# 레지스터 주소 정의
DRV2605_REG_MODE = 0x01
DRV2605_REG_LIBRARY = 0x03
DRV2605_REG_WAVESEQ1 = 0x04
DRV2605_REG_GO = 0x0C

# I2C 버스 열기
bus1 = smbus2.SMBus(I2C_BUS_1)  # 첫 번째 I2C 버스
bus2 = smbus2.SMBus(I2C_BUS_2)  # 두 번째 I2C 버스

def drv2605_init(bus, address, bus_number):
    """DRV2605 초기화"""
    print(f"Initializing DRV2605 at address {hex(address)} on bus {bus_number}")
    bus.write_byte_data(address, DRV2605_REG_MODE, 0x00)  # 활성 모드 설정
    bus.write_byte_data(address, DRV2605_REG_LIBRARY, 0x01)  # 라이브러리 1 선택

def play_effect(bus, address, bus_number, effect_id):
    """효과 실행"""
    print(f"Playing effect #{effect_id} on motor at address {hex(address)} on bus {bus_number}")
    bus.write_byte_data(address, DRV2605_REG_WAVESEQ1, effect_id)  # 효과 설정
    bus.write_byte_data(address, DRV2605_REG_WAVESEQ1 + 1, 0x00)  # 효과 종료
    bus.write_byte_data(address, DRV2605_REG_GO, 0x01)  # 실행 명령

# 두 개의 DRV2605 장치 초기화
drv2605_init(bus1, DRV2605_ADDR, I2C_BUS_1)  # 첫 번째 장치 (버스 0)
drv2605_init(bus2, DRV2605_ADDR, I2C_BUS_2)  # 두 번째 장치 (버스 1)

isLeft=True
while True:
    if isLeft:
        for i in range(1000):
            play_effect(bus1, DRV2605_ADDR, I2C_BUS_1, 1)        # 첫 번째 모터
        isLeft=False
    else:
        for i in range(1000):
            play_effect(bus2, DRV2605_ADDR, I2C_BUS_2, 1)   # 두 번째 모터
        isLeft=True
    time.sleep(0.5)  # 100ms 간격으로 실행
    #for i in range(1,2):  # 효과 ID는 0부터 47까지, 최대 48개 효과
        # 두 모터의 진동 강도를 반비례로 설정
        # 첫 번째 모터: effect_id = i, 두 번째 모터: effect_id = 47 - i (반비례 관계)

