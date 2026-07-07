#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""批量文件夹检测"""

from ultralytics import YOLO

MODEL_PATH = "runs/yolo11s_pretrained/train/weights/best.pt"
FOLDER_PATH = "images/test"

model = YOLO(MODEL_PATH)
model.predict(FOLDER_PATH, save=True, imgsz=640, conf=0.5, save_txt=True, save_conf=False)
