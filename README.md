# YOLO11 摔倒检测系统

基于改进 YOLO11 的实时摔倒检测系统，支持图片检测、摄像头实时监测、多目标追踪，提供 PySide6 桌面客户端、Gradio Web 演示和微信小程序三种交互方式。

![GUI 主页](ReadMe%20pic/GUI端主页.png)

## 核心特性

- **高精度检测** — YOLOv5/v8/v11 多架构对比，mAP@0.5 最高 0.81，GPU 推理 140 FPS
- **注意力增强** — CBAM（通道 + 空间注意力）提升关键姿态特征敏感度
- **多目标追踪** — ByteTrack / BoT-SORT，支持轨迹绘制和跨帧目标关联
- **SAHI 切片** — 高分辨率大图切片推理，小目标不漏检
- **三端统一** — PySide6 桌面客户端 / Gradio Web / 微信小程序，共享 FastAPI 后端
- **模型热切换** — 运行时动态切换模型权重，无需重启服务

## 界面展示

### 桌面客户端（PySide6）

| 主页 | 图片检测 |
|------|----------|
| ![GUI 主页](ReadMe%20pic/GUI端主页.png) | ![GUI 检测](ReadMe%20pic/GUI检测页面.png) |

### 微信小程序

| 首页 | 视频流检测 | 摔倒告警 |
|------|-----------|----------|
| ![小程序首页](ReadMe%20pic/小程序首页.png) | ![视频流](ReadMe%20pic/小程序视频流页面.png) | ![摔倒告警](ReadMe%20pic/小程序摔倒警告页面.png) |

| 历史记录 | 系统设置 |
|----------|----------|
| ![历史记录](ReadMe%20pic/小程序历史检测.png) | ![系统设置](ReadMe%20pic/小程序设置页面.png) |

### Web 演示（Gradio）

![Web 检测](ReadMe%20pic/网页端检测页面.png)

## 架构

```
┌─────────────────────────────────────────────────────┐
│                     用户层                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ PySide6  │  │  Gradio  │  │ 微信小程序        │  │
│  │ 桌面客户端│  │ Web Demo │  │ (WXML/WXSS/JS)   │  │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
├───────┼─────────────┼─────────────────┼─────────────┤
│       │             │   HTTP/JSON     │             │
│       └─────────────┴────────┬────────┘             │
│                   API 网关层  │                      │
│            ┌─────────────────┴─────────────────┐    │
│            │  FastAPI + CORS + 请求校验          │    │
│            └─────────────────┬─────────────────┘    │
│                  模型推理层  │                      │
│            ┌─────────────────┴─────────────────┐    │
│            │  YOLO11 + CBAM + ByteTrack        │    │
│            │  SAHI 切片（可选）                  │    │
│            └───────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

## 项目结构

```
yolo11-falling/
├── scripts/                    # 脚本与训练
│   ├── train.py                #   多架构对比训练
│   ├── validate.py             #   模型验证
│   ├── detect_image.py         #   单张图片检测
│   ├── detect_folder.py        #   批量文件夹检测
│   ├── detect_webcam.py        #   摄像头实时检测
│   ├── gui_detect.py           #   PySide6 桌面客户端
│   ├── gui_detect_track.py     #   PySide6 客户端（含追踪）
│   ├── sahi_detect_image.py    #   SAHI 切片检测（图片）
│   ├── sahi_detect_video.py    #   SAHI 切片检测（视频）
│   ├── web_demo.py             #   Gradio Web 演示
│   └── track_test.py           #   追踪功能测试
├── tools/                      # 数据处理工具
│   └── data_process/           #   视频抽帧、标注转换、数据集划分
├── backend/                    # FastAPI 后端
│   ├── main.py                 #   服务入口
│   ├── model_manager.py        #   模型管理（加载/切换/推理）
│   ├── routes/detect.py        #   检测 API 路由
│   └── utils.py                #   图像编解码工具
├── miniprogram/                # 微信小程序（5 个页面）
├── ultralytics/                # YOLO 核心库（含 CBAM 改进模块）
├── falling_data/               # 摔倒检测数据集（16,551 张训练）
├── PROJECT.md                  # 详细项目书
├── EVALUATION.md               # 模型评估报告
├── SUMMARY.md                  # 技术总结
└── README.md
```

## 快速开始

### 环境要求

| 组件 | 版本 |
|------|------|
| Python | ≥ 3.8 |
| PyTorch | ≥ 1.8.0 |
| CUDA | 11.3（GPU，可选） |

### 安装

```bash
# 创建虚拟环境
conda create -n yolo python=3.8 -y && conda activate yolo

# 安装 PyTorch（GPU）
conda install pytorch==1.10.0 torchvision torchaudio cudatoolkit=11.3

# 安装项目依赖
cd yolo11-falling
pip install -e .
```

### 启动后端 API

```bash
cd backend
pip install fastapi uvicorn python-multipart
python main.py
# → http://localhost:8000
# → API 文档: http://localhost:8000/docs
```

### 启动桌面客户端

```bash
python scripts/gui_detect_track.py   # 含追踪的完整客户端
python scripts/web_demo.py           # Gradio Web 演示
```

### 启动微信小程序

1. 微信开发者工具导入 `miniprogram/` 目录
2. 详情 → 本地设置 → 勾选「不校验合法域名」
3. 编译预览

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/health` | 健康检查 |
| `GET` | `/` | 服务状态（模型名、可用数量） |
| `POST` | `/api/detect/image` | 图片检测 (`multipart/form-data`) |
| `POST` | `/api/detect/camera_frame` | 摄像头帧检测 (`application/json`) |
| `GET` | `/api/detect/models` | 获取模型列表 |
| `POST` | `/api/detect/models/switch` | 切换模型 |

### 请求示例

```bash
# 图片检测
curl -X POST http://localhost:8000/api/detect/image \
  -F "image=@test.jpg" \
  -F "conf_threshold=0.25" \
  -F "iou_threshold=0.45"

# 切换模型
curl -X POST http://localhost:8000/api/detect/models/switch \
  -H "Content-Type: application/json" \
  -d '{"model_name": "yolo11s_pretrained"}'
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
python scripts/train.py   # 编辑 DATA_CONFIG_PATH 指向你的数据集
```

### 模型对比

| 模型 | mAP@0.5 | Precision | Recall | 参数量 | GFLOPs |
|------|---------|-----------|--------|--------|--------|
| **YOLOv5n** | **0.8129** | 0.7365 | **0.7904** | 2.50M | 7.1 |
| YOLOv8n | 0.8104 | 0.7813 | 0.7314 | 3.01M | 8.1 |
| YOLO11n | 0.7949 | **0.7897** | 0.7574 | 2.58M | 6.3 |
| YOLO11s | 0.7948 | 0.7814 | 0.7303 | 9.41M | 21.3 |
| YOLO11n-CBAM | 0.6085 | 0.6333 | 0.5624 | 3.29M | 9.3 |
| YOLO11n-GhostConv | 0.5394 | 0.5643 | 0.5079 | **2.35M** | **5.6** |

> 评估环境：RTX 4060 Laptop 8GB / CUDA 11.3 / 640×640 / 305 张验证图片，详见 [EVALUATION.md](EVALUATION.md)

### 模型选型建议

| 场景 | 推荐模型 | 理由 |
|------|----------|------|
| 最高检出率 | YOLOv5n | mAP@0.5 最高，Recall 最高 |
| 最低误报 | YOLO11n | Precision 最高，架构最新 |
| 边缘端部署 | YOLO11n-GhostConv | 参数量 2.35M，计算量 5.6 GFLOPs |
| 综合推荐 | **YOLO11n** | 精度/速度最佳平衡 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 深度学习 | PyTorch, Ultralytics YOLO11, CBAM |
| 目标追踪 | ByteTrack, BoT-SORT |
| 切片检测 | SAHI |
| 后端 API | FastAPI, Uvicorn |
| 桌面 GUI | PySide6 (Qt 6) |
| Web 演示 | Gradio |
| 小程序 | 微信小程序（WXML/WXSS/JS） |
| 图像处理 | OpenCV, Pillow |
| 数据可视化 | Matplotlib, Seaborn |

## 相关文档

- [PROJECT.md](PROJECT.md) — 完整项目书（技术方案、场景分析、创新点）
- [EVALUATION.md](EVALUATION.md) — 模型评估报告（精度/速度/混淆矩阵）
- [SUMMARY.md](SUMMARY.md) — 技术总结（推理管道、追踪管道、闭环流程）

## License

AGPL-3.0
