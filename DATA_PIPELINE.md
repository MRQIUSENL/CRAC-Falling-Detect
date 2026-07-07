# 数据采集与处理管线文档

> 本文档详细阐述 YOLO11 摔倒检测系统中数据采集、标注、格式转换、预处理和数据集管理的完整管线设计与各模块实现原理。

---

## 一、数据流转全景

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         数据采集与处理管线                                │
│                                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────────────┐  │
│  │ 1.数据源 │───▶│ 2.预处理 │───▶│ 3.标注   │───▶│ 4.格式转换       │  │
│  └──────────┘    └──────────┘    └──────────┘    └────────┬─────────┘  │
│                                                           │            │
│  ·监控摄像头     ·视频抽帧      ·LabelMe      ·VOC XML → YOLO TXT       │
│  ·手机拍摄       ·批量重命名    ·VOC XML      ·LabelMe JSON → YOLO TXT   │
│  ·公开数据集     ·大图切片      ·自动分割      ·类别索引统一             │
│  ·网络爬虫       ·去重清洗                                    │            │
│                                                    ▼            │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                        5. 数据集管理                             │   │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐   │   │
│  │  │ 训练集   │    │ 验证集   │    │ 测试集   │    │ data.yaml│   │   │
│  │  │ 70%      │    │ 20%      │    │ 10%      │    │ 配置文件 │   │   │
│  │  └──────────┘    └──────────┘    └──────────┘    └──────────┘   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                   6. 训练 & 推理                                  │   │
│  │  train.py ──▶ YOLO11 模型 ──▶ model2csv.py ──▶ 结果分析          │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 二、数据采集

### 2.1 视频抽帧 — `video2img.py`

**功能**：将监控录像或手机拍摄的视频按固定间隔抽取为图片序列。

**核心逻辑**：

```python
cap = cv2.VideoCapture(video_path)
frame_count = 0
while True:
    ok, frame = cap.read()
    if not ok: break
    frame_count += 1
    if frame_count % interval == 0:      # 每隔 interval 帧保存一张
        cv2.imwrite(f"{prefix}_{idx}.jpg", frame)
```

**参数说明**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `video_dir` | — | 视频文件夹路径 |
| `output_dir` | — | 输出图片文件夹路径 |
| `interval` | 10 | 抽帧间隔（每 N 帧抽一张） |

**设计要点**：
- 每个视频的输出图片存入独立子文件夹，以视频文件名命名，便于追溯来源
- `interval` 控制采样密度：30fps 视频设 `interval=30` 即每秒抽 1 张，避免过多相似帧
- 摔倒场景建议设较小间隔（10-15），保证关键帧被捕获

### 2.2 图片合成视频 — `img2video.py` / `image2mp4.py`

**功能**：将检测结果图片序列反向合成为视频，用于结果展示和汇报。

**核心逻辑**：

```python
frame = cv2.imread(first_image)
h, w = frame.shape[:2]
writer = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
for img in sorted_images:
    writer.write(cv2.imread(img))
writer.release()
```

`image2mp4.py` 是 `img2video.py` 的别名封装，仅 fps 默认值不同（10 vs 30）。

---

## 三、数据预处理

### 3.1 大图切片（滑窗分割）— `main.py` / `main_folder.py`

**适用场景**：高分辨率监控画面（如 4000×3000）直接缩放到 640×640 会丢失小目标细节。切片检测将大图按滑窗拆分为多个子图，每张子图独立推理后再合并结果。

**算法流程**：

```
原始大图 (4000×3000)
    │
    ├── [1] pad_to_multiple: 填充至切片大小的整数倍
    │    输入: 4000×3000, slice_size=1024
    │    输出: 4096×3072 (右侧+72px, 底部+48px 黑边)
    │
    ├── [2] slice_image_mask: 滑窗切分
    │    窗口大小: 1024×1024
    │    步长: 300px (重叠 724px，防止边界目标被切碎)
    │    输出: N 个 1024×1024 子图
    │
    └── [3] mask_to_shapes: 每张子图的标注 mask → LabelMe JSON
         输出: 子图 PNG + 对应 JSON 标注文件
```

**关键参数对比**：

| 参数 | 大图场景 | 标准场景 |
|------|----------|----------|
| `slice_size` | 1024 | 640 |
| `stride` | 300 | 512 |
| 重叠率 | 70% | 20% |
| 适用 | 4000px+ 监控画面 | 普通相机拍摄 |

**`main.py` vs `main_folder.py`**：
- `main.py`：单张图片 + JSON 标注 → 切片输出
- `main_folder.py`：批量处理整个文件夹中所有 `.JPG` + `.json` 对

### 3.2 批量重命名 — `batch_rename.py`

**功能**：将混杂命名的原始图片统一为 `prefix_0.jpg, prefix_1.jpg, ...` 格式。

**特殊处理**：使用 `cv2.imdecode(np.fromfile(...))` 而非 `cv2.imread()`，解决 Windows 下中文路径无法读取的问题。

```python
def cv_imread_chinese(path):
    return cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
```

### 3.3 文件合并 — `move_data.py`

**功能**：递归遍历源目录，将所有子文件夹中的文件平铺复制到目标目录。

**使用场景**：多个标注人员分别标注后，文件分散在各自的子文件夹中，需要合并到统一目录进行训练。

---

## 四、标注格式转换

### 4.1 标注格式对比

```
┌──────────────────────────────────────────────────────────────┐
│                    三种标注格式                               │
│                                                              │
│  VOC XML                    LabelMe JSON        YOLO TXT     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │ <object>          │  │ {"shapes": [     │  │ 0 0.5 0.5  │ │
│  │   <name>摔倒</name>│  │   {"label":"摔倒",│  │   0.3 0.8  │ │
│  │   <bndbox>        │  │    "points":[...]│  │ 1 0.2 0.7  │ │
│  │     <xmin>100</…>  │  │   }             │  │   0.1 0.4  │ │
│  │     ...            │  │ ]               │  └────────────┘ │
│  │   </bndbox>       │  │ }               │                 │
│  │ </object>         │  └──────────────────┘                 │
│  └──────────────────┘                                        │
│                                                              │
│  绝对坐标 (xmin,ymin,   多边形顶点坐标      归一化中心坐标     │
│  xmax,ymax)             (x1,y1,x2,y2...)  (xc,yc,w,h)       │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 VOC XML → YOLO TXT — `voc_to_yolo.py`

**坐标转换公式**：

```python
dw = 1.0 / img_width        # 归一化因子
dh = 1.0 / img_height

w = xmax - xmin              # 框宽度
h = ymax - ymin              # 框高度
xc = xmin + w / 2            # 中心点 x
yc = ymin + h / 2            # 中心点 y

# YOLO 格式: class_id x_center y_center width height
x_center = xc * dw           # 归一化到 [0, 1]
y_center = yc * dh
width    = w  * dw
height   = h  * dh
```

**模块结构**：

```
parse_xml(xml_path)          解析 XML → (图片尺寸, [标注框列表])
    │
    ▼
cord_converter(size, box)    VOC绝对坐标 → YOLO归一化坐标
    │
    ▼
convert_voc_to_yolo(...)     批量转换 + 复制图片 + 生成标签
```

**输入输出**：

```
输入:
  Annotations/               # VOC XML 标注文件夹
    IMG_0001.xml
    IMG_0002.xml
  JPEGImages/                # 原始图片文件夹
    IMG_0001.jpg
    IMG_0002.jpg

输出:
  output/
    labels/                  # YOLO TXT 标签
      IMG_0001.txt
      IMG_0002.txt
    images/                  # 复制的图片
      IMG_0001.jpg
      IMG_0002.jpg
```

### 4.3 VOC → YOLO 批量转换（含数据集划分）— `voc_to_yolo_batch.py`

在 `voc_to_yolo.py` 基础上增加 **train/val/test 划分** 功能：

```
Main/
  train.txt        # 训练集文件名列表（不含后缀）
  val.txt          # 验证集文件名列表
  test.txt         # 测试集文件名列表

输出结构:
  images/train/    labels/train/
  images/val/      labels/val/
  images/test/     labels/test/
```

### 4.4 LabelMe JSON → YOLO TXT — `labelme2yolo.py`

**与 VOC 转换的关键不同**：LabelMe 使用多边形顶点坐标，需要计算外接矩形。

**坐标转换**：

```python
xs = [p[0] for p in shape["points"]]   # 所有顶点的 x 坐标
ys = [p[1] for p in shape["points"]]   # 所有顶点的 y 坐标

xc = mean(xs) / img_w                  # 多边形中心 x
yc = mean(ys) / img_h                  # 多边形中心 y
w  = (max(xs) - min(xs)) / img_w       # 外接矩形宽
h  = (max(ys) - min(ys)) / img_h       # 外接矩形高
```

**额外功能**：
- 自动按 80/20 划分 train/val
- 生成 `data.yaml` 配置文件（包含 train/val 路径、类别数、类别名）

---

## 五、标注清洗与校验

### 5.1 类别索引统一 — `change_idx.py`

**场景**：合并多个来源的数据集时，不同标注源可能使用不同的类别 ID（如摔倒=0 vs 摔倒=1）。

**逻辑**：遍历所有标签文件，将每行第一个字段（class_id）统一改为 `0`。

```python
for parts in lines:
    parts[0] = "0"                    # 强制归零
    f.write(" ".join(parts) + "\n")
```

适用场景：单类别检测任务（只检测"人"或只检测"摔倒"）。

### 5.2 检测框与分割标注混用检查 — `find_wrong_seg_labels.py`

**场景**：YOLO 分割标注每行有 N×2+1 个值（类别 + 多个坐标对），而检测标注每行只有 5 个值（类别 + xc + yc + w + h）。此工具找出混入分割标注数据集中的目标检测格式行。

```python
if len(line.strip().split()) == 5:    # 5 个元素 = 目标检测标注
    bbox_imgs.append(fname)           # 标记为异常
```

---

## 六、数据集划分

### 6.1 随机划分 — `split_dataset.py`

**功能**：从标注目录生成 train/val/test 的文件名列表。

```python
names = [os.path.splitext(n)[0] for n in os.listdir(anno_dir)]
random.shuffle(names)
split = int(len(names) * val_ratio)
val_names, train_names = names[:split], names[split:]
```

**输出**：`train.txt`、`val.txt`、`test.txt`，每行一个文件名（不含后缀）。

**参数**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `anno_dir` | — | 标注文件目录 |
| `val_ratio` | 0.3 | 验证集比例 |
| `seed` | 42 | 随机种子，保证可复现 |

---

## 七、批量推理与结果导出

### 7.1 批量推理 → CSV — `model2csv.py`

**功能**：对图片目录进行批量推理，将各类别检测计数导出为 CSV 表格。

**输出格式**：

```csv
filename,standing,falling
IMG_0001.jpg,3,0
IMG_0002.jpg,1,2
IMG_0003.jpg,5,0
```

**流程**：

```
图片目录 → YOLO 批量推理 → 逐张统计各类别数量 → np.savetxt → CSV
```

适用场景：
- 批量评估模型在测试集上的表现
- 生成统计报告用于数据分析
- 对比不同模型的检测结果

---

## 八、模块总览

| 模块 | 文件 | 输入 | 输出 | 核心能力 |
|------|------|------|------|----------|
| 视频抽帧 | `video2img.py` | 视频文件 | 图片序列 | 可调间隔采样 |
| 图片合成视频 | `img2video.py` | 图片序列 | MP4 视频 | 可调帧率 |
| 大图切片 | `main.py` | 大图 + LabelMe JSON | 子图 + 子标注 | 滑窗重叠切片 |
| 批量切片 | `main_folder.py` | 多组大图+JSON | 多组子图+标注 | 遍历+调用main |
| 批量重命名 | `batch_rename.py` | 任意命名图片 | 统一命名图片 | 中文路径兼容 |
| 文件合并 | `move_data.py` | 多层目录 | 平铺目录 | 递归复制 |
| VOC→YOLO | `voc_to_yolo.py` | VOC XML | YOLO TXT | 绝对→归一化坐标 |
| VOC→YOLO(划分) | `voc_to_yolo_batch.py` | VOC XML + 划分列表 | YOLO TXT + 子集 | 坐标转换+划分 |
| LabelMe→YOLO | `labelme2yolo.py` | LabelMe JSON | YOLO TXT + yaml | 多边形→外接矩形 |
| 类别统一 | `change_idx.py` | YOLO TXT | YOLO TXT | 强制class_id=0 |
| 标注检查 | `find_wrong_seg_labels.py` | YOLO TXT | 异常文件列表 | bbox/seg分类 |
| 数据集划分 | `split_dataset.py` | 标注目录 | train/val/test.txt | 随机划分+种子 |
| 批量推理 | `model2csv.py` | 图片目录 + .pt | CSV 统计表 | 批量推理+计数 |

---

## 九、典型数据管线示例

### 场景：从监控视频到训练就绪的数据集

```
Step 1: 视频抽帧
  video2img.py → 200 张 jpg 图片

Step 2: 重命名
  batch_rename.py → img_0.jpg ~ img_199.jpg

Step 3: 大图切片（可选，仅高分辨率场景）
  main_folder.py → 每张大图拆分为 12 张 1024×1024 子图

Step 4: LabelMe 标注（人工）
  标注工具 → 每张图一个 .json 文件

Step 5: 格式转换
  labelme2yolo.py → YOLO TXT 标签 + data.yaml

Step 6: 划分数据集
  split_dataset.py → train.txt / val.txt / test.txt

Step 7: 训练
  train.py → best.pt

Step 8: 评估导出
  model2csv.py → result.csv
```

---

*文档版本：v1.0 | 2026-07-07*