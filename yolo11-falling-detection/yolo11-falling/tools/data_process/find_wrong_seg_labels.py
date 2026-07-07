"""检测并移除 YOLO 标注中的目标检测框（保留分割标注）"""
import os


def find_bbox_labels(anno_dir):
    """找出所有目标检测标注（5元素）对应的图片名"""
    bbox_imgs = []
    for fname in os.listdir(anno_dir):
        if not fname.endswith(".txt"):
            continue
        with open(os.path.join(anno_dir, fname)) as f:
            for line in f:
                if len(line.strip().split()) == 5:
                    bbox_imgs.append(fname.replace(".txt", ".jpg"))
                    break
    return bbox_imgs


if __name__ == "__main__":
    anno_dir = "path/to/labels"
    bbox_imgs = find_bbox_labels(anno_dir)
    print(f"Found {len(bbox_imgs)} bbox images")
