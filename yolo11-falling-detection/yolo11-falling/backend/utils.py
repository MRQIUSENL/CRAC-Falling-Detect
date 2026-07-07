#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
工具函数: 图像处理、base64编解码等
"""

import base64
import io
import time
from typing import Tuple, Optional

import cv2
import numpy as np
from PIL import Image


def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
    """将 PIL Image 转换为 OpenCV 格式 (BGR)"""
    rgb = np.array(pil_image)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    return bgr


def cv2_to_base64(cv2_image: np.ndarray, quality: int = 85) -> str:
    """将 OpenCV 图像转换为 base64 字符串 (JPEG 格式)"""
    # BGR -> RGB
    rgb = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=quality)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def base64_to_cv2(b64_string: str) -> np.ndarray:
    """将 base64 字符串转换为 OpenCV 图像"""
    # 去掉可能的 data:image/...;base64, 前缀
    if "," in b64_string:
        b64_string = b64_string.split(",")[1]
    img_bytes = base64.b64decode(b64_string)
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img


def resize_image(img: np.ndarray, max_size: int = 1280) -> np.ndarray:
    """按比例缩放图像，长边不超过 max_size"""
    h, w = img.shape[:2]
    if max(h, w) > max_size:
        scale = max_size / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        img = cv2.resize(img, (new_w, new_h))
    return img


def format_detection_result(result, inference_time_ms: float) -> dict:
    """
    将 YOLO 推理结果格式化为统一的 API 返回格式

    Args:
        result: ultralytics Results 对象
        inference_time_ms: 推理耗时(毫秒)

    Returns:
        格式化后的字典
    """
    detections = []
    counts = {}

    if result.boxes is not None and len(result.boxes) > 0:
        boxes = result.boxes.xyxy.cpu().numpy()
        confs = result.boxes.conf.cpu().numpy()
        cls_ids = result.boxes.cls.cpu().numpy().astype(int)
        names = result.names

        for i in range(len(boxes)):
            cls_id = int(cls_ids[i])
            cls_name = names.get(cls_id, f"class_{cls_id}")
            detections.append({
                "class": cls_name,
                "class_id": cls_id,
                "confidence": round(float(confs[i]), 4),
                "bbox": [round(float(x), 2) for x in boxes[i]]
            })
            counts[cls_name] = counts.get(cls_name, 0) + 1

    # 生成标注图像
    annotated_img = result.plot()
    annotated_b64 = cv2_to_base64(annotated_img)

    return {
        "success": True,
        "detections": detections,
        "counts": counts,
        "total_objects": len(detections),
        "annotated_image": annotated_b64,
        "inference_time_ms": round(inference_time_ms, 2)
    }
