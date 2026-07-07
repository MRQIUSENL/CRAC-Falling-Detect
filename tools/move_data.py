"""将子文件夹内所有文件合并到目标文件夹"""
import os, os.path as osp, shutil


def flatten_copy(src_dir, dst_dir):
    """递归复制 src_dir 下所有文件到 dst_dir"""
    os.makedirs(dst_dir, exist_ok=True)
    for root, _, files in os.walk(src_dir):
        for fname in files:
            shutil.copy2(osp.join(root, fname), dst_dir)


if __name__ == "__main__":
    flatten_copy("path/to/src", "path/to/dst")
