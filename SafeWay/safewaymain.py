import subprocess
import signal
import time
import os
from playsound import playsound


# 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BT_DIR = os.path.join(BASE_DIR, "bluetooth")
MONITOR_SCRIPT = "monitor.py"
BT_SERVER_BINARY = "bluetooth_server"
MONITOR_PATH = os.path.join(BT_DIR, MONITOR_SCRIPT)
BT_SERVER_PATH = os.path.join(BT_DIR, BT_SERVER_BINARY)

# 실행 중인 프로세스 저장
processes = []

# 📡 Wi-Fi 연결 여부 확인 함수
def is_wifi_connected():
    try:
        result = subprocess.run(["iwgetid", "-r"], capture_output=True, text=True)
        ssid = result.stdout.strip()
        return ssid != ""
    except Exception as e:
        print(f"Wi-Fi 상태 확인 중 오류 발생: {e}")
        return False

# 📡 Wi-Fi 연결 대기 함수
def wait_for_wifi():
    print("📡 Wi-Fi 연결 대기 중...")
    while not is_wifi_connected():
        print("⏳ Wi-Fi가 아직 연결되지 않았습니다. 3초 후 다시 시도합니다.")
        time.sleep(3)
    print("✅ Wi-Fi 연결됨!")

# ⚙️ bluetooth_server 실행 중이면 종료
def kill_bt_server():
    try:
        result = subprocess.run(["pgrep", "-f", BT_SERVER_BINARY], capture_output=True, text=True)
        pids = result.stdout.strip().split()
        if pids:
            for pid in pids:
                print(f"🛑 bluetooth_server 종료 중... (PID: {pid})")
                subprocess.run(["kill", "-9", pid])
            print("✅ 기존 bluetooth_server 종료 완료")
    except Exception as e:
        print(f"bluetooth_server 종료 중 오류 발생: {e}")

def wait_for_bluetooth():

    print("📶 Bluetooth 서비스 대기 중...")
    while True:
        result = subprocess.run(["hciconfig"], capture_output=True, text=True)
        if "UP RUNNING" in result.stdout:
            print("✅ Bluetooth 서비스 준비 완료!")

            break
        print("⏳ Bluetooth 아직 준비되지 않음. 2초 대기...")
        time.sleep(2)

def wait_for_audio():
    print("🔊 오디오 장치 대기 중...")
    for _ in range(10):
        result = subprocess.run(["aplay", "-l"], capture_output=True, text=True)
        if "card" in result.stdout:
            print("✅ 오디오 장치 인식됨!")
            return True
        print("⏳ 오디오 장치 미인식. 1초 후 재시도...")
        time.sleep(1)
    print("❌ 오디오 장치 인식 실패.")
    return False

def play_audio(path):
    subprocess.run(["aplay", path])


# 🚀 전체 실행 함수
def launch_programs():
    print("원격 제어 서버 실행 준비 중 ...")

    # wait_for_wifi()

    #print("✅ VNC 서버 실행 중...")
    #try:
    #    result = subprocess.run(
    #        ["sudo", "/etc/vnc/vncservice", "start", "vncserver-x11-serviced"],
    #        check=True, capture_output=True, text=True
    #    )
    #    print(result.stdout)
    #except subprocess.CalledProcessError as e:
    #    print("VNC 실행 중 오류 발생:")
    #    print(e.stderr)



    #print("▶ bluetooth_server 재시작 준비")
    #kill_bt_server()
    #time.sleep(1)  # 종료 대기 시간
    print("▶ bluetooth_server 실행")
    bt_proc = subprocess.Popen([BT_SERVER_PATH], cwd=BT_DIR)
    processes.append(bt_proc)


    print("▶ monitor.py 실행")
    monitor_proc = subprocess.Popen(["python3", MONITOR_SCRIPT], cwd=BT_DIR)
    processes.append(monitor_proc)

    set_volume(100)  # 볼륨 크기 설정
    print(f"현재 볼륨: {get_volume()}%")

    # wait_for_audio()
    play_audio("./안내음성/부팅완료.wav")    

    # print("▶ main_inference.py 실행")
    # inference_command = (
    #     "source /home/safeway/Desktop/SafeWay/venv/bin/activate && "
    #     "python /home/safeway/Desktop/SafeWay/main_inference.py"
    # )
    # inference_proc = subprocess.Popen(
    #     ["bash", "-c", inference_command],
    #     cwd="/home/safeway/Desktop/SafeWay"
    # )
    # processes.append(inference_proc)


CONTROL_NAME = "Master"  # 이 부분을 amixer scontrols 결과에 맞게 수정

def set_volume(percent):
    if not (0 <= percent <= 100):
        raise ValueError("볼륨은 0~100 사이여야 합니다.")
    
    command = ["amixer", "sset", CONTROL_NAME, f"{percent}%"]
    subprocess.run(command)

def get_volume():
    result = subprocess.run(["amixer", "get", CONTROL_NAME], capture_output=True, text=True)
    lines = result.stdout.split('\n')
    for line in lines:
        if "%" in line:
            start = line.find("[") + 1
            end = line.find("%")
            return int(line[start:end])
    return None

    
# 🛑 종료 시 모든 프로세스 종료
def terminate_programs():
    print("\n🛑 종료 중... 실행 중인 모든 프로세스 정리")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            print(f"⚠️ 프로세스 강제 종료: {proc.pid}")
            proc.kill()
    print("✅ 모든 프로세스 종료됨")

# 🔁 메인 루프
def main():
    try:
        print("🚀 프로그램 시작! 5초 후 SafeWay를 실행합니다.")
        time.sleep(5)
        wait_for_bluetooth()
        launch_programs()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        terminate_programs()

if __name__ == "__main__":
    main()
