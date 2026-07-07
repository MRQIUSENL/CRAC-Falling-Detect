#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""性能验证脚本：测试 180 秒内识别 20 张图片，计算评分"""

import os
import random
import time
import argparse
import os.path as osp
from ultralytics import YOLO

SCRIPT_DIR = osp.dirname(osp.abspath(__file__))


def parse_yolo_label(label_path, img_w, img_h):
    """解析 YOLO 格式标签，返回 [(class_id, x1, y1, x2, y2), ...] 像素坐标"""
    boxes = []
    if not osp.exists(label_path):
        return boxes
    with open(label_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            cls_id = int(parts[0])
            cx, cy, w, h = map(float, parts[1:5])
            # 归一化坐标 → 像素坐标
            x1 = (cx - w / 2) * img_w
            y1 = (cy - h / 2) * img_h
            x2 = (cx + w / 2) * img_w
            y2 = (cy + h / 2) * img_h
            boxes.append((cls_id, max(0, x1), max(0, y1), min(img_w, x2), min(img_h, y2)))
    return boxes


def compute_iou(box_a, box_b):
    """计算两个框的 IoU (box: [x1, y1, x2, y2])"""
    xa = max(box_a[0], box_b[0])
    ya = max(box_a[1], box_b[1])
    xb = min(box_a[2], box_b[2])
    yb = min(box_a[3], box_b[3])
    inter = max(0, xb - xa) * max(0, yb - ya)
    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    return inter / (area_a + area_b - inter + 1e-7)


def check_image_correct(gt_boxes, pred_boxes, iou_thr=0.5):
    """
    判定单张图片是否正确
    规则：对每个 GT 框，找到 IoU>iou_thr 且类别一致的预测框匹配
         所有 GT 框都被匹配 → 正确
         若无 GT（空标注），则无预测为正确
    """
    if len(gt_boxes) == 0:
        return len(pred_boxes) == 0

    matched = [False] * len(gt_boxes)
    for pi, (_, px1, py1, px2, py2) in enumerate(pred_boxes):
        best_iou = 0
        best_gi = -1
        for gi, (_, gx1, gy1, gx2, gy2) in enumerate(gt_boxes):
            if matched[gi]:
                continue
            iou = compute_iou((px1, py1, px2, py2), (gx1, gy1, gx2, gy2))
            if iou > best_iou:
                best_iou = iou
                best_gi = gi
        if best_iou >= iou_thr and best_gi >= 0 and pred_boxes[pi][0] == gt_boxes[best_gi][0]:
            matched[best_gi] = True

    return all(matched)


def benchmark(model_path, image_dir, label_dir=None, time_limit=180, target_count=20,
              conf=0.25, iou=0.45, iou_thr=0.5):
    """
    性能基准测试 + 评分
    - model_path   : 模型权重路径
    - image_dir    : 测试图片文件夹
    - label_dir    : 标注文件夹（YOLO 格式，与图片同名 .txt）
    - time_limit   : 时间限制（秒）
    - target_count : 目标识别张数
    - iou_thr      : GT 匹配 IoU 阈值
    """
    CLASS_NAMES = {0: "站立", 1: "摔倒"}
    MAX_SCORE = 35.0           # 最高分
    POINTS_PER_CORRECT = 1.75  # 每正确一张得分
    PENALTY_PER_SECOND = 0.5   # 每秒超时扣分

    # [1] 加载模型
    print(f"[1/5] 加载模型: {model_path}")
    if not osp.isfile(model_path):
        print(f"错误: 模型文件不存在: {model_path}")
        print(f"请通过 --model 指定模型权重路径，例如:")
        print(f"  python benchmark.py --model path/to/best.pt")
        return
    t0 = time.time()
    model = YOLO(model_path)
    print(f"      模型加载耗时: {time.time() - t0:.1f}s")

    # [2] 收集图片
    print(f"[2/5] 扫描图片: {image_dir}")
    if not osp.isdir(image_dir):
        print(f"错误: 图片目录不存在: {image_dir}")
        print(f"请通过 --images 指定测试图片目录，例如:")
        print(f"  python benchmark.py --images path/to/test/images")
        return
    images = []
    for fname in sorted(os.listdir(image_dir)):
        if fname.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            images.append(osp.join(image_dir, fname))
    print(f"      找到 {len(images)} 张图片")

    if len(images) == 0:
        print("错误: 目录中没有图片文件 (.jpg/.png/.bmp)")
        return

    # [3] 预热
    print("[3/5] 预热中...")
    model(images[0], conf=conf, iou=iou, imgsz=640, verbose=False)

    # [4] 正式测试
    print(f"[4/5] 开始测试 (时间限制: {time_limit}s, 目标: {target_count} 张)")
    if label_dir:
        print(f"      标注目录: {label_dir} (IoU阈值: {iou_thr})")
    print("-" * 80)

    start_time = time.time()
    correct_count = 0
    total_inference_time = 0
    details = []

    # 随机抽取 target_count 张图片
    if len(images) >= target_count:
        target_images = random.sample(images, target_count)
    else:
        target_images = images[:]  # 不足则全部使用

    for i, img_path in enumerate(target_images):
        elapsed = time.time() - start_time

        # 读取图片尺寸（用于坐标转换）
        import cv2
        h, w = cv2.imread(img_path).shape[:2]

        # 加载 GT 标注
        gt_boxes = []
        if label_dir:
            label_name = osp.splitext(osp.basename(img_path))[0] + '.txt'
            label_path = osp.join(label_dir, label_name)
            gt_boxes = parse_yolo_label(label_path, w, h)

        # 推理
        t_img = time.time()
        result = model(img_path, conf=conf, iou=iou, imgsz=640, verbose=False)
        img_time = time.time() - t_img
        total_inference_time += img_time

        # 提取预测框
        pred_boxes = []
        boxes_obj = result[0].boxes
        if boxes_obj is not None and len(boxes_obj) > 0:
            for b in boxes_obj:
                cls_id = int(b.cls[0])
                x1, y1, x2, y2 = b.xyxy[0].tolist()
                pred_boxes.append((cls_id, x1, y1, x2, y2))

        # 判定正确性
        is_correct = check_image_correct(gt_boxes, pred_boxes, iou_thr) if gt_boxes else (len(pred_boxes) == 0)
        if is_correct:
            correct_count += 1

        gt_cls_str = ",".join([CLASS_NAMES.get(g[0], str(g[0])) for g in gt_boxes]) if gt_boxes else "无"
        pred_cls_str = ",".join([CLASS_NAMES.get(p[0], str(p[0])) for p in pred_boxes]) if pred_boxes else "无"

        elapsed = time.time() - start_time
        status = "✓" if is_correct else "✗"
        print(f"  [{i+1:2d}] {osp.basename(img_path):30s}  "
              f"{img_time*1000:5.0f}ms  GT:{gt_cls_str:8s}  Pred:{pred_cls_str:8s}  "
              f"{status}  累计: {elapsed:.1f}s")

        details.append({
            "index": i + 1,
            "file": osp.basename(img_path),
            "time_ms": round(img_time * 1000, 1),
            "gt_class": gt_cls_str,
            "pred_class": pred_cls_str,
            "correct": is_correct
        })

    total_elapsed = time.time() - start_time

    # [5] 计算得分
    raw_score = correct_count * POINTS_PER_CORRECT
    overtime = max(0, total_elapsed - time_limit)
    penalty = overtime * PENALTY_PER_SECOND
    final_score = max(0, raw_score - penalty)

    # 结果汇总
    print("-" * 80)
    print()
    print("=" * 60)
    print("  测试结果")
    print("=" * 60)
    print(f"  时间限制        : {time_limit}s")
    print(f"  测试图片数      : {len(target_images)} 张")
    print(f"  总耗时          : {total_elapsed:.1f}s")
    print(f"  超时            : {overtime:.1f}s")
    print(f"  平均推理时间    : {total_inference_time/max(len(target_images),1)*1000:.1f}ms/张")
    print(f"  最快            : {min(r['time_ms'] for r in details):.0f}ms")
    print(f"  最慢            : {max(r['time_ms'] for r in details):.0f}ms")
    print()
    print(f"  --- 评分 ---")
    print(f"  正确张数        : {correct_count}/{len(target_images)}")
    print(f"  基础得分        : {correct_count} x {POINTS_PER_CORRECT} = {raw_score:.2f}")
    if overtime > 0:
        print(f"  超时扣分        : {overtime:.1f}s x {PENALTY_PER_SECOND} = -{penalty:.2f}")
    print(f"  最终得分        : {final_score:.2f} / {MAX_SCORE}")
    print()

    # 评级
    if final_score >= 30:
        grade = "S 优秀"
    elif final_score >= 25:
        grade = "A 良好"
    elif final_score >= 20:
        grade = "B 一般"
    elif final_score >= 10:
        grade = "C 较差"
    else:
        grade = "D 不合格"

    print(f"  评级            : {grade}")
    print("=" * 60)

    return {"score": final_score, "max_score": MAX_SCORE, "grade": grade,
            "correct": correct_count, "total": len(target_images),
            "elapsed": total_elapsed, "details": details}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YOLO11 摔倒检测性能验证 + 评分")
    parser.add_argument("--model", default=osp.join(SCRIPT_DIR, "runs", "yolo11n_pretrained", "train", "weights", "best.pt"),
                        help="模型权重路径")
    parser.add_argument("--images", default=osp.normpath(osp.join(SCRIPT_DIR, "..", "falling_data", "images", "test")),
                        help="测试图片文件夹")
    parser.add_argument("--labels", default=osp.normpath(osp.join(SCRIPT_DIR, "..", "falling_data", "labels", "test")),
                        help="标注文件夹 (YOLO 格式)")
    parser.add_argument("--time-limit", type=int, default=180, help="时间限制（秒）")
    parser.add_argument("--target", type=int, default=20, help="测试图片张数")
    parser.add_argument("--conf", type=float, default=0.25, help="置信度阈值")
    parser.add_argument("--iou", type=float, default=0.45, help="NMS IoU 阈值")
    parser.add_argument("--iou-thr", type=float, default=0.5, help="GT 匹配 IoU 阈值")
    args = parser.parse_args()

    benchmark(args.model, args.images, args.labels, args.time_limit, args.target,
              args.conf, args.iou, args.iou_thr)
