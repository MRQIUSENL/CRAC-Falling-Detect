const api = require('../../utils/api');

Page({
  data: {
    serverOnline: null,
    currentModel: '',
    checking: false,
    features: [
      { icon: '🎯', title: 'YOLO11 高精度检测模型' },
      { icon: '⚡', title: '实时推理，毫秒级响应' },
      { icon: '🎥', title: '支持 ByteTrack / BoT-SORT 追踪' },
      { icon: '📊', title: '检测结果可视化展示' },
      { icon: '🔧', title: '可调置信度与 IoU 阈值' },
      { icon: '📱', title: '专为移动端优化' }
    ]
  },

  onLoad() {
    const app = getApp();
    this.setData({ currentModel: app.globalData.currentModel || '' });
    setTimeout(() => this.checkServerStatus(), 300);
  },

  onShow() {
    const app = getApp();
    this.setData({ currentModel: app.globalData.currentModel || '' });
    if (this.data.serverOnline === null) this.checkServerStatus();
  },

  async checkServerStatus() {
    if (this.data.checking) return;
    this.setData({ checking: true });
    try {
      await api.healthCheck();
      this.setData({ serverOnline: true });
    } catch (e) {
      this.setData({ serverOnline: false });
    } finally {
      this.setData({ checking: false });
    }
  },

  refreshStatus() { this.checkServerStatus(); },

  navigateTo(e) {
    const url = e.currentTarget.dataset.page;
    // license 页面不在 tabBar 中，用 navigateTo
    if (url.includes('license')) {
      wx.navigateTo({ url });
    } else {
      wx.switchTab({ url });
    }
  },

  onPullDownRefresh() {
    this.checkServerStatus().then(() => wx.stopPullDownRefresh());
  }
});
