#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
YOLO11 摔倒检测系统 - 后端 API 服务
FastAPI 主入口
"""

import sys
import os
from contextlib import asynccontextmanager

# 将当前目录和上级目录添加到路径中，方便导入本地模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from model_manager import model_manager
from routes.detect import router as detect_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时加载模型，关闭时释放资源"""
    print("=" * 60)
    print("YOLO11 摔倒检测系统 API 正在启动...")
    print("=" * 60)

    available = model_manager.get_available_models()
    if available:
        print(f"发现 {len(available)} 个模型文件:")
        for name in available:
            print(f"  - {name}")
        loaded = model_manager.set_auto_model()
        if loaded:
            print(f"已自动加载模型: {loaded}")
    else:
        print("警告: 未找到任何模型文件(.pt)")
        print("请将训练好的模型放在 scripts/ 目录下")

    yield  # 服务器运行期间在此暂停

    # 关闭时的清理工作
    print("YOLO11 摔倒检测系统 API 正在关闭...")


# 创建 FastAPI 应用
app = FastAPI(
    title="YOLO11 摔倒检测系统 API",
    description="基于 YOLO11 的目标检测后端服务，为微信小程序提供推理接口",
    version="1.0.0",
    lifespan=lifespan,
)

# 配置 CORS，允许微信小程序跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(detect_router)


@app.get("/")
async def root():
    """根路径 - 服务状态检查"""
    return {
        "service": "YOLO11 摔倒检测系统 API",
        "version": "1.0.0",
        "status": "running",
        "current_model": model_manager.current_model_name,
        "available_models": len(model_manager.get_available_models())
    }


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
