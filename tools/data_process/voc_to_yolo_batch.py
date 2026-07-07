"""VOC XML → YOLO 格式批量转换 (含 train/val/test 划分)"""
import os
import os.path as osp
import shutil
from pathlib import Path
from shutil import copyfile
import numpy as np
from xml.dom.minidom import parse


def cord_converter(size, box):
    """VOC bbox → YOLO 归一化坐标"""
    dw, dh = 1.0 / int(size[0]), 1.0 / int(size[1])
    w, h = box[2] - box[0], box[3] - box[1]
    x, y = box[0] + w / 2, box[1] + h / 2
    return [x * dw, w * dw, y * dh, h * dh]


def parse_xml(xml_path):
    """解析 VOC XML 标注"""
    dom = parse(xml_path)
    root = dom.documentElement
    size = root.getElementsByTagName("size")[0]
    w = size.getElementsByTagName("width")[0].childNodes[0].data
    h = size.getElementsByTagName("height")[0].childNodes[0].data
    boxes = []
    for obj in root.getElementsByTagName("object"):
        name = obj.getElementsByTagName("name")[0].childNodes[0].data
        x1 = float(obj.getElementsByTagName("xmin")[0].childNodes[0].data)
        y1 = float(obj.getElementsByTagName("ymin")[0].childNodes[0].data)
        x2 = float(obj.getElementsByTagName("xmax")[0].childNodes[0].data)
        y2 = float(obj.getElementsByTagName("ymax")[0].childNodes[0].data)
        boxes.append([name, x1, y1, x2, y2])
    return [w, h], boxes


def convert_dataset(anno_dir, img_dir, output_dir, class_names):
    """批量转换 VOC → YOLO，按 train/val/test 划分"""
    labels_root = osp.join(output_dir, "Labels")
    os.makedirs(labels_root, exist_ok=True)

    for fname in os.listdir(anno_dir):
        if not fname.endswith(".xml"):
            continue
        base = osp.splitext(fname)[0]
        size, boxes = parse_xml(osp.join(anno_dir, fname))
        with open(osp.join(labels_root, f"{base}.txt"), "w") as f:
            for box in boxes:
                if box[0] in class_names:
                    cid = class_names.index(box[0])
                    yb = cord_converter(size, box[1:])
                    f.write(f"{cid} {' '.join(f'{v:.6f}' for v in yb)}\n")

    # 按 train/val/test 划分并复制
    main_dir = osp.join(output_dir, "Main")
    for split in ["train", "val", "test"]:
        split_file = osp.join(main_dir, f"{split}.txt")
        if not osp.exists(split_file):
            continue
        img_dst = osp.join(output_dir, "images", split)
        lbl_dst = osp.join(output_dir, "labels", split)
        os.makedirs(img_dst, exist_ok=True)
        os.makedirs(lbl_dst, exist_ok=True)
        with open(split_file) as f:
            for name in f:
                name = name.strip()
                for ext in [".jpg", ".png"]:
                    src_img = osp.join(img_dir, name + ext)
                    if osp.exists(src_img):
                        copyfile(src_img, osp.join(img_dst, name + ext))
                        break
                src_lbl = osp.join(labels_root, name + ".txt")
                if osp.exists(src_lbl):
                    copyfile(src_lbl, osp.join(lbl_dst, name + ".txt"))

    print("数据转换完成")


if __name__ == "__main__":
    convert_dataset(
        anno_dir="path/to/Annotations",
        img_dir="path/to/JPEGImages",
        output_dir="path/to/output",
        class_names=["class1", "class2"]
    )
