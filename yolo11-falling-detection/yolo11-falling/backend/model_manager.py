#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
YOLO 模型管理器: 负责模型加载、推理和切换
"""

import os
import time
from typing import Optional, Dict, Any

import cv2
import numpy as np
from ultralytics import YOLO


class ModelManager:
    """管理 YOLO 模型的加载和推理"""

    def __init__(self):
        self.models: Dict[str, YOLO] = {}
        self.current_model_name: str = ""
        self.model_base_dir: str = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "scripts"
        )
        # 自动发现可用的模型文件
        self._discover_models()

    def _discover_models(self):
        """自动发现项目中的模型文件"""
        self.available_models = {}
        # 搜索 scripts 目录下的 .pt 文件
        if os.path.isdir(self.model_base_dir):
            for fname in os.listdir(self.model_base_dir):
                if fname.endswith(".pt"):
                    model_path = os.path.join(self.model_base_dir, fname)
                    self.available_models[fname] = model_path

        # 也搜索 runs 目录
        runs_dir = os.path.join(
            os.path.dirname(self.model_base_dir),
        )
        for root, dirs, files in os.walk(runs_dir):
            for fname in files:
                if fname.endswith(".pt") and "best" in fname.lower():
                    rel_path = os.path.relpath(os.path.join(root, fname), runs_dir)
                    self.available_models[rel_path] = os.path.join(root, fname)

    def get_available_models(self) -> Dict[str, str]:
        """返回可用模型列表"""
        return self.available_models

    def load_model(self, model_name: str) -> bool:
        """
        加载指定模型

        Args:
            model_name: 模型文件名或相对路径

        Returns:
            是否加载成功
        """
        if model_name not in self.available_models:
            # 尝试作为绝对路径加载
            model_path = model_name if os.path.isfile(model_name) else None
            if model_path is None:
                return False
        else:
            model_path = self.available_models[model_name]

        try:
            if model_name not in self.models:
                self.models[model_name] = YOLO(model_path)
            self.current_model_name = model_name
            return True
        except Exception as e:
            print(f"模型加载失败: {e}")
            return False

    def get_current_model(self) -> Optional[YOLO]:
        """获取当前模型"""
        if self.current_model_name and self.current_model_name in self.models:
            return self.models[self.current_model_name]
        return None

    def set_auto_model(self) -> str:
        """自动选择最优模型：优先使用摔倒检测专用模型"""
        # 优先级：yolo11s_pretrained > yolo11n_pretrained > 任意 pretrained/best > 第一个可用
        priority = [
            'scripts/runs/yolo11s_pretrained/train/weights/best.pt',
            'scripts/runs/yolo11n_pretrained/train/weights/best.pt',
        ]
        for name in priority:
            if name in self.available_models:
                self.load_model(name)
                return name
        # 回退到包含 best 的模型
        for name in self.available_models:
            if 'best' in name.lower() and 'pretrained' in name:
                self.load_model(name)
                return name
        # 最后回退到第一个
        if self.available_models:
            first = list(self.available_models.keys())[0]
            self.load_model(first)
            return first
        return ""

    def predict_image(
        self,
        image: np.ndarray,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        imgsz: int = 640,
        tracker_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        对单张图像进行检测

        Args:
            image: OpenCV 格式图像 (BGR)
            conf_threshold: 置信度阈值
            iou_threshold: IoU 阈值
            imgsz: 推理图像大小
            tracker_type: 追踪器类型 (None/"bytetrack.yaml"/"botsort.yaml")

        Returns:
            检测结果字典
        """
        model = self.get_current_model()
        if model is None:
            return {"success": False, "error": "没有加载模型，请先选择模型"}

        t_start = time.time()

        if tracker_type and tracker_type in ("bytetrack.yaml", "botsort.yaml"):
            results = model.track(
                image,
                conf=conf_threshold,
                iou=iou_threshold,
                imgsz=imgsz,
                persist=True,
                tracker=tracker_type
            )
        else:
            results = model(
                image,
                conf=conf_threshold,
                iou=iou_threshold,
                imgsz=imgsz
            )

        t_end = time.time()

        from utils import format_detection_result
        return format_detection_result(results[0], (t_end - t_start) * 1000)


# 全局单例，供其他模块直接引用
model_manager = ModelManager()
