"""批量大图切片 - 遍历文件夹中所有图片+JSON执行切片"""
import os
import os.path as osp
from main import process


def batch_process(src_dir, dst_dir, slice_size=1024, stride=300):
    """遍历 src_dir 中所有 .JPG + .json 对，逐一执行切片"""
    for fname in os.listdir(src_dir):
        if not fname.endswith(".JPG"):
            continue
        prefix = osp.splitext(fname)[0]
        img_path = osp.join(src_dir, fname)
        json_path = osp.join(src_dir, prefix + ".json")
        out_dir = osp.join(dst_dir, "output_" + prefix)
        if osp.exists(json_path):
            print(f"Processing: {prefix}")
            process(img_path, json_path, out_dir, prefix, slice_size, stride)


if __name__ == "__main__":
    batch_process("path/to/src", "path/to/output", slice_size=1024, stride=300)
