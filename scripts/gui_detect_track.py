"""PySide6 图形化检测界面 (含追踪)"""

import copy
import os
import os.path as osp
import shutil
import sys
import threading
import time
import cv2
import numpy as np
import torch
from collections import defaultdict
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from ultralytics import YOLO

os.chdir(osp.dirname(osp.abspath(__file__)))  # 确保工作目录是脚本所在目录

WINDOW_TITLE = "Target detection system"
WELCOME_SENTENCE = "YOLO11 摔倒检测系统"
USERNAME = "admin"
PASSWORD = "admin"


def _create_placeholder_pixmap(text, width, height, bg_color=(200, 200, 200), text_color=(100, 100, 100)):
    """创建带文字的占位图像"""
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor(*bg_color))
    painter = QPainter(pixmap)
    painter.setPen(QColor(*text_color))
    font = QFont('楷体', 18)
    painter.setFont(font)
    painter.drawText(QRect(0, 0, width, height), Qt.AlignCenter, text)
    painter.end()
    return pixmap


def _create_app_icon():
    """创建程序图标"""
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(48, 124, 208))
    painter = QPainter(pixmap)
    painter.setPen(QColor(255, 255, 255))
    font = QFont('楷体', 22)
    painter.setFont(font)
    painter.drawText(QRect(0, 0, 64, 64), Qt.AlignCenter, "Y")
    painter.end()
    return QIcon(pixmap)


class MainWindow(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)       # 系统界面标题
        self.resize(1200, 800)                  # 系统初始化大小
        self.setWindowIcon(_create_app_icon())   # 系统logo图像
        self.output_size = 480                  # 上传的图像和视频在系统界面上显示的大小
        self.img2predict = ""                   # 要进行预测的图像路径
        self.init_vid_id = '0'                  # 网络摄像头修改 包括ip或者是ip地址的修改
        self.vid_source = int(self.init_vid_id) # 需要设置为对应的整数，加载的才是usb的摄像头
        self.conf_thres = 0.25   # 置信度的阈值
        self.iou_thres = 0.45    # NMS操作的时候 IOU过滤的阈值
        self.save_txt = False
        self.save_conf = False
        self.save_crop = False
        self.vid_gap = 30        # 摄像头视频帧保存间隔。
        self.is_open_track = ""  # 三种选择，如果是空表示不开启追踪，否则有两种追踪器可以进行选择


        self.model_path = osp.join(osp.dirname(osp.abspath(__file__)), "runs", "yolo11s_pretrained", "train", "weights", "best.pt")
        self.model = self.model_load(weights=self.model_path)
        self.cap = cv2.VideoCapture(self.vid_source)
        self.stopEvent = threading.Event()
        self.webcam = True
        self.stopEvent.clear()

        self.initUI()            # 初始化图形化界面
        self.reset_vid()         # 重新设置视频参数，重新初始化是为了防止视频加载出错

    @torch.no_grad()
    def model_load(self, weights=""):
        """
        模型加载
        """
        model_loaded = YOLO(weights)
        return model_loaded

    def initUI(self):
        """
        图形化界面初始化
        """
        font_title = QFont('楷体', 16)
        font_main = QFont('楷体', 14)
        img_detection_widget = QWidget()
        img_detection_layout = QVBoxLayout()
        img_detection_title = QLabel("图片识别功能")
        img_detection_title.setFont(font_title)
        mid_img_widget = QWidget()
        mid_img_layout = QHBoxLayout()
        self.left_img = QLabel()
        self.right_img = QLabel()
        self.left_img.setPixmap(_create_placeholder_pixmap("图片预览", 480, 360))
        self.right_img.setPixmap(_create_placeholder_pixmap("检测结果", 480, 360))
        self.left_img.setAlignment(Qt.AlignCenter)
        self.right_img.setAlignment(Qt.AlignCenter)
        mid_img_layout.addWidget(self.left_img)
        mid_img_layout.addWidget(self.right_img)
        self.img_num_label = QLabel("当前检测结果：待检测")
        self.img_num_label.setFont(font_main)
        mid_img_widget.setLayout(mid_img_layout)
        up_img_button = QPushButton("上传图片")
        det_img_button = QPushButton("开始检测")
        up_img_button.clicked.connect(self.upload_img)
        det_img_button.clicked.connect(self.detect_img)
        up_img_button.setFont(font_main)
        det_img_button.setFont(font_main)
        up_img_button.setStyleSheet("QPushButton{color:white}"
                                    "QPushButton:hover{background-color: rgb(2,110,180);}"
                                    "QPushButton{background-color:rgb(48,124,208)}"
                                    "QPushButton{border:2px}"
                                    "QPushButton{border-radius:5px}"
                                    "QPushButton{padding:5px 5px}"
                                    "QPushButton{margin:5px 5px}")
        det_img_button.setStyleSheet("QPushButton{color:white}"
                                     "QPushButton:hover{background-color: rgb(2,110,180);}"
                                     "QPushButton{background-color:rgb(48,124,208)}"
                                     "QPushButton{border:2px}"
                                     "QPushButton{border-radius:5px}"
                                     "QPushButton{padding:5px 5px}"
                                     "QPushButton{margin:5px 5px}")
        img_detection_layout.addWidget(img_detection_title, alignment=Qt.AlignCenter)
        img_detection_layout.addWidget(mid_img_widget, alignment=Qt.AlignCenter)
        img_detection_layout.addWidget(self.img_num_label)
        img_detection_layout.addWidget(up_img_button)
        img_detection_layout.addWidget(det_img_button)
        img_detection_widget.setLayout(img_detection_layout)

        vid_detection_widget = QWidget()
        vid_detection_layout = QVBoxLayout()
        vid_title = QLabel("视频检测功能")
        vid_title.setFont(font_title)
        self.vid_img = QLabel()
        self.vid_img.setPixmap(_create_placeholder_pixmap("视频检测", 480, 360))
        vid_title.setAlignment(Qt.AlignCenter)
        self.vid_img.setAlignment(Qt.AlignCenter)
        self.webcam_detection_btn = QPushButton("摄像头实时监测")
        self.mp4_detection_btn = QPushButton("视频文件检测")
        self.vid_stop_btn = QPushButton("停止检测")
        self.webcam_detection_btn.setFont(font_main)
        self.mp4_detection_btn.setFont(font_main)
        self.vid_stop_btn.setFont(font_main)
        self.webcam_detection_btn.setStyleSheet("QPushButton{color:white}"
                                                "QPushButton:hover{background-color: rgb(2,110,180);}"
                                                "QPushButton{background-color:rgb(48,124,208)}"
                                                "QPushButton{border:2px}"
                                                "QPushButton{border-radius:5px}"
                                                "QPushButton{padding:5px 5px}"
                                                "QPushButton{margin:5px 5px}")
        self.mp4_detection_btn.setStyleSheet("QPushButton{color:white}"
                                             "QPushButton:hover{background-color: rgb(2,110,180);}"
                                             "QPushButton{background-color:rgb(48,124,208)}"
                                             "QPushButton{border:2px}"
                                             "QPushButton{border-radius:5px}"
                                             "QPushButton{padding:5px 5px}"
                                             "QPushButton{margin:5px 5px}")
        self.vid_stop_btn.setStyleSheet("QPushButton{color:white}"
                                        "QPushButton:hover{background-color: rgb(2,110,180);}"
                                        "QPushButton{background-color:rgb(48,124,208)}"
                                        "QPushButton{border:2px}"
                                        "QPushButton{border-radius:5px}"
                                        "QPushButton{padding:5px 5px}"
                                        "QPushButton{margin:5px 5px}")
        self.webcam_detection_btn.clicked.connect(self.open_cam)
        self.mp4_detection_btn.clicked.connect(self.open_mp4)
        self.vid_stop_btn.clicked.connect(self.close_vid)
        vid_detection_layout.addWidget(vid_title)
        vid_detection_layout.addWidget(self.vid_img)
        self.vid_num_label = QLabel("当前检测结果：{}".format("等待检测"))
        self.vid_num_label.setFont(font_main)
        vid_detection_layout.addWidget(self.vid_num_label)
        vid_detection_layout.addWidget(self.webcam_detection_btn)
        vid_detection_layout.addWidget(self.mp4_detection_btn)
        vid_detection_layout.addWidget(self.vid_stop_btn)
        vid_detection_widget.setLayout(vid_detection_layout)

        about_widget = QWidget()
        about_layout = QVBoxLayout()
        about_title = QLabel(WELCOME_SENTENCE)
        about_title.setFont(QFont('楷体', 18))
        about_title.setAlignment(Qt.AlignCenter)
        about_img = QLabel()
        about_img.setPixmap(_create_placeholder_pixmap("YOLO11\n摔倒检测系统", 400, 200, bg_color=(48, 124, 208), text_color=(255, 255, 255)))
        self.model_label = QLabel("当前模型：{}".format(self.model_path))
        self.model_label.setFont(font_main)
        change_model_button = QPushButton("切换模型")
        change_model_button.setFont(font_main)
        change_model_button.setStyleSheet("QPushButton{color:white}"
                                          "QPushButton:hover{background-color: rgb(2,110,180);}"
                                          "QPushButton{background-color:rgb(48,124,208)}"
                                          "QPushButton{border:2px}"
                                          "QPushButton{border-radius:5px}"
                                          "QPushButton{padding:5px 5px}"
                                          "QPushButton{margin:5px 5px}")

        record_button = QPushButton("查看历史记录")
        record_button.setFont(font_main)
        record_button.clicked.connect(self.check_record)
        record_button.setStyleSheet("QPushButton{color:white}"
                                    "QPushButton:hover{background-color: rgb(2,110,180);}"
                                    "QPushButton{background-color:rgb(48,124,208)}"
                                    "QPushButton{border:2px}"
                                    "QPushButton{border-radius:5px}"
                                    "QPushButton{padding:5px 5px}"
                                    "QPushButton{margin:5px 5px}")
        change_model_button.clicked.connect(self.change_model)
        about_img.setAlignment(Qt.AlignCenter)
        label_super = QLabel("v1.0.0")
        label_super.setFont(QFont('楷体', 14))
        label_super.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(about_title)
        about_layout.addStretch()
        about_layout.addWidget(about_img)
        about_layout.addWidget(self.model_label)
        about_layout.addStretch()
        about_layout.addWidget(change_model_button)
        about_layout.addWidget(record_button)
        about_layout.addWidget(label_super)
        about_widget.setLayout(about_layout)
        self.left_img.setAlignment(Qt.AlignCenter)

        config_widget = QWidget()

        config_grid_widget = QWidget()
        config_grid_layout = QGridLayout()

        config_output_size_label = QLabel("系统图像显示大小")
        self.config_output_size_value = QLineEdit("")
        self.config_output_size_value.setText(str(self.output_size))
        config_grid_layout.addWidget(config_output_size_label, 0, 0)
        config_grid_layout.addWidget(self.config_output_size_value, 0, 1)


        config_vid_source_label = QLabel("摄像头源地址")
        self.config_vid_source_value = QLineEdit("")
        self.config_vid_source_value.setText(str(self.vid_source))
        config_grid_layout.addWidget(config_vid_source_label)
        config_grid_layout.addWidget(self.config_vid_source_value)

        config_vid_gap_label = QLabel("视频帧保存间隔")
        self.config_vid_gap_value = QLineEdit("")
        self.config_vid_gap_value.setText(str(self.vid_gap))
        config_grid_layout.addWidget(config_vid_gap_label)
        config_grid_layout.addWidget(self.config_vid_gap_value )

        config_conf_thres_label = QLabel("检测模型置信度阈值")
        self.config_conf_thres_value = QLineEdit("")
        self.config_conf_thres_value.setText(str(self.conf_thres))
        config_grid_layout.addWidget(config_conf_thres_label)
        config_grid_layout.addWidget(self.config_conf_thres_value)

        config_iou_thres_label = QLabel("检测模型IOU阈值")
        self.config_iou_thres_value = QLineEdit("")
        self.config_iou_thres_value.setText(str(self.iou_thres))
        config_grid_layout.addWidget(config_iou_thres_label)
        config_grid_layout.addWidget(self.config_iou_thres_value)

        config_save_txt_label = QLabel("推理时是否保存txt文件")
        self.config_save_txt_value = QRadioButton("True")
        self.config_save_txt_value.setChecked(False)
        self.config_save_txt_value.setAutoExclusive(False)
        config_grid_layout.addWidget(config_save_txt_label)
        config_grid_layout.addWidget(self.config_save_txt_value)

        config_save_conf_label = QLabel("推理时是否保存置信度")
        self.config_save_conf_value = QRadioButton("True")
        self.config_save_conf_value.setChecked(False)
        self.config_save_conf_value.setAutoExclusive(False)
        config_grid_layout.addWidget( config_save_conf_label)
        config_grid_layout.addWidget( self.config_save_conf_value)
        config_save_crop_label = QLabel("推理时是否保存切片文件")
        self.config_save_crop_value = QRadioButton("True")
        self.config_save_crop_value.setChecked(False)
        self.config_save_crop_value.setAutoExclusive(False)
        config_grid_layout.addWidget(config_save_crop_label)
        config_grid_layout.addWidget(self.config_save_crop_value)

        config_track_label = QLabel("追踪配置")
        self.config_track_value = QComboBox(self)
        self.config_track_value.addItems(['不开启追踪', "bytetrack.yaml", "botsort.yaml"])
        config_grid_layout.addWidget(config_track_label)
        config_grid_layout.addWidget(self.config_track_value)


        config_grid_widget.setLayout(config_grid_layout)
        config_grid_widget.setFont(font_main)

        save_config_button = QPushButton("保存配置信息")
        save_config_button.setFont(font_main)
        save_config_button.clicked.connect(self.save_config_change)
        save_config_button.setStyleSheet("QPushButton{color:white}"
                                    "QPushButton:hover{background-color: rgb(2,110,180);}"
                                    "QPushButton{background-color:rgb(48,124,208)}"
                                    "QPushButton{border:2px}"
                                    "QPushButton{border-radius:5px}"
                                    "QPushButton{padding:5px 5px}"
                                    "QPushButton{margin:5px 5px}")
        config_layout = QVBoxLayout()
        config_vid_title = QLabel("配置信息修改")
        config_icon_label = QLabel()
        config_icon_label.setPixmap(self.style().standardIcon(QStyle.SP_FileDialogDetailedView).pixmap(80, 80))
        config_icon_label.setAlignment(Qt.AlignCenter)
        config_vid_title.setAlignment(Qt.AlignCenter)
        config_vid_title.setFont(font_title)
        config_layout.addWidget(config_vid_title)
        config_layout.addWidget(config_icon_label)
        config_layout.addWidget(config_grid_widget)
        config_layout.addStretch()
        config_layout.addWidget(save_config_button)
        config_widget.setLayout(config_layout)


        style = self.style()
        self.addTab(about_widget, '主页')
        self.addTab(img_detection_widget, '图片检测')
        self.addTab(vid_detection_widget, '视频检测')
        self.addTab(config_widget, '配置信息')
        self.setTabIcon(0, style.standardIcon(QStyle.SP_ComputerIcon))
        self.setTabIcon(1, style.standardIcon(QStyle.SP_FileDialogContentsView))
        self.setTabIcon(2, style.standardIcon(QStyle.SP_MediaPlay))
        self.setTabIcon(3, style.standardIcon(QStyle.SP_FileDialogDetailedView))


    def upload_img(self):
        """上传图像，图像要尽可能保证是中文格式"""
        fileName, fileType = QFileDialog.getOpenFileName(self, 'Choose file', '', '*.jpg *.png *.tif *.jpeg') # 选择图像
        if fileName: # 如果存在文件名称则对图像进行处理
            suffix = fileName.split(".")[-1]
            save_path = osp.join("images/tmp", "tmp_upload." + suffix)  # 将图像转移到images目录下并且修改为英文的形式
            shutil.copy(fileName, save_path)
            im0 = cv2.imread(save_path)
            resize_scale = self.output_size / im0.shape[0]
            im0 = cv2.resize(im0, (0, 0), fx=resize_scale, fy=resize_scale)
            cv2.imwrite("images/tmp/upload_show_result.jpg", im0)
            self.img2predict = save_path                               # 给变量进行赋值方便后面实际进行读取
            self.left_img.setPixmap(QPixmap("images/tmp/upload_show_result.jpg"))
            self.right_img.setPixmap(_create_placeholder_pixmap("检测结果", 480, 360))
            self.img_num_label.setText("当前检测结果：待检测")

    def change_model(self):
        """切换模型，重新对self.model进行赋值"""
        fileName, fileType = QFileDialog.getOpenFileName(self, 'Choose file', '', '*.pt')
        if fileName:
            self.model_path = fileName
            self.model = self.model_load(weights=self.model_path)
            QMessageBox.information(self, "成功", "模型切换成功！")
            self.model_label.setText("当前模型：{}".format(self.model_path))

    def detect_img(self):
        """检测单张的图像文件"""
        if not self.img2predict:
            QMessageBox.warning(self, "提示", "请先上传图片！")
            return
        output_size = self.output_size
        print(self.save_txt)
        results = self.model(self.img2predict, conf=self.conf_thres, iou=self.iou_thres, save_txt=self.save_txt, save_conf=self.save_conf, save_crop=self.save_crop)  # 读取图像并执行检测的逻辑
        result = results[0]                     # 获取检测结果
        img_array = result.plot()               # 在图像上绘制检测结果
        im0 = img_array
        im_record = copy.deepcopy(im0)
        resize_scale = output_size / im0.shape[0]
        im0 = cv2.resize(im0, (0, 0), fx=resize_scale, fy=resize_scale)
        cv2.imwrite("images/tmp/single_result.jpg", im0)
        self.right_img.setPixmap(QPixmap("images/tmp/single_result.jpg"))
        time_re = str(time.strftime('result_%Y-%m-%d_%H-%M-%S_%A'))
        cv2.imwrite("record/img/{}.jpg".format(time_re), im_record)
        result_names = result.names
        result_nums = [0 for i in range(0, len(result_names))]
        cls_ids = list(result.boxes.cls.cpu().numpy())
        for cls_id in cls_ids:
            result_nums[int(cls_id)] = result_nums[int(cls_id)] + 1
        result_info = ""
        for idx_cls, cls_num in enumerate(result_nums):
            if cls_num > 0:
                result_info = result_info + "{}:{}\n".format(result_names[idx_cls], cls_num)
        self.img_num_label.setText("当前检测结果\n{}".format(result_info))
        QMessageBox.information(self, "检测成功", "日志已保存！")

    def open_cam(self):
        """打开摄像头上传"""
        self.webcam_detection_btn.setEnabled(False)    # 将打开摄像头的按钮设置为false，防止用户误触
        self.mp4_detection_btn.setEnabled(False)       # 将打开mp4文件的按钮设置为false，防止用户误触
        self.vid_stop_btn.setEnabled(True)             # 将关闭按钮打开，用户可以随时点击关闭按钮关闭实时的检测任务
        if str(self.vid_source).isdigit():
            self.vid_source = int(self.vid_source)
        self.webcam = True                             # 将实时摄像头设置为true
        print(f"当前实时源：{self.vid_source}")
        self.cap = cv2.VideoCapture(self.vid_source)   # 初始化摄像头的对象
        th = threading.Thread(target=self.detect_vid)  # 初始化视频检测线程
        th.start()                                     # 启动线程进行检测

    def open_mp4(self):
        """打开mp4文件上传"""
        fileName, fileType = QFileDialog.getOpenFileName(self, 'Choose file', '', '*.mp4 *.avi')
        if fileName:
            self.webcam_detection_btn.setEnabled(False)
            self.mp4_detection_btn.setEnabled(False)
            self.vid_source = fileName
            self.webcam = False
            self.cap = cv2.VideoCapture(self.vid_source)
            th = threading.Thread(target=self.detect_vid)
            th.start()

    def detect_vid(self):
        """检测视频文件，这里的视频文件包含了mp4格式的视频文件和摄像头形式的视频文件"""
        vid_i = 0
        track_history = defaultdict(lambda: [])
        while self.cap.isOpened():
            success, frame = self.cap.read()
            if success:
                if self.config_track_value.currentText() == "不开启追踪":

                    results = self.model(frame, conf=self.conf_thres, iou=self.iou_thres, save_txt=self.save_txt, save_conf=self.save_conf, save_crop=self.save_crop)
                    result = results[0]
                    img_array = result.plot()
                    im0 = img_array
                    im_record = copy.deepcopy(im0)
                    resize_scale = self.output_size / im0.shape[0]
                    im0 = cv2.resize(im0, (0, 0), fx=resize_scale, fy=resize_scale)
                    cv2.imwrite("images/tmp/single_result_vid.jpg", im0)
                    self.vid_img.setPixmap(QPixmap("images/tmp/single_result_vid.jpg"))
                    time_re = str(time.strftime('result_%Y-%m-%d_%H-%M-%S_%A'))
                    if vid_i % self.vid_gap == 0:
                        cv2.imwrite("record/vid/{}.jpg".format(time_re), im_record)
                    result_names = result.names
                    result_nums = [0 for i in range(0, len(result_names))]
                    cls_ids = list(result.boxes.cls.cpu().numpy())
                    for cls_id in cls_ids:
                        result_nums[int(cls_id)] = result_nums[int(cls_id)] + 1
                    result_info = ""
                    for idx_cls, cls_num in enumerate(result_nums):
                        if cls_num > 0:
                            result_info = result_info + "{}:{}\n".format(result_names[idx_cls], cls_num)
                    self.vid_num_label.setText("当前检测结果：\n{}".format(result_info))
                    vid_i = vid_i + 1
                else:
                    results = self.model.track(frame,  conf=self.conf_thres, iou=self.iou_thres, save_txt=self.save_txt,
                                         save_conf=self.save_conf, save_crop=self.save_crop, tracker=self.config_track_value.currentText(), persist=True)
                    result = results[0]
                    img_array = result.plot()
                    try:
                        boxes = results[0].boxes.xywh.cpu()
                        track_ids = results[0].boxes.id.int().cpu().tolist()

                        for box, track_id in zip(boxes, track_ids):
                            x, y, w, h = box
                            track = track_history[track_id]
                            track.append((float(x), float(y)))  # x, y center point
                            if len(track) > 30:  # retain 90 tracks for 90 frames
                                track.pop(0)

                            points = np.hstack(track).astype(np.int32).reshape((-1, 1, 2))
                            cv2.polylines(img_array, [points], isClosed=False, color=(0, 0, 230),
                                          thickness=5)
                    except:
                        print("not got targets")
                    im0 = img_array
                    im_record = copy.deepcopy(im0)
                    resize_scale = self.output_size / im0.shape[0]
                    im0 = cv2.resize(im0, (0, 0), fx=resize_scale, fy=resize_scale)
                    cv2.imwrite("images/tmp/single_result_vid.jpg", im0)
                    self.vid_img.setPixmap(QPixmap("images/tmp/single_result_vid.jpg"))
                    time_re = str(time.strftime('result_%Y-%m-%d_%H-%M-%S_%A'))
                    if vid_i % self.vid_gap == 0:
                        cv2.imwrite("record/vid/{}.jpg".format(time_re), im_record)
                    result_names = result.names
                    result_nums = [0 for i in range(0, len(result_names))]
                    cls_ids = list(result.boxes.cls.cpu().numpy())
                    for cls_id in cls_ids:
                        result_nums[int(cls_id)] = result_nums[int(cls_id)] + 1
                    result_info = ""
                    for idx_cls, cls_num in enumerate(result_nums):
                        if cls_num > 0:
                            result_info = result_info + "{}:{}\n".format(result_names[idx_cls], cls_num)
                    self.vid_num_label.setText("当前检测结果：\n{}".format(result_info))
                    vid_i = vid_i + 1
            if cv2.waitKey(1) & self.stopEvent.is_set() == True:
                self.stopEvent.clear()
                self.webcam_detection_btn.setEnabled(True)
                self.mp4_detection_btn.setEnabled(True)
                if self.cap is not None:
                    self.cap.release()
                    cv2.destroyAllWindows()
                self.reset_vid()
                break

    def reset_vid(self):
        """重置摄像头内容"""
        self.webcam_detection_btn.setEnabled(True)                      # 打开摄像头检测的按钮
        self.mp4_detection_btn.setEnabled(True)                         # 打开视频文件检测的按钮
        self.vid_img.setPixmap(_create_placeholder_pixmap("视频检测", 480, 360))  # 重新设置视频检测页面的初始化图像
        self.webcam = True                                              # 重新将摄像头设置为true
        self.vid_num_label.setText("当前检测结果：{}".format("等待检测"))   # 重新设置视频检测页面的文字内容

    def close_vid(self):
        """关闭摄像头"""
        self.stopEvent.set()
        self.reset_vid()


    def check_record(self):
        """打开历史记录文件夹"""
        os.startfile(osp.join(os.path.abspath(os.path.dirname(__file__)), "record"))

    def save_config_change(self):
        print("保存配置修改的结果")
        try:
            self.output_size = int(self.config_output_size_value.text())
            self.vid_source = str(self.config_vid_source_value.text())
            print(f"源地址:{self.vid_source}")
            self.vid_gap = int(self.config_vid_gap_value.text())
            self.conf_thres = float(self.config_conf_thres_value.text())
            self.iou_thres = float(self.config_iou_thres_value.text())
            self.save_txt = self.config_save_txt_value.isChecked()
            self.save_conf = self.config_save_conf_value.isChecked()
            self.save_crop = self.config_save_crop_value.isChecked()

            QMessageBox.information(self, "配置文件保存成功", "配置文件保存成功")
        except:
            QMessageBox.warning(self, "配置文件保存失败", "配置文件保存失败")



    def closeEvent(self, event):
        """用户退出事件"""
        reply = QMessageBox.question(self,
                                     'quit',
                                     "Are you sure?",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                if self.cap is not None:
                    self.cap.release()
                    print("摄像头已释放")
            except:
                pass
            self.close()
            event.accept()
        else:
            event.ignore()
class LoginWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        font_title = QFont('楷体', 16)
        self.setWindowTitle("YOLO11 摔倒检测 - 登录")
        self.resize(800, 600)
        mid_widget = QWidget()
        window_layout = QFormLayout()
        self.user_name = QLineEdit()
        self.u_password = QLineEdit()
        window_layout.addRow("账 号：", self.user_name)
        window_layout.addRow("密 码：", self.u_password)
        self.user_name.setEchoMode(QLineEdit.Normal)
        self.u_password.setEchoMode(QLineEdit.Password)
        mid_widget.setLayout(window_layout)

        main_layout = QVBoxLayout()
        a = QLabel("欢迎使用 YOLO11 摔倒检测系统")
        a.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(a)
        main_layout.addWidget(mid_widget)

        login_button = QPushButton("立即登陆")
        login_button.clicked.connect(self.login)

        main_layout.addWidget(login_button)

        self.setLayout(main_layout)

        self.mainWindow = MainWindow()
        self.setFont(font_title)


    def login(self):
        user_name = self.user_name.text()
        pwd = self.u_password.text()
        is_ok = (user_name == USERNAME) and (pwd == PASSWORD)

        print(is_ok)
        if is_ok:
            self.mainWindow.show()
            self.close()
        else:
            QMessageBox.warning(self, "账号密码不匹配", "请输入正确的账号密码")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = LoginWindow()
    mainWindow.show()
    sys.exit(app.exec())