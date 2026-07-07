"""LabelMe JSON → YOLO TXT 批量转换 (含 train/val 划分)"""
import os, json, shutil, glob
import yaml
from sklearn.model_selection import train_test_split


def labelme_to_yolo(json_path, output_path, class_map, img_w, img_h):
    """单文件转换：LabelMe JSON → YOLO TXT"""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    with open(output_path, "w") as out:
        for shape in data["shapes"]:
            cid = class_map.get(shape["label"])
            if cid is None:
                continue
            xs = [p[0] for p in shape["points"]]
            ys = [p[1] for p in shape["points"]]
            xc = sum(xs) / len(xs) / img_w
            yc = sum(ys) / len(ys) / img_h
            w = (max(xs) - min(xs)) / img_w
            h = (max(ys) - min(ys)) / img_h
            out.write(f"{cid} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")


def convert_dataset(json_dir, img_dir, output_dir, class_map, test_size=0.2):
    """批量转换 + 划分 train/val + 生成 data.yaml"""
    json_files = glob.glob(os.path.join(json_dir, "*.json"))
    train_files, val_files = train_test_split(json_files, test_size=test_size, random_state=42)

    for phase, files in [("train", train_files), ("val", val_files)]:
        lbl_dir = os.path.join(output_dir, phase, "labels")
        img_out = os.path.join(output_dir, phase, "images")
        os.makedirs(lbl_dir, exist_ok=True)
        os.makedirs(img_out, exist_ok=True)
        for jf in files:
            base = os.path.splitext(os.path.basename(jf))[0]
            # 复制原图
            for ext in [".jpg", ".png"]:
                src_img = os.path.join(img_dir, base + ext)
                if os.path.exists(src_img):
                    shutil.copy(src_img, os.path.join(img_out, base + ext))
                    break
            # 转换标注
            with open(jf, encoding="utf-8") as f:
                data = json.load(f)
            labelme_to_yolo(jf, os.path.join(lbl_dir, base + ".txt"),
                           class_map, data["imageWidth"], data["imageHeight"])

    # 生成 data.yaml
    yaml_path = os.path.join(output_dir, "data.yaml")
    with open(yaml_path, "w") as f:
        yaml.safe_dump({
            "train": os.path.abspath(os.path.join(output_dir, "train", "images")),
            "val": os.path.abspath(os.path.join(output_dir, "val", "images")),
            "nc": len(class_map),
            "names": list(class_map.keys())
        }, f, allow_unicode=True)
    print(f"完成: {yaml_path}")


if __name__ == "__main__":
    convert_dataset(
        json_dir="path/to/jsons",
        img_dir="path/to/images",
        output_dir="output_dataset",
        class_map={"class_a": 0, "class_b": 1}
    )
