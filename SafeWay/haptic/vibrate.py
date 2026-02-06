import sys
import smbus2
import time
import threading  # 맨 위에 추가


I2C_BUS_1 = 0  # 왼쪽
I2C_BUS_2 = 1  # 오른쪽
DRV2605_ADDR = 0x5A
DRV2605_REG_MODE = 0x01
DRV2605_REG_LIBRARY = 0x03
DRV2605_REG_WAVESEQ1 = 0x04
DRV2605_REG_GO = 0x0C

STRONG_CLICK_EFFECT_ID = 1  # 가장 강한 진동

def drv2605_init(bus):
    bus.write_byte_data(DRV2605_ADDR, DRV2605_REG_MODE, 0x00)  # 내장 모드
    bus.write_byte_data(DRV2605_ADDR, DRV2605_REG_LIBRARY, 0x01)  # ERM Library

def play_effect(bus, effect_id=STRONG_CLICK_EFFECT_ID, duration_sec=2):
    end_time = time.time() + duration_sec
    while time.time() < end_time:
        bus.write_byte_data(DRV2605_ADDR, DRV2605_REG_WAVESEQ1, effect_id)
        bus.write_byte_data(DRV2605_ADDR, DRV2605_REG_WAVESEQ1 + 1, 0x00)
        bus.write_byte_data(DRV2605_ADDR, DRV2605_REG_GO, 0x01)
        time.sleep(0.1)  # 효과 재생 후 약간의 대기 (효과 간 중복 방지)

def main():
    if len(sys.argv) != 2:
        print("사용법: python vibrate.py [left|right|both]")
        return

    target = sys.argv[1]
    bus1 = smbus2.SMBus(I2C_BUS_1)
    bus2 = smbus2.SMBus(I2C_BUS_2)
    drv2605_init(bus1)
    drv2605_init(bus2)

    if target == "left":
        print("▶ 왼쪽 진동 (2초간)")
        play_effect(bus1)
    elif target == "right":
        print("▶ 오른쪽 진동 (2초간)")
        play_effect(bus2)
    elif target == "both":
        print("▶ 양쪽 진동 (2초간)")
        thread1 = threading.Thread(target=play_effect, args=(bus1,))
        thread2 = threading.Thread(target=play_effect, args=(bus2,))
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()
    else:
        print("⚠️ 잘못된 인자:", target)

if __name__ == "__main__":
    main()
