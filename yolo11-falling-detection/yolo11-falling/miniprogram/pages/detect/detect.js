/**
 * 图片检测页面逻辑
 */

const api = require('../../utils/api');
const storage = require('../../utils/storage');

Page({
  data: {
    // 图片
    selectedImage: '',       // 用户选择的原图路径
    annotatedImage: '',      // 标注后的结果图片(base64)

    // 检测参数
    confThreshold: 0.25,
    iouThreshold: 0.45,
    trackerOptions: ['不开启追踪', 'ByteTrack', 'BoT-SORT'],
    trackerIndex: 0,
    trackerValues: ['', 'bytetrack.yaml', 'botsort.yaml'],

    // 状态
    detecting: false,
    detectionResult: null,
    countsArray: []
  },

  onLoad() {
    // 从全局配置加载参数
    const app = getApp();
    this.setData({
      confThreshold: app.globalData.confThreshold,
      iouThreshold: app.globalData.iouThreshold
    });
  },

  onShow() {
    const app = getApp();
    this.setData({
      confThreshold: app.globalData.confThreshold,
      iouThreshold: app.globalData.iouThreshold
    });
  },

  // 选择图片
  chooseImage() {
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],  // 压缩图以减少上传时间
      sourceType: ['album', 'camera'],
      success: (res) => {
        this.setData({
          selectedImage: res.tempFilePaths[0],
          annotatedImage: '',
          detectionResult: null,
          countsArray: []
        });
      },
      fail: (err) => {
        if (err.errMsg !== 'chooseImage:fail cancel') {
          wx.showToast({ title: '选择图片失败', icon: 'none' });
        }
      }
    });
  },

  // 开始检测
  async startDetect() {
    if (!this.data.selectedImage) {
      wx.showToast({ title: '请先选择图片', icon: 'none' });
      return;
    }

    this.setData({ detecting: true });

    try {
      const result = await api.detectImage(this.data.selectedImage, {
        confThreshold: this.data.confThreshold,
        iouThreshold: this.data.iouThreshold,
        tracker: this.data.trackerValues[this.data.trackerIndex]
      });

      if (result.success) {
        // 构建 counts 数组用于显示
        const countsArray = Object.entries(result.counts || {}).map(
          ([name, count]) => ({ name, count })
        );

        // 格式化检测结果（WXML 不支持 .toFixed 等方法调用）
        const formattedDetections = (result.detections || []).map(d => ({
          ...d,
          confidence_pct: (d.confidence * 100).toFixed(1),
          bbox_str: d.bbox.map(v => Math.round(v)).join(', ')
        }));

        this.setData({
          annotatedImage: result.annotated_image,
          detectionResult: Object.assign({}, result, { detections: formattedDetections }),
          countsArray: countsArray
        });

        // 保存到历史记录
        storage.addHistory({
          imageUrl: this.data.selectedImage,
          annotatedImage: result.annotated_image,
          detections: result.detections,
          counts: result.counts,
          totalObjects: result.total_objects,
          inferenceTimeMs: result.inference_time_ms,
          params: {
            confThreshold: this.data.confThreshold,
            iouThreshold: this.data.iouThreshold,
            tracker: this.data.trackerOptions[this.data.trackerIndex]
          }
        });

        wx.showToast({
          title: `检测到 ${result.total_objects} 个目标`,
          icon: 'success'
        });
      } else {
        wx.showToast({
          title: result.error || '检测失败',
          icon: 'none'
        });
      }
    } catch (e) {
      console.error('检测失败:', e);
      wx.showToast({
        title: e.message || '检测失败，请检查后端服务',
        icon: 'none',
        duration: 3000
      });
    } finally {
      this.setData({ detecting: false });
    }
  },

  // 清空图片
  clearImage() {
    this.setData({
      selectedImage: '',
      annotatedImage: '',
      detectionResult: null,
      countsArray: []
    });
  },

  // 参数变化
  onConfChange(e) {
    this.setData({ confThreshold: e.detail.value });
  },

  onIouChange(e) {
    this.setData({ iouThreshold: e.detail.value });
  },

  onTrackerChange(e) {
    this.setData({ trackerIndex: parseInt(e.detail.value) });
  },

  // 分享
  onShareAppMessage() {
    return {
      title: '摔倒检测工具 - 图片检测',
      path: '/pages/detect/detect'
    };
  }
});
