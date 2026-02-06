import cv2
import numpy as np
from PIL import Image

#from google.colab.patches import cv2_imshow

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision.datasets import Cityscapes
from torchvision import transforms
import numpy as np
import matplotlib.pyplot as plt
import os
import haptic
import time
from camera import Camera

import time

retry_limit = 5   # 재시도 최대 횟수
retry_delay = 3   # 재시도 간격 (초)

def reconnect_camera(cap, retry_limit=5, retry_delay=3):
    for i in range(retry_limit):
        print(f"📷 카메라 재연결 시도 {i+1}/{retry_limit}...")
        cap.release()
        cap.open(0)
        if cap.isOpened():
            print("✅ 카메라 재연결 성공")
            return True
        time.sleep(retry_delay)
    print("❌ 카메라 재연결 실패")
    return False


class LearningToDownsample(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Sequential(
            nn.Conv2d(3, 32, 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True)
        )
        self.conv2 = nn.Sequential(
            nn.Conv2d(32, 48, 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(48),
            nn.ReLU(inplace=True)
        )
        self.conv3 = nn.Sequential(
            nn.Conv2d(48, 64, 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.conv3(self.conv2(self.conv1(x)))

class GlobalFeatureExtractor(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(64, 128, 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, 3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.conv(x)

class FeatureFusion(nn.Module):
    def __init__(self):
        super().__init__()
        self.low_res = nn.Conv2d(128, 128, 1, bias=False)
        self.high_res = nn.Conv2d(64, 128, 1, bias=False)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, high, low):
        low_up = F.interpolate(self.low_res(low), size=high.size()[2:], mode='bilinear', align_corners=True)
        high = self.high_res(high)
        return self.relu(high + low_up)

class Classifier(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(128, 128, 3, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.1),
            nn.Conv2d(128, num_classes, 1)
        )

    def forward(self, x):
        return self.conv(x)

class FastSCNN(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.downsample = LearningToDownsample()
        self.global_feature = GlobalFeatureExtractor()
        self.fusion = FeatureFusion()
        self.classifier = Classifier(num_classes)

    def forward(self, x):
        size = x.size()[2:]
        higher = self.downsample(x)
        lower = self.global_feature(higher)
        fused = self.fusion(higher, lower)
        out = self.classifier(fused)
        return F.interpolate(out, size=size, mode='bilinear', align_corners=True)


def draw_trapezoid_split_sectors(frame, color=(0, 255, 0), thickness=2):
    h, w, _ = frame.shape

    y_top = int(h * 2 / 3)    # 탑라인 위치 (2/3 지점)
    y_bottom = h              # 바닥

    # 사다리꼴 전체 너비
    top_width = int(w * 0.3)
    bottom_width = int(w * 0.9)
    center_x = w // 2

    # 꼭짓점 계산
    top_left = (center_x - top_width // 2, y_top)
    top_right = (center_x + top_width // 2, y_top)
    bottom_left = (center_x - bottom_width // 2, y_bottom)
    bottom_right = (center_x + bottom_width // 2, y_bottom)

    def interp(p1, p2, t):
        x = int(p1[0] + (p2[0] - p1[0]) * t)
        y = int(p1[1] + (p2[1] - p1[1]) * t)
        return (x, y)

    # 분할점 (1/3, 2/3)
    top_1_3 = interp(top_left, top_right, 1/3)
    top_2_3 = interp(top_left, top_right, 2/3)
    bottom_1_3 = interp(bottom_left, bottom_right, 1/3)
    bottom_2_3 = interp(bottom_left, bottom_right, 2/3)

    # === LEFT 섹터 ===
    left_pts = np.array([top_left, top_1_3, bottom_1_3, bottom_left], np.int32)
    cv2.polylines(frame, [left_pts], isClosed=True, color=color, thickness=thickness)

    # === CENTER 섹터 ===
    center_pts = np.array([top_1_3, top_2_3, bottom_2_3, bottom_1_3], np.int32)
    cv2.polylines(frame, [center_pts], isClosed=True, color=color, thickness=thickness)

    # === RIGHT 섹터 ===
    right_pts = np.array([top_2_3, top_right, bottom_right, bottom_2_3], np.int32)
    cv2.polylines(frame, [right_pts], isClosed=True, color=color, thickness=thickness)

    return frame

# 전처리
input_size = (256, 512)
transform = transforms.Compose([
    transforms.Resize(input_size),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

# Cityscapes 색상
CITYSCAPES_COLORS = np.array([
    [128, 64,128], [244, 35,232], [ 70, 70, 70], [102,102,156],
    [190,153,153], [153,153,153], [250,170, 30], [220,220,  0],
    [107,142, 35], [152,251,152], [ 70,130,180], [220, 20, 60],
    [255,  0,  0], [  0,  0,142], [  0,  0, 70], [  0, 60,100],
    [  0, 80,100], [  0,  0,230], [119, 11, 32]
], dtype=np.uint8)

def decode_segmap(mask):
    return CITYSCAPES_COLORS[mask]




def compute_avoidance_amplitude_avg(seg_maps,
                                    obstacle_classes=None,
                                    m_threshold=0.10,  # 비율 (0.0 ~ 1.0)
                                    side_threshold=0.05):
    """
    중앙 위험도 '비율' 기준 넘을 때만 → 양쪽 섹터의 위험 분포에 따라 진동 결정

    Args:
        m_threshold: 중앙 섹터의 위험 비율 (0~1), 예: 0.15 = 15% 이상 위험해야 진동
        side_threshold: 좌우 섹터 위험 비율 총합 기준 (비율로 처리)

    Returns:
        (left_level, right_level): int (0: 없음, 1: 강함 ~ 6: 약함)
    """
    if not seg_maps:
        return 0, 0

    H, W = seg_maps[0].shape
    rois = [seg[H//2:, :] for seg in seg_maps]
    roi_H, roi_W = rois[0].shape

    if obstacle_classes is None:
        obstacle_classes = set(range(19)) - {0, 1, 2, 3, 6, 7, 9, 10} # 0:도로, 1:인도, 6:신호등, 7:교통표지판, 10:하늘, 9: 흙언덕 3:벽, 2:건물

    masks = [np.isin(roi, list(obstacle_classes)).astype(np.float32) for roi in rois]
    avg_mask = np.mean(np.stack(masks), axis=0)

    vertical_weights = np.linspace(0.1, 1.0, roi_H).reshape(roi_H, 1)
    weighted_mask = avg_mask * vertical_weights

    pillar_width = int(roi_W * 0.15)
    centers = [int(roi_W * 0.25), int(roi_W * 0.5), int(roi_W * 0.75)]

    def get_sector(cx):
        x1 = max(cx - pillar_width // 2, 0)
        x2 = min(cx + pillar_width // 2, roi_W)
        return weighted_mask[:, x1:x2]

    left_sector = get_sector(centers[0])
    center_sector = get_sector(centers[1])
    right_sector = get_sector(centers[2])

    left_sum = np.sum(left_sector)
    center_sum = np.sum(center_sector)
    right_sum = np.sum(right_sector)

    center_area = center_sector.size	
    left_area = left_sector.size
    right_area = right_sector.size

    center_ratio = center_sum / (center_area + 1e-6)
    total_side_ratio = (left_sum + right_sum) / (left_area + right_area + 1e-6)

    # ✅ 중앙 위험 비율이 낮으면 진동 없음
    if center_ratio < m_threshold:
        return 0, 0

    # ✅ 좌우 섹터도 일정 수준 이상 위험해야 진동 발생
    if total_side_ratio < side_threshold:
        return 0, 0

    # 좌우 비율
    left_ratio = left_sum / (left_sum + right_sum + 1e-6)
    right_ratio = right_sum / (left_sum + right_sum + 1e-6)
	# 진동 세기가 큰 쪽으로 회피
    def ratio_to_level(r):
        if r >= 0.6:
            return 1            # 1
        elif r >= 0.4:
            return 2            # 2
        elif r >= 0.25:
            return 3            # 3
        elif r >= 0.15:
            return 4            # 4
        elif r >= 0.05:
            return 5            # 5
        else:
            return 6

    right_level = ratio_to_level(right_ratio)
    left_level = ratio_to_level(left_ratio)

    return left_level, right_level
    




# ✅ 모델 로드
device = torch.device("cpu")
model = FastSCNN(num_classes=19).to(device)
model.load_state_dict(torch.load("/home/safeway/Smart_Cane_Project/fast_scnn_cityscapes_full.pth", map_location="cpu"))
model.eval()

# === 비디오 읽기 & 저장 ===
cap = cv2.VideoCapture(0)
#cap = cv2.VideoCapture("/home/safeway/Smart_Cane_Project/test_cut_plant.mp4")
fps = cap.get(cv2.CAP_PROP_FPS)
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

savr_path ="/home/safeway/test_result/camera_inference_v4.mp4"

out = cv2.VideoWriter(savr_path,
                      cv2.VideoWriter_fourcc(*'mp4v'),
                      fps,
                      (w, h))

frame_idx = 0
seg_history = []
n_frames = 2  # 사용할 프레임 수
left_level, right_level = 0, 0  # int 레벨로 초기화

# === 메인 루프 ===
while cap.isOpened():
    ret, frame = cap.read()
    #if not ret or frame_idx >= 3000:        # 최대 3000프레임
    if not ret:
        print("⚠️ 프레임을 읽지 못했습니다. 재연결 시도...")
        if not reconnect_camera(cap, retry_limit=100, retry_delay=3):
            print("🚫 프로그램 종료: 카메라 연결 실패")
            break
        continue  # 재연결 후 다시 루프
    haptic.init_all()

    # 전처리 & 추론
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    input_tensor = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        output = model(input_tensor)
        seg_map = torch.argmax(output.squeeze(), dim=0).cpu().numpy()
        seg_history.append(seg_map)

    # 회피기동 계산 (n프레임 평균 기반, 정수 레벨 리턴)
    if len(seg_history) >= n_frames:
        left_level, right_level = compute_avoidance_amplitude_avg(seg_history[-n_frames:])
        # 진동 실행
        def get_value(level):
            if level == 6:
                return 47
            elif level in (4, 5):
                return 2
            elif level == 3:
                return 4
            elif level in (1, 2):
                return 6
            else:  # level == 0
                return 0

        left = get_value(left_level)
        right = get_value(right_level)
        haptic.vibrate(left_level=right, right_level=left)
        

    # 색상 시각화
    seg_color = CITYSCAPES_COLORS[seg_map]
    
    seg_color = cv2.cvtColor(seg_color, cv2.COLOR_RGB2BGR)
    seg_color = cv2.resize(seg_color, (w, h))

    blended = cv2.addWeighted(frame, 0.5, seg_color, 0.5, 0)
    blended = draw_trapezoid_split_sectors(blended)

    # 텍스트로 진동 레벨 출력
    cv2.putText(blended, f"LEFT LEVEL: {right_level}", (30, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(blended, f"RIGHT LEVEL: {left_level}", (30, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    out.write(blended)
    
    cv2.imshow('segmentation', blended)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

	
    frame_idx += 1

cap.release()
cv2.destroyAllWindows()
# out.release()

# print(f"✅ 완료: {savr_path}")


