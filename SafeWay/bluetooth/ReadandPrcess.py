import time
import os

LOG_FILE = "received_messages.txt"
PROCESSED_FILE = "processed_lines.txt"

# turnType 메시지 매핑
turn_type_map = {
    **dict.fromkeys(range(1, 8), "안내 없음"),
    11: "직진하세요", 12: "좌회전하세요", 13: "우회전하세요", 14: "U턴하세요",
    16: "8시 방향으로 좌회전하세요", 17: "10시 방향으로 좌회전하세요",
    18: "2시 방향으로 우회전하세요", 19: "4시 방향으로 우회전하세요",
    184: "경유지입니다", 185: "첫 번째 경유지입니다", 186: "두 번째 경유지입니다",
    187: "세 번째 경유지입니다", 188: "네 번째 경유지입니다", 189: "다섯 번째 경유지입니다",
    125: "육교를 이용하세요", 126: "지하보도를 이용하세요", 127: "계단으로 진입하세요",
    128: "경사로로 진입하세요", 129: "계단과 경사로로 진입하세요",
    200: "출발지입니다", 201: "목적지에 도착했습니다",
    211: "횡단보도를 건너세요", 212: "좌측 횡단보도를 건너세요",
    213: "우측 횡단보도를 건너세요", 214: "8시 방향 횡단보도를 건너세요",
    215: "10시 방향 횡단보도를 건너세요", 216: "2시 방향 횡단보도를 건너세요",
    217: "4시 방향 횡단보도를 건너세요", 218: "엘리베이터를 이용하세요",
    233: "직진하세요 (임시)"
}

def load_processed_lines():
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)

def save_processed_line(line):
    with open(PROCESSED_FILE, "a", encoding="utf-8") as f:
        f.write(line.strip() + "\n")

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
    except ValueError:
        print(f"[{timestamp}] 오류: 코드 해석 실패")

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
        time.sleep(1)  # 주기적으로 체크

if __name__ == "__main__":
    monitor_log_file()
