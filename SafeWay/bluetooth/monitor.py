import time
import os
import subprocess
from playsound import playsound


LOG_FILE = "received_messages.txt"
PROCESSED_FILE = "processed_lines.txt"

# turnType → 메시지 맵
turn_type_map = {
    11: "직진하세요", 12: "좌회전하세요", 13: "우회전하세요",
    16: "8시 방향으로 좌회전하세요", 17: "10시 방향으로 좌회전하세요",
    18: "2시 방향으로 우회전하세요", 19: "4시 방향으로 우회전하세요",
    233: "직진하세요 (임시)",200: "출발지입니다",201: "목적지에 도착했습니다"
}

# 방향 분류
TURNTYPE_LEFT = {12, 16, 17}
TURNTYPE_RIGHT = {13, 18, 19}
TURNTYPE_STRAIGHT = {11, 233}
TURNTYPE_START = {200}
TURNTYPE_END = {201}



def load_processed_lines():
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)

def save_processed_line(line):
    with open(PROCESSED_FILE, "a", encoding="utf-8") as f:
        f.write(line.strip() + "\n")


def handle_turn(turn_type):
    if turn_type in TURNTYPE_LEFT:
        print("▶ 좌회전 → 왼쪽 음성 안내")
        playsound("../안내음성/좌회전.wav")
    elif turn_type in TURNTYPE_RIGHT:
        print("▶ 우회전 → 오른쪽 음성 안내")
        playsound("../안내음성/우회전.wav")
    elif turn_type in TURNTYPE_STRAIGHT:
        print("▶ 직진 → 직진 음성 안내")
        playsound("../안내음성/직진.wav")
    elif turn_type in TURNTYPE_START:
        print("▶ 출발점 → 출발점 음성 안내")
        playsound("../안내음성/출발지.wav")
    elif turn_type in TURNTYPE_END:
        print("▶ 목적지 → 도착 음성 안내")
        playsound("../안내음성/목적지.wav")
    else:
        print(f"▶ turnType {turn_type}은(는) 음성 안내 없음")


def process_line(line):
    parts = line.strip().split(", ")
    if len(parts) != 3:
        return
    timestamp, label, code = parts
    if label != "turnMessage":
        return
    try:
        code = int(code)
        message = turn_type_map.get(code, "알 수 없는 경로")
        print(f"[{timestamp}] {label}: {message}")
        handle_turn(code)
    except ValueError:
        print(f"[{timestamp}] 잘못된 코드 형식: {code}")

def monitor_log_file():
    print("📡 로그 파일 모니터링 시작...")
    processed = load_processed_lines()
    while True:
        if not os.path.exists(LOG_FILE):
            time.sleep(1)
            continue
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line_id = line.strip()
                if not line_id or line_id in processed:
                    continue
                process_line(line)
                save_processed_line(line)
                processed.add(line_id)
        time.sleep(1)

if __name__ == "__main__":
    monitor_log_file()
