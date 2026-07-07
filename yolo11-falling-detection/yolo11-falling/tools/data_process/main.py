"""大图切片工具 - LabelMe JSON 标注 + 图片按滑窗切分为子图"""
import json, os, base64
from io import BytesIO
import cv2
import numpy as np
from PIL import Image


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def img_to_base64(img):
    pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    buf = BytesIO()
    pil.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def pad_to_multiple(img, mask, size):
    """填充到切片大小的整数倍"""
    h, w = img.shape[:2]
    ph = (size - h % size) % size
    pw = (size - w % size) % size
    img = cv2.copyMakeBorder(img, 0, ph, 0, pw, cv2.BORDER_CONSTANT, value=[0, 0, 0])
    mask = cv2.copyMakeBorder(mask, 0, ph, 0, pw, cv2.BORDER_CONSTANT, value=0)
    return img, mask


def slice_image_mask(img, mask, size, stride):
    """滑窗切片"""
    slices = []
    h, w = img.shape[:2]
    for y in range(0, h - size + 1, stride):
        for x in range(0, w - size + 1, stride):
            slices.append((img[y:y+size, x:x+size], mask[y:y+size, x:x+size], x, y))
    return slices


def mask_to_shapes(mask, class_map):
    """uint16 mask → LabelMe shapes"""
    shapes = []
    for cls_id in np.unique(mask):
        if cls_id == 0:
            continue
        cls_mask = (mask == cls_id).astype(np.uint8) * 255
        contours, _ = cv2.findContours(cls_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            shapes.append({
                "label": class_map[cls_id],
                "points": [[float(p[0][0]), float(p[0][1])] for p in cnt],
                "group_id": None, "shape_type": "polygon", "flags": {}
            })
    return shapes


def process(input_img, input_json, output_dir, prefix="slice", slice_size=1024, stride=300):
    """主流程：读取大图 + JSON → 输出子图 + 子标注"""
    os.makedirs(output_dir, exist_ok=True)
    img = cv2.imread(input_img)
    data = load_json(input_json)
    h, w = img.shape[:2]

    # 生成 uint16 mask
    mask = np.zeros((h, w), dtype=np.uint16)
    class_map = {}
    for i, shape in enumerate(data["shapes"], 1):
        pts = np.array(shape["points"], dtype=np.int32)
        class_map[i] = shape["label"]
        cv2.fillPoly(mask, [pts], i)

    img, mask = pad_to_multiple(img, mask, slice_size)
    for i, (im_slice, mk_slice, _, _) in enumerate(slice_image_mask(img, mask, slice_size, stride)):
        cv2.imwrite(os.path.join(output_dir, f"{prefix}_{i}.png"), im_slice)
        result = data.copy()
        result["shapes"] = mask_to_shapes(mk_slice, class_map)
        result["imagePath"] = f"{prefix}_{i}.png"
        result["imageData"] = img_to_base64(im_slice)
        result["imageWidth"] = im_slice.shape[1]
        result["imageHeight"] = im_slice.shape[0]
        save_json(result, os.path.join(output_dir, f"{prefix}_{i}.json"))


if __name__ == "__main__":
    process("data/IMG_1046.JPG", "data/IMG_1046.json", "output_IMG_1046", slice_size=1024, stride=300)
