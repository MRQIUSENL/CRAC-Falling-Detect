#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""单张图片检测"""

from ultralytics import YOLO

# 加载模型
model = YOLO("runs/yolo11s_pretrained/train/weights/best.pt")

# 单张图片检测
results = model("images/resources/demo.jpg")

# 显示并保存结果
for result in results:
    result.show()
    result.save(filename="images/resources/result.jpg")
