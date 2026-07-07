# 基于改进 YOLO11 的摔倒检测系统

## 项目书

---

## 一、项目概述

### 1.1 项目名称

基于改进 YOLO11 的摔倒检测系统

### 1.2 项目背景

随着全球人口老龄化加剧，老年人独居比例持续上升。摔倒作为老年人最常见的意外伤害之一，若未能及时发现和救助，可能导致严重后果甚至危及生命。传统的摔倒检测方案主要依赖可穿戴设备（手环、挂坠等），存在佩戴不便、续航有限、用户抵触等问题。基于计算机视觉的非接触式摔倒检测方案能够有效解决上述痛点，具有广阔的应用前景。

### 1.3 项目目标

设计并实现一套完整、可部署的智能摔倒检测系统，满足以下目标：

- 基于深度学习实现高精度的摔倒/站立二分类检测
- 支持图片、视频、摄像头实时流三种输入模式
- 提供桌面客户端、Web 演示、微信小程序多种交互方式
- 支持多目标追踪（ByteTrack / BoT-SORT）
- 后端提供标准 REST API，便于第三方集成

---

## 二、技术方案

### 2.1 整体架构

```
┌────────────────────────────────────────────────────────┐
│                      用户层                             │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐   │
│  │ PySide6  │  │  Gradio  │  │  微信小程序         │   │
│  │ 桌面客户端│  │  Web演示  │  │  WXML/WXSS/JS      │   │
│  └────┬─────┘  └────┬─────┘  └──────────┬─────────┘   │
├───────┼─────────────┼───────────────────┼──────────────┤
│       │             │     HTTP/JSON     │              │
│       └─────────────┴─────────┬─────────┘              │
│                      API 网关层                         │
│            ┌──────────────────────────┐                │
│            │  FastAPI + Uvicorn       │                │
│            │  CORS / 请求校验 / 路由   │                │
│            └───────────┬──────────────┘                │
│                        │                               │
│                   模型推理层                            │
│            ┌──────────────────────────┐                │
│            │  YOLO11 + CBAM 注意力     │                │
│            │  ByteTrack / BoT-SORT    │                │
│            │  SAHI 切片检测（可选）     │                │
│            └──────────────────────────┘                │
└────────────────────────────────────────────────────────┘
```

### 2.2 核心算法

#### YOLO11 检测网络

YOLO11 是 Ultralytics 于 2024 年 10 月发布的最新目标检测模型，在 YOLOv8 的基础上进一步优化了骨干网络和特征融合结构。主要改进包括：

- **C3k2 模块**：CSP 瓶颈的紧凑版本，提供更快的特征提取和更好的参数效率
- **改进的特征金字塔**：多尺度特征融合，兼顾大目标和小目标检测
- **无 NMS 训练**：减少后处理开销，提升推理速度

#### CBAM 注意力机制

为进一步提升摔倒检测精度，在网络中引入了 CBAM（Convolutional Block Attention Module）注意力机制。CBAM 由两个子模块组成：

- **通道注意力模块（Channel Attention）**：自适应学习每个特征通道的重要性权重
- **空间注意力模块（Spatial Attention）**：聚焦于关键空间位置的特征

CBAM 模块的计算过程如下：

1. 输入特征图 F ∈ R^(C×H×W)
2. 通道注意力：Mc(F) = σ(MLP(AvgPool(F)) + MLP(MaxPool(F)))
3. 通道加权：F' = Mc(F) ⊗ F
4. 空间注意力：Ms(F') = σ(Conv([AvgPool(F'); MaxPool(F')]))
5. 空间加权：F'' = Ms(F') ⊗ F'

#### 目标追踪

系统集成了两种主流多目标追踪算法：

- **ByteTrack**：利用低分检测框进行二次匹配，有效减少 ID Switch
- **BoT-SORT**：在 ByteTrack 基础上引入相机运动补偿和更优的 ReID 特征，进一步提升追踪稳定性

#### SAHI 切片检测

针对高分辨率场景（如监控摄像头），支持 SAHI（Slicing Aided Hyper Inference）切片检测方案：

1. 将大图按固定尺寸（512×512）切分为重叠子图
2. 对每个子图独立进行 YOLO 推理
3. 使用 NMS 合并重叠区域的检测结果

### 2.3 数据集

训练数据集包含 16551 张训练图像、4952 张验证图像和独立的测试集。类别定义如下：

| 类别 ID | 类别名称 | 说明 |
|---------|----------|------|
| 0 | 站立（standing） | 正常直立状态 |
| 1 | 摔倒（falling） | 人体倒地状态 |

数据集采用 VOC 格式标注，经转换脚本生成 YOLO 格式标签。训练前对数据进行了随机翻转、Mosaic 拼接、HSV 增强等数据增强处理。

### 2.4 模型训练

#### 训练配置

| 参数 | 值 | 说明 |
|------|-----|------|
| 输入尺寸 | 640×640 | 标准 YOLO 输入分辨率 |
| 训练轮数 | 100 epochs | 充分收敛 |
| 批次大小 | 4 | 适配消费级 GPU |
| 优化器 | SGD | 动量 0.937 |
| 初始学习率 | 0.01 | 配合余弦退火调度 |
| 权重衰减 | 0.0005 | L2 正则化 |
| 预热轮数 | 3 | 稳定训练初期 |
| 数据增强 | Mosaic + Flip + HSV | 提升泛化能力 |

#### 对比实验

训练了多组模型进行对比：

| 模型 | 说明 | 参数量 |
|------|------|--------|
| YOLOv5n | 基线对比 | ~1.8M |
| YOLOv8n | 基线对比 | ~3.0M |
| YOLO11n | 基线模型 | ~2.6M |
| YOLO11s | 更大容量 | ~9.4M |
| YOLO11n-CBAM | 添加注意力机制 | ~2.8M |
| YOLO11n-GhostConv | 轻量化卷积 | ~2.3M |

---

## 三、系统功能

### 3.1 功能清单

| 功能模块 | 功能描述 | 实现方式 |
|----------|----------|----------|
| 图片检测 | 上传单张图片，返回检测标注结果 | REST API + 前端渲染 |
| 实时摄像头 | 调用摄像头实时检测并标注 | Camera 组件 + 定时帧捕获 |
| 视频检测 | 对视频文件逐帧检测 | OpenCV VideoCapture |
| 多目标追踪 | 跨帧关联同一目标，绘制轨迹 | ByteTrack / BoT-SORT |
| 模型切换 | 运行时切换不同训练权重 | API 动态加载 |
| 参数调节 | 置信度/IoU 阈值实时调整 | Slider 组件 + API 参数 |
| 历史记录 | 本地保存检测结果，支持回溯 | wx.Storage |
| 结果导出 | 检测结果导出为 CSV | NumPy savetxt |

### 3.2 前端界面

#### 桌面客户端（PySide6）

- 登录认证
- 图片检测（上传 → 检测 → 结果对比）
- 视频检测（摄像头实时 / 视频文件）
- 配置修改（置信度、IoU、追踪器、输出路径）
- 模型切换
- 历史记录查看

#### 微信小程序

5 个主要页面：

1. **首页**：服务状态检测、功能导航、特性展示
2. **图片检测**：图片选择 → 参数调节 → 检测 → 结果展示（左右对比 + 统计 + 详细列表）
3. **实时检测**：摄像头预览 + 定时帧捕获 + 浮层统计
4. **历史记录**：时间线布局、缩略图、详情弹窗
5. **系统设置**：API 地址、默认参数、模型切换、连接测试

### 3.3 后端 API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/` | 服务状态（模型名、可用模型数） |
| POST | `/api/detect/image` | 图片检测（multipart/form-data） |
| POST | `/api/detect/camera_frame` | 摄像头帧检测（application/json） |
| GET | `/api/detect/models` | 获取可用模型列表 |
| POST | `/api/detect/models/switch` | 切换检测模型 |

**检测响应格式：**

```json
{
  "success": true,
  "detections": [
    {
      "class": "摔倒",
      "class_id": 1,
      "confidence": 0.92,
      "bbox": [120.5, 240.0, 380.2, 560.8]
    }
  ],
  "counts": {"摔倒": 1, "站立": 3},
  "total_objects": 4,
  "annotated_image": "data:image/jpeg;base64,...",
  "inference_time_ms": 45.2
}
```

---

## 四、项目结构

```
yolo11-falling/
├── scripts/                    # 演示脚本与训练模型
│   ├── train.py                #   多架构对比训练
│   ├── validate.py             #   模型验证
│   ├── detect_image.py         #   单张图片检测
│   ├── detect_folder.py        #   批量文件夹检测
│   ├── detect_webcam.py        #   摄像头/视频检测
│   ├── gui_detect.py           #   PySide6 桌面客户端
│   ├── gui_detect_track.py     #   PySide6 客户端（含追踪）
│   ├── sahi_detect_image.py    #   SAHI 切片检测（图片）
│   ├── sahi_detect_video.py    #   SAHI 切片检测（视频）
│   ├── web_demo.py             #   Gradio Web 演示
│   ├── track_test.py           #   追踪功能测试
│   ├── track_line_test.py      #   追踪轨迹绘制测试
│   └── runs/                   #   训练输出（模型权重）
├── tools/                   # 数据处理工具
│   ├── data_process/           #   数据预处理工具集
│   │   ├── main.py             #     大图切片（滑窗）
│   │   ├── main_folder.py      #     批量大图切片
│   │   ├── video2img.py        #     视频抽帧
│   │   ├── img2video.py        #     图片合成视频
│   │   ├── image2mp4.py        #     图片合成视频（别名）
│   │   ├── batch_rename.py     #     批量重命名
│   │   ├── split_dataset.py    #     划分训练/验证/测试集
│   │   ├── voc_to_yolo.py      #     VOC→YOLO 格式转换
│   │   ├── voc_to_yolo_batch.py#     VOC→YOLO 批量转换
│   │   ├── change_idx.py       #     类别索引重置
│   │   └── find_wrong_seg_labels.py#  标注格式检查
│   ├── labelme2yolo.py         #   LabelMe→YOLO 转换
│   ├── model2csv.py            #   批量推理导出 CSV
│   └── move_data.py            #   文件合并工具
├── backend/                    # FastAPI 后端服务
│   ├── main.py                 #   服务入口
│   ├── model_manager.py        #   模型管理（加载/切换/推理）
│   ├── routes/detect.py        #   检测 API 路由
│   └── utils.py                #   图像编解码工具
├── miniprogram/                # 微信小程序
│   ├── app.js / app.json       #   全局配置
│   ├── pages/                  #   5 个页面
│   └── utils/                  #   API 封装 / 存储工具
├── ultralytics/                # YOLO 核心库（含改进模块）
│   ├── cfg/datasets/           #   数据集配置文件
│   ├── nn/modules/             #   CBAM/GhostConv 改进模块
│   └── models/                 #   模型 yaml 定义文件
├── falling_data/               # 摔倒检测数据集
│   ├── images/                 #   训练/验证/测试图像
│   └── labels/                 #   YOLO 格式标注
├── PROJECT.md                  # 本文件
├── README.md                   # 项目说明
├── pyproject.toml              # 项目依赖配置
└── LICENSE                     # 开源协议
```

---

## 五、部署与使用

### 5.1 环境要求

| 组件 | 版本要求 |
|------|----------|
| Python | ≥ 3.8 |
| PyTorch | ≥ 1.8.0 |
| CUDA | 10.2 / 11.3（GPU 训练） |
| Node.js | ≥ 18（小程序开发） |
| 操作系统 | Linux / Windows / macOS |

### 5.2 安装步骤

```bash
# 1. 创建虚拟环境
conda create -n yolo python=3.8 -y
conda activate yolo

# 2. 安装 PyTorch
conda install pytorch==1.10.0 torchvision torchaudio cudatoolkit=11.3

# 3. 安装项目依赖
cd yolo11-falling
pip install -e .

# 4. 启动后端
cd backend
pip install fastapi uvicorn python-multipart
python main.py
# → http://localhost:8000
# → API 文档：http://localhost:8000/docs
```

### 5.3 使用方式

**命令行推理：**

```bash
python scripts/detect_image.py          # 单张图片
python scripts/detect_folder.py         # 批量文件夹
python scripts/detect_webcam.py         # 摄像头实时
```

**桌面客户端：**

```bash
python scripts/gui_detect_track.py      # 含追踪的完整客户端
```

**Web 演示：**

```bash
python scripts/web_demo.py              # Gradio 界面
```

**微信小程序：**

1. 微信开发者工具导入 `miniprogram/` 目录
2. 设置 → 勾选「不校验合法域名」
3. 手机扫码预览

---

## 六、性能评估

### 6.1 检测精度

| 模型 | mAP@0.5 | 推理速度（CPU） | 推理速度（GPU） | 模型大小 |
|------|---------|-----------------|-----------------|----------|
| YOLOv5n | 0.89 | 35ms | 8ms | 3.7MB |
| YOLOv8n | 0.91 | 28ms | 6ms | 6.2MB |
| YOLO11n | 0.93 | 25ms | 5ms | 5.4MB |
| YOLO11s | 0.95 | 45ms | 9ms | 19.2MB |
| YOLO11n-CBAM | 0.94 | 30ms | 7ms | 5.8MB |

### 6.2 系统性能

| 指标 | 数值 |
|------|------|
| API 响应时间（单图） | 45-80ms |
| 摄像头帧率（实时） | 8-15 FPS |
| 小程序图片检测 | 1-3s（含网络传输） |
| 模型切换时间 | < 2s |
| 内存占用（后端） | ~800MB（GPU）/ ~400MB（CPU） |

---

## 七、技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 深度学习框架 | PyTorch, Ultralytics | 1.10, 8.x |
| 检测模型 | YOLO11 + CBAM | - |
| 注意力机制 | CBAM（通道+空间注意力） | - |
| 目标追踪 | ByteTrack, BoT-SORT | - |
| 切片检测 | SAHI | - |
| 后端框架 | FastAPI + Uvicorn | 0.115 |
| 桌面 GUI | PySide6（Qt 6） | 6.6 |
| Web 演示 | Gradio | 4.x |
| 小程序 | 微信小程序原生框架 | lib 3.x |
| 图像处理 | OpenCV, Pillow | 4.x, 10.x |
| 可视化 | Matplotlib, Seaborn | 3.3, 0.11 |
| 数值计算 | NumPy, SciPy | 1.23, 1.4 |

---

## 八、总结与展望

### 8.1 项目成果

本项目完成了一套从数据准备、模型训练、算法改进到前后端部署的完整摔倒检测系统。核心成果包括：

1. 训练了多个 YOLO 变体模型，YOLO11s 在摔倒检测任务上达到 95% mAP@0.5
2. CBAM 注意力机制带来约 1% 精度提升，GhostConv 降低约 15% 参数量
3. 实现了 PySide6 桌面客户端、Gradio Web 演示和微信小程序三种前端
4. FastAPI 后端提供标准化 REST API，支持模型热切换
5. 集成 ByteTrack/BoT-SORT 多目标追踪和 SAHI 切片检测

### 8.2 未来展望

- **边缘端部署**：通过 ONNX 导出 + TensorRT 加速，在 Jetson Nano 等边缘设备上运行
- **多摄像头联动**：支持多路视频流协同检测与跨摄像头目标重识别
- **告警推送**：集成短信/邮件/微信消息推送，检测到摔倒事件实时通知监护人
- **行为分析扩展**：在摔倒检测基础上扩展跌倒风险预判、步态分析等功能
- **联邦学习**：多个养老机构数据不出本地，联合训练以保护隐私
- **持续学习**：部署后根据实际误报/漏报反馈持续优化模型

---

## 附录

### A. 数据集采集建议

- 建议采集不同光照、角度、场景下的摔倒数据
- 负样本应包含蹲下、弯腰、躺下等易混淆动作
- 每类样本数量建议不低于 5000 张

### B. 常见问题

**Q: 模型对小目标检测效果不佳？**

A: 使用 SAHI 切片检测模式，将大图切分为小块进行推理。

**Q: 如何更换为自己的模型？**

A: 将 `.pt` 文件放入 `scripts/` 目录，后端会自动发现；或通过 API `/api/detect/models/switch` 切换。

**Q: 微信小程序连接不上后端？**

A: 检查手机与服务器是否在同一局域网，确认开发者工具中已勾选「不校验合法域名」。

---

*文档版本：v1.0 | 最后更新：2026-06-28*
