import subprocess
import signal
import time
import os
# 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BT_DIR = os.path.join(BASE_DIR, "bluetooth")
MONITOR_SCRIPT = "monitor.py"
BT_SERVER_BINARY = "bluetooth_server"
MONITOR_PATH = os.path.join(BT_DIR, MONITOR_SCRIPT)
BT_SERVER_PATH = os.path.join(BT_DIR, BT_SERVER_BINARY)

# 실행 중인 프로세스 저장
processes = []


# 🚀 전체 실행 함수
def launch_programs():
    
    print("▶ main_inference.py 실행")
    inference_command = (
        "source /home/safeway/Desktop/SafeWay/venv/bin/activate && "
        "python /home/safeway/Desktop/SafeWay/main_inference.py"
    )
    inference_proc = subprocess.Popen(
        ["bash", "-c", inference_command],
        cwd="/home/safeway/Desktop/SafeWay"
    )
    processes.append(inference_proc)






# 🔁 메인 루프
def main():
    try:
        print("🚀 프로그램 시작! 5초 후 Vision Service를 실행합니다.")
        time.sleep(5)
        launch_programs()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        terminate_programs()

if __name__ == "__main__":
    main()
