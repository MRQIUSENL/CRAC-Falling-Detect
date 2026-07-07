"""VOC XML 格式 → YOLO TXT 格式转换"""
import os
import os.path as osp
import shutil
from pathlib import Path
from shutil import copyfile
from xml.dom.minidom import parse
import numpy as np


def cord_converter(size, box):
    """VOC bbox → YOLO [x_center, y_center, width, height] (归一化)"""
    dw = 1.0 / int(size[0])
    dh = 1.0 / int(size[1])
    w = box[2] - box[0]
    h = box[3] - box[1]
    x = box[0] + w / 2
    y = box[1] + h / 2
    return [x * dw, w * dw, y * dh, h * dh]


def parse_xml(xml_path):
    """解析单个 VOC XML 标注文件"""
    dom = parse(xml_path)
    root = dom.documentElement
    img_w = root.getElementsByTagName("width")[0].childNodes[0].data
    img_h = root.getElementsByTagName("height")[0].childNodes[0].data
    boxes = []
    for obj in root.getElementsByTagName("object"):
        cls_name = obj.getElementsByTagName("name")[0].childNodes[0].data
        x1 = float(obj.getElementsByTagName("xmin")[0].childNodes[0].data)
        y1 = float(obj.getElementsByTagName("ymin")[0].childNodes[0].data)
        x2 = float(obj.getElementsByTagName("xmax")[0].childNodes[0].data)
        y2 = float(obj.getElementsByTagName("ymax")[0].childNodes[0].data)
        boxes.append([cls_name, x1, y1, x2, y2])
    return [img_w, img_h], boxes


def convert_voc_to_yolo(anno_dir, img_dir, output_dir, class_names):
    """
    批量转换 VOC 格式数据集为 YOLO 格式
    - anno_dir: Annotations 目录 (XML)
    - img_dir: JPEGImages 目录
    - output_dir: 输出根目录
    - class_names: 类别名列表
    """
    labels_dir = osp.join(output_dir, "labels")
    images_dir = osp.join(output_dir, "images")
    os.makedirs(labels_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    for fname in os.listdir(anno_dir):
        if not fname.endswith(".xml"):
            continue
        base = osp.splitext(fname)[0]

        # 转换标注
        size, boxes = parse_xml(osp.join(anno_dir, fname))
        with open(osp.join(labels_dir, f"{base}.txt"), "w") as f:
            for box in boxes:
                if box[0] in class_names:
                    cls_id = class_names.index(box[0])
                    yolo_box = cord_converter(size, box[1:])
                    f.write(f"{cls_id} {' '.join(f'{v:.6f}' for v in yolo_box)}\n")

        # 复制图片
        for ext in [".jpg", ".png", ".jpeg"]:
            img_path = osp.join(img_dir, base + ext)
            if osp.exists(img_path):
                copyfile(img_path, osp.join(images_dir, base + ext))
                break

    print(f"转换完成: {len(os.listdir(labels_dir))} 个标签")


if __name__ == "__main__":
    convert_voc_to_yolo(
        anno_dir="path/to/Annotations",
        img_dir="path/to/JPEGImages",
        output_dir="path/to/yolo_output",
        class_names=["class1", "class2"]
    )
