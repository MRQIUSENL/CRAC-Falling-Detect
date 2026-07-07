#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""SAHI 切片检测 - 图片 (适用于小目标/高分辨率图像)"""

import argparse
from pathlib import Path

import cv2
from sahi import AutoDetectionModel
from sahi.predict import get_sliced_prediction
from sahi.utils.yolov8 import download_yolov8s_model

from ultralytics.utils.files import increment_path
from ultralytics.utils.plotting import Annotator, colors


class SahiInference:
    def __init__(self):
        self.detection_model = None

    def load_model(self, weights):
        yolov8_model_path = f"models/{weights}"
        download_yolov8s_model(yolov8_model_path)
        self.detection_model = AutoDetectionModel.from_pretrained(
            model_type="yolov8", model_path=yolov8_model_path,
            confidence_threshold=0.3, device="cpu"
        )

    def inference(self, weights="yolov8n.pt", source="test.jpg",
                  view_img=False, save_img=False, exist_ok=False):
        save_dir = increment_path(Path("ultralytics_results_with_sahi") / "exp", exist_ok)
        save_dir.mkdir(parents=True, exist_ok=True)
        self.load_model(weights)

        frame = cv2.imread(source)
        annotator = Annotator(frame)
        results = get_sliced_prediction(
            frame, self.detection_model,
            slice_height=512, slice_width=512,
            overlap_height_ratio=0.2, overlap_width_ratio=0.2,
        )
        detection_data = [
            (det.category.name, det.category.id,
             (det.bbox.minx, det.bbox.miny, det.bbox.maxx, det.bbox.maxy))
            for det in results.object_prediction_list
        ]
        for det in detection_data:
            annotator.box_label(det[2], label=str(det[0]),
                              color=colors(int(det[1]), True))
        if view_img:
            cv2.imshow(Path(source).stem, frame)
        if save_img:
            cv2.imwrite(str(save_dir / Path(source).name), frame)

    def parse_opt(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--weights", type=str, default="yolov8n.pt")
        parser.add_argument("--source", type=str, required=True)
        parser.add_argument("--view-img", action="store_true")
        parser.add_argument("--save-img", action="store_true")
        parser.add_argument("--exist-ok", action="store_true")
        return parser.parse_args()


if __name__ == "__main__":
    inference = SahiInference()
    inference.inference(**vars(inference.parse_opt()))
