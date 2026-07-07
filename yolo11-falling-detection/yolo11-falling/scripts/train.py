#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""模型训练：使用 YOLO11 多个架构进行对比训练"""

import time
from ultralytics import YOLO

# ==================== 训练参数 ====================
DATA_CONFIG_PATH = 'A_my_data.yaml'
EPOCHS = 100
IMAGE_SIZE = 640
DEVICE = []
WORKERS = 0
BATCH = 4
CACHE = True
AMP = False

# ==================== 基础模型训练 ====================

# YOLO11n
model = YOLO("yolo11n.yaml").load("yolo11n.pt")
model.train(data=DATA_CONFIG_PATH, project="./runs/yolo11n_pretrained",
            epochs=EPOCHS, imgsz=IMAGE_SIZE, device=DEVICE,
            workers=WORKERS, batch=BATCH, cache=CACHE, amp=AMP)
time.sleep(10)

# YOLO11s
model = YOLO("yolo11s.yaml").load("yolo11s.pt")
model.train(data=DATA_CONFIG_PATH, project="./runs/yolo11s_pretrained",
            epochs=EPOCHS, imgsz=IMAGE_SIZE, device=DEVICE,
            workers=WORKERS, batch=BATCH, cache=CACHE, amp=AMP)
time.sleep(10)

# YOLOv5n
model = YOLO("yolov5n.yaml").load("yolov5n.pt")
model.train(data=DATA_CONFIG_PATH, project="./runs/yolov5n_pretrained",
            epochs=EPOCHS, imgsz=IMAGE_SIZE, device=DEVICE,
            workers=WORKERS, batch=BATCH, cache=CACHE, amp=AMP)
time.sleep(10)

# YOLOv8n
model = YOLO("yolov8n.yaml").load("yolov8n.pt")
model.train(data=DATA_CONFIG_PATH, project="./runs/yolov8n_pretrained",
            epochs=EPOCHS, imgsz=IMAGE_SIZE, device=DEVICE,
            workers=WORKERS, batch=BATCH, cache=CACHE, amp=AMP)
time.sleep(10)

# ==================== 消融实验 ====================

# 原始 YOLO11n (无预训练权重)
model = YOLO("yolo11n.yaml")
model.train(data=DATA_CONFIG_PATH, project="./runs/yolo11n_src",
            epochs=EPOCHS, imgsz=IMAGE_SIZE, device=DEVICE,
            workers=WORKERS, batch=BATCH, cache=CACHE, amp=AMP)
time.sleep(10)

# YOLO11n + CBAM 注意力机制
model = YOLO("yolo11n-cbam.yaml")
model.train(data=DATA_CONFIG_PATH, project="./runs/yolo11n-cbam",
            epochs=EPOCHS, imgsz=IMAGE_SIZE, device=DEVICE,
            workers=WORKERS, batch=BATCH, cache=CACHE, amp=AMP)
time.sleep(10)

# YOLO11n + GhostConv 轻量化
model = YOLO("yolo11n-GhostConv.yaml")
model.train(data=DATA_CONFIG_PATH, project="./runs/yolo11n-GhostConv",
            epochs=EPOCHS, imgsz=IMAGE_SIZE, device=DEVICE,
            workers=WORKERS, batch=BATCH, cache=CACHE, amp=AMP)
time.sleep(10)
