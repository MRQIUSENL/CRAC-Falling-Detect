"""批量重命名图片（支持中文路径）"""
import os
import os.path as osp
import cv2
import numpy as np


def cv_imread_chinese(path):
    """读取中文路径图片"""
    return cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)


def batch_rename(src_dir, dst_dir, prefix="img"):
    """将源目录图片批量重命名为 prefix_0.jpg, prefix_1.jpg ..."""
    os.makedirs(dst_dir, exist_ok=True)
    for i, name in enumerate(os.listdir(src_dir)):
        src_path = osp.join(src_dir, name)
        dst_path = osp.join(dst_dir, f"{prefix}_{i}.jpg")
        cv2.imwrite(dst_path, cv_imread_chinese(src_path))


if __name__ == "__main__":
    batch_rename("path/to/src", "path/to/dst", prefix="img")
