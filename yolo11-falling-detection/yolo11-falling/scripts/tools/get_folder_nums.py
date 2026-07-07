"""统计文件夹内文件数量"""
import os


def count_files(root_dir):
    """递归统计每个子文件夹的文件数量"""
    for sub in sorted(os.listdir(root_dir)):
        sub_path = os.path.join(root_dir, sub)
        if os.path.isdir(sub_path):
            print(f"{sub}: {len(os.listdir(sub_path))}")


if __name__ == "__main__":
    count_files("path/to/dataset")
