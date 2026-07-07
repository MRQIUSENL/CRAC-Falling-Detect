#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Gradio Web 检测演示"""

import os
import gradio as gr
import PIL.Image as Image

from ultralytics import ASSETS, YOLO

# 使用脚本所在目录的相对路径，避免从其他目录运行时找不到模型
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
model = YOLO(os.path.join(SCRIPT_DIR, "runs", "yolo11n_pretrained", "train", "weights", "best.pt"))


def predict_image(img, conf_threshold, iou_threshold):
    """使用 YOLO11 模型进行检测，可调节置信度和 IoU 阈值"""
    results = model.predict(
        source=img,
        conf=conf_threshold,
        iou=iou_threshold,
        show_labels=True,
        show_conf=True,
        imgsz=640,
    )
    for r in results:
        im_array = r.plot()
        im = Image.fromarray(im_array[..., ::-1])
    return im


iface = gr.Interface(
    fn=predict_image,
    inputs=[
        gr.Image(type="pil", label="Upload Image"),
        gr.Slider(minimum=0, maximum=1, value=0.25, label="Confidence threshold"),
        gr.Slider(minimum=0, maximum=1, value=0.45, label="IoU threshold"),
    ],
    outputs=gr.Image(type="pil", label="Result"),
    title="YOLO11 摔倒检测系统",
    description="基于 YOLO11 的摔倒检测演示",
)

if __name__ == "__main__":
    iface.launch()
