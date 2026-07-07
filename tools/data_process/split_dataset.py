"""划分训练集/验证集/测试集"""
import os
import random
import numpy as np


def gen_split(anno_dir, val_ratio=0.3, seed=42):
    """从标注目录生成 train/val/test 划分文件"""
    names = [os.path.splitext(n)[0] for n in os.listdir(anno_dir)]
    random.seed(seed)
    random.shuffle(names)

    split = int(len(names) * val_ratio)
    val_names, train_names = names[:split], names[split:]

    np.savetxt("val.txt", np.array(val_names), fmt="%s")
    np.savetxt("test.txt", np.array(val_names), fmt="%s")
    np.savetxt("train.txt", np.array(train_names), fmt="%s")
    print(f"train: {len(train_names)}, val: {len(val_names)}, test: {len(val_names)}")


if __name__ == "__main__":
    gen_split("path/to/Annotations", val_ratio=0.3)
