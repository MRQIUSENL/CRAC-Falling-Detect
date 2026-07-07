"""批量推理并导出检测结果为 CSV"""
import os, os.path as osp
import numpy as np
from ultralytics import YOLO


def inference_to_csv(img_dir, model_path, output_csv="result.csv"):
    model = YOLO(model_path)
    rows = []
    for fname in os.listdir(img_dir):
        path = osp.join(img_dir, fname)
        results = model(path)
        r = results[0]
        counts = [0] * len(r.names)
        if r.boxes is not None:
            for cid in r.boxes.cls.cpu().numpy():
                counts[int(cid)] += 1
        rows.append([fname] + counts)
    np.savetxt(output_csv, np.array(rows), fmt="%s", delimiter=",")
    print(f"Saved to {output_csv}")


if __name__ == "__main__":
    inference_to_csv("path/to/images", "yolo11s_pretrained.pt")
