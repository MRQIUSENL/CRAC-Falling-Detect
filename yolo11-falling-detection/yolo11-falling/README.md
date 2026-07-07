# YOLO11 摔倒检测系统

基于改进 YOLO11 的实时摔倒检测系统，支持图片检测、摄像头实时监测、多目标追踪，并提供 PySide6 桌面客户端、Gradio Web 演示和微信小程序三种交互方式。

![](https://vehicle4cm.oss-cn-beijing.aliyuncs.com/imgs/image-20250115014323595.png)

## 特性

- **高精度检测** — YOLO11 + CBAM 注意力机制，针对摔倒场景优化
- **多模型对比** — 内置 YOLOv5/v8/v11 多架构对比实验
- **实时追踪** — 支持 ByteTrack / BoT-SORT 多目标追踪
- **SAHI 切片** — 支持高分辨率图像切片检测
- **多端交互** — PySide6 桌面客户端 / Gradio Web / 微信小程序
- **REST API** — FastAPI 后端，提供完整检测 API

## 架构

```
┌─────────────────────────────────────────────────────┐
│                    前端层                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ PySide6  │  │  Gradio  │  │ 微信小程序        │  │
│  │ 桌面客户端│  │ Web Demo │  │ (WXML/WXSS/JS)   │  │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
├───────┼─────────────┼─────────────────┼─────────────┤
│       │             │       HTTP API  │             │
│       └─────────────┴────────┬────────┘             │
│                    后端层     │                      │
│               ┌──────────────┴──────────────┐       │
│               │   FastAPI + YOLO11 Engine   │       │
│               └─────────────────────────────┘       │
└─────────────────────────────────────────────────────┘
```

## 项目结构

```
yolo11-falling/
├── scripts/                # 演示脚本与训练模型
│   ├── train.py            #   模型训练 (多架构对比+消融)
│   ├── validate.py         #   模型验证
│   ├── detect_image.py     #   单张图片检测
│   ├── detect_folder.py    #   批量文件夹检测
│   ├── detect_webcam.py    #   摄像头/视频检测
│   ├── gui_detect.py       #   PySide6 图形化界面
│   ├── gui_detect_track.py #   PySide6 界面 (含追踪)
│   ├── sahi_detect_image.py#   SAHI 切片检测 (图片)
│   ├── sahi_detect_video.py#   SAHI 切片检测 (视频)
│   ├── web_demo.py         #   Gradio Web 演示
│   └── runs/               #   训练输出 (模型权重)
├── tools/               # 数据处理工具
│   └── data_process/       #   视频分帧、标注转换、数据集划分
├── backend/                # FastAPI 后端服务
│   ├── main.py             #   服务入口
│   ├── model_manager.py    #   模型管理 (加载/推理/切换)
│   ├── routes/detect.py    #   检测 API
│   └── utils.py            #   图像处理工具
├── miniprogram/            # 微信小程序
│   ├── pages/              #   首页/图片检测/实时检测/历史/设置
│   └── utils/              #   API 封装 / 本地存储
├── ultralytics/            # YOLO 核心库 (含改进模块)
│   └── cfg/datasets/       #   数据集配置
├── falling_data/           # 摔倒数据集
├── pyproject.toml
└── README.md
```

## 快速开始

### 环境要求

- Python >= 3.8
- PyTorch >= 1.8
- Node.js (小程序开发时可选)

### 安装

```bash
# 创建虚拟环境
conda create -n yolo python=3.8 -y && conda activate yolo

# 安装 PyTorch (根据 CUDA 版本选择)
# CPU:  conda install pytorch==1.8.0 torchvision torchaudio cpuonly
# GPU:  conda install pytorch==1.10.0 torchvision torchaudio cudatoolkit=11.3

# 安装项目依赖
pip install -e .
```

### 启动后端 API

```bash
cd backend
pip install fastapi uvicorn python-multipart
python main.py
# → http://localhost:8000
# → API 文档 http://localhost:8000/docs
```

### 启动微信小程序

1. 微信开发者工具导入 `miniprogram/` 目录
2. 右上角「详情」→「本地设置」→ 勾选「不校验合法域名」
3. 编译预览

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/health` | 健康检查 |
| `GET` | `/` | 服务状态 (当前模型、可用模型数) |
| `POST` | `/api/detect/image` | 上传图片检测 (`multipart/form-data`) |
| `POST` | `/api/detect/camera_frame` | 摄像头帧检测 (`application/json`) |
| `GET` | `/api/detect/models` | 获取可用模型列表 |
| `POST` | `/api/detect/models/switch` | 切换模型 |

### 请求示例

```bash
# 图片检测
curl -X POST http://localhost:8000/api/detect/image \
  -F "image=@test.jpg" \
  -F "conf_threshold=0.25" \
  -F "iou_threshold=0.45"

# 摄像头帧检测
curl -X POST http://localhost:8000/api/detect/camera_frame \
  -H "Content-Type: application/json" \
  -d '{"frame":"data:image/jpeg;base64,...", "conf_threshold":0.25}'
```

### 响应格式

```json
{
  "success": true,
  "detections": [
    {"class": "摔倒", "class_id": 1, "confidence": 0.92, "bbox": [x1,y1,x2,y2]}
  ],
  "counts": {"摔倒": 1, "站立": 3},
  "total_objects": 4,
  "annotated_image": "data:image/jpeg;base64,...",
  "inference_time_ms": 45.2
}
```

## 模型训练

```bash
# 编辑 train.py 中的 DATA_CONFIG_PATH 指向你的数据集
python scripts/train.py
```

训练配置在 `ultralytics/cfg/datasets/A_my_data.yaml`，支持以下改进模型：

| 模型 | 配置文件 | 说明 |
|------|----------|------|
| YOLO11n | `yolo11n.yaml` | 基线模型 |
| YOLO11s | `yolo11s.yaml` | 更大参数量 |
| YOLO11n-CBAM | `yolo11n-cbam.yaml` | 加入 CBAM 注意力 |
| YOLO11n-GhostConv | `yolo11n-GhostConv.yaml` | GhostConv 轻量化 |

训练输出保存在 `scripts/runs/` 目录下。

## 桌面客户端

```bash
# PySide6 图形化界面 (含追踪)
python scripts/gui_detect_track.py

# Gradio Web 演示
python scripts/web_demo.py
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 深度学习框架 | PyTorch, Ultralytics YOLO11 |
| 注意力机制 | CBAM, GhostConv |
| 目标追踪 | ByteTrack, BoT-SORT |
| 切片检测 | SAHI |
| 后端 API | FastAPI, Uvicorn |
| 桌面 GUI | PySide6 (Qt 6) |
| Web 演示 | Gradio |
| 小程序 | 微信小程序 (WXML/WXSS/JS) |
| 图像处理 | OpenCV, Pillow |
| 数据可视化 | Matplotlib, Seaborn |

## License

AGPL-3.0
