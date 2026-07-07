#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""模型验证：计算 mAP、Precision、Recall 等指标"""

from ultralytics import YOLO

model = YOLO("runs/yolo11s_pretrained/train/weights/best.pt")
model.val(data='A_my_data.yaml', imgsz=640, batch=4, conf=0.25, iou=0.6, device="0", workers=0)
