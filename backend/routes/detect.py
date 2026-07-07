#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
检测相关的 API 路由
"""

import io
import time
from typing import Optional

import numpy as np
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from PIL import Image

from model_manager import model_manager
from utils import pil_to_cv2, base64_to_cv2, resize_image

router = APIRouter(prefix="/api/detect", tags=["detection"])


class CameraFrameRequest(BaseModel):
    frame: str = Field(..., description="Base64 编码的摄像头帧")
    conf_threshold: float = Field(0.25, ge=0.0, le=1.0)
    iou_threshold: float = Field(0.45, ge=0.0, le=1.0)
    tracker: Optional[str] = None


class SwitchModelRequest(BaseModel):
    model_name: str = Field(..., description="要切换的模型名称")


@router.post("/image")
async def detect_image(
    image: UploadFile = File(..., description="上传的图片文件"),
    conf_threshold: float = Form(0.25, ge=0.0, le=1.0, description="置信度阈值"),
    iou_threshold: float = Form(0.45, ge=0.0, le=1.0, description="IoU 阈值"),
    tracker: Optional[str] = Form(None, description="追踪器类型")
):
    """
    上传图片进行目标检测

    - **image**: 图片文件 (jpg, png, jpeg)
    - **conf_threshold**: 置信度阈值 (0.0-1.0)
    - **iou_threshold**: IoU 阈值 (0.0-1.0)
    - **tracker**: 可选追踪器 (bytetrack.yaml / botsort.yaml)
    """
    # 验证文件类型
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")

    try:
        # 读取上传的图片
        contents = await image.read()
        pil_img = Image.open(io.BytesIO(contents)).convert("RGB")
        cv2_img = pil_to_cv2(pil_img)

        # 缩放大图以加快推理
        cv2_img = resize_image(cv2_img, max_size=1280)

        # 执行检测
        result = model_manager.predict_image(
            cv2_img,
            conf_threshold=conf_threshold,
            iou_threshold=iou_threshold,
            tracker_type=tracker
        )

        return JSONResponse(content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@router.post("/camera_frame")
async def detect_camera_frame(req: CameraFrameRequest):
    """
    接收摄像头帧进行实时检测

    - **frame**: Base64 编码的图像帧
    - **conf_threshold**: 置信度阈值
    - **iou_threshold**: IoU 阈值
    - **tracker**: 可选追踪器
    """
    try:
        # 解码 base64 图像
        cv2_img = base64_to_cv2(req.frame)

        # 缩放以加快推理
        cv2_img = resize_image(cv2_img, max_size=640)

        # 执行检测
        result = model_manager.predict_image(
            cv2_img,
            conf_threshold=req.conf_threshold,
            iou_threshold=req.iou_threshold,
            tracker_type=req.tracker or None
        )

        return JSONResponse(content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@router.get("/models")
async def get_models():
    """获取可用的模型列表"""
    models = model_manager.get_available_models()
    return JSONResponse(content={
        "success": True,
        "models": [
            {"name": name, "path": path}
            for name, path in models.items()
        ],
        "current_model": model_manager.current_model_name
    })


@router.post("/models/switch")
async def switch_model(req: SwitchModelRequest):
    """切换当前使用的模型"""
    success = model_manager.load_model(req.model_name)
    if success:
        return JSONResponse(content={
            "success": True,
            "current_model": req.model_name,
            "message": f"已切换到模型: {req.model_name}"
        })
    else:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"模型 '{req.model_name}' 不存在"}
        )
