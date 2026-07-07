#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""摄像头/视频文件实时检测"""

import cv2
from ultralytics import YOLO

model = YOLO("runs/yolo11s_pretrained/train/weights/best.pt")

# 可替换为摄像头: cv2.VideoCapture(0)
cap = cv2.VideoCapture("images/resources/demo.mp4")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    results = model(frame)
    annotated_frame = results[0].plot()
    cv2.imshow("YOLO11 Detection", annotated_frame)

    if cv2.waitKey(10) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
