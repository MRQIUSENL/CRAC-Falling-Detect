"""将 YOLO 标签类别索引统一改为 0（单类别任务）"""
import os


def reset_class_id(label_dir):
    for fname in os.listdir(label_dir):
        if not fname.endswith(".txt"):
            continue
        path = os.path.join(label_dir, fname)
        with open(path) as f:
            lines = [l.strip().split() for l in f if l.strip()]
        with open(path, "w") as f:
            for parts in lines:
                parts[0] = "0"
                f.write(" ".join(parts) + "\n")


if __name__ == "__main__":
    reset_class_id("path/to/labels/train")
