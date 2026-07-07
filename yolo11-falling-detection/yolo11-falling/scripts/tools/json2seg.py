"""LabelMe JSON → YOLO 分割格式转换"""
import json
import os
import glob
import os.path as osp


def labelme_to_yolo_seg(json_dir, output_dir, class_list):
    """将 LabelMe 标注的 JSON 文件转换为 YOLO 分割 TXT 格式"""
    os.makedirs(output_dir, exist_ok=True)

    for json_path in glob.glob(osp.join(json_dir, "*.json")):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        txt_name = osp.basename(json_path).replace(".json", ".txt")
        with open(osp.join(output_dir, txt_name), "w") as out:
            for shape in data["shapes"]:
                cls_id = class_list.index(shape["label"])
                out.write(str(cls_id) + " ")
                for point in shape["points"]:
                    x = point[0] / data["imageWidth"]
                    y = point[1] / data["imageHeight"]
                    out.write(f"{x} {y} ")
                out.write("\n")


if __name__ == "__main__":
    labelme_to_yolo_seg(
        json_dir="path/to/jsons",
        output_dir="path/to/labels",
        class_list=["class1", "class2"]
    )
