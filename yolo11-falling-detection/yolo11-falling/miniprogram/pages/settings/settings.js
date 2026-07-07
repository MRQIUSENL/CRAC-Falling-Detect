/**
 * 设置页面逻辑
 */

const api = require('../../utils/api');

Page({
  data: {
    // 后端连接
    apiBaseUrl: '',
    serverOnline: false,

    // 检测默认参数
    defaultConfThreshold: 0.25,
    defaultIouThreshold: 0.45,
    trackerOptions: ['不开启追踪', 'ByteTrack', 'BoT-SORT'],
    defaultTrackerIndex: 0,
    trackerValues: ['', 'bytetrack.yaml', 'botsort.yaml'],

    // 模型
    currentModel: '',
    modelList: []
  },

  onLoad() {
    this.loadCurrentSettings();
  },

  onShow() {
    this.loadCurrentSettings();
    this.refreshModels();
    this.checkConnection();
  },

  // 从全局加载当前设置
  loadCurrentSettings() {
    const app = getApp();
    const trackerIndex = this.data.trackerValues.indexOf(
      app.globalData.trackerType
    );
    this.setData({
      apiBaseUrl: app.globalData.apiBaseUrl,
      defaultConfThreshold: app.globalData.confThreshold,
      defaultIouThreshold: app.globalData.iouThreshold,
      defaultTrackerIndex: trackerIndex >= 0 ? trackerIndex : 0,
      currentModel: app.globalData.currentModel
    });
  },

  // 测试后端连接
  async checkConnection() {
    try {
      await api.healthCheck();
      this.setData({ serverOnline: true });
    } catch (e) {
      this.setData({ serverOnline: false });
    }
  },

  // 刷新模型列表
  async refreshModels() {
    try {
      const res = await api.getModels();
      if (res.success && res.models) {
        this.setData({
          modelList: res.models,
          currentModel: res.current_model || this.data.currentModel
        });
        // 同步到全局
        if (res.current_model) {
          const app = getApp();
          app.globalData.currentModel = res.current_model;
        }
      }
    } catch (e) {
      console.error('获取模型列表失败:', e);
    }
  },

  // 切换模型
  async switchModel(e) {
    const modelName = e.currentTarget.dataset.name;
    if (modelName === this.data.currentModel) return;

    wx.showModal({
      title: '切换模型',
      content: `确定切换到模型 "${modelName}" 吗？`,
      success: async (res) => {
        if (res.confirm) {
          try {
            const result = await api.switchModel(modelName);
            if (result.success) {
              const app = getApp();
              app.globalData.currentModel = modelName;
              app.saveSettings();
              this.setData({ currentModel: modelName });
              wx.showToast({ title: '模型切换成功', icon: 'success' });
            }
          } catch (e) {
            wx.showToast({ title: e.message || '切换失败', icon: 'none' });
          }
        }
      }
    });
  },

  // 保存所有设置
  saveAllSettings() {
    const app = getApp();

    // 更新全局数据
    app.globalData.apiBaseUrl = this.data.apiBaseUrl;
    app.globalData.confThreshold = this.data.defaultConfThreshold;
    app.globalData.iouThreshold = this.data.defaultIouThreshold;
    app.globalData.trackerType = this.data.trackerValues[this.data.defaultTrackerIndex];

    // 持久化保存
    app.saveSettings();

    wx.showToast({
      title: '设置已保存',
      icon: 'success'
    });
  },

  // 输入变化
  onApiUrlInput(e) {
    this.setData({ apiBaseUrl: e.detail.value });
  },

  onConfChange(e) {
    this.setData({ defaultConfThreshold: e.detail.value });
  },

  onIouChange(e) {
    this.setData({ defaultIouThreshold: e.detail.value });
  },

  onTrackerChange(e) {
    this.setData({ defaultTrackerIndex: parseInt(e.detail.value) });
  },

  onShareAppMessage() {
    return {
      title: '摔倒检测工具 - 设置',
      path: '/pages/settings/settings'
    };
  }
});
