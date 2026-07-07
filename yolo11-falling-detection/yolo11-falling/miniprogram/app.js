// 摔倒检测工具 - 微信小程序
// 全局应用逻辑

App({
  // 全局数据
  globalData: {
    // 后端 API 地址 (开发环境)
    apiBaseUrl: 'http://127.0.0.1:8001',

    // 默认检测参数
    confThreshold: 0.40,
    iouThreshold: 0.45,
    trackerType: '',

    // 当前模型
    currentModel: '',

    // 后端连接状态
    serverOnline: false
  },

  onLaunch() {
    console.log('摔倒检测工具启动');
    // 从本地存储恢复设置
    this.loadSettings();
    // 自动检测后端连接
    this.checkServer();
  },

  /** 检测后端服务是否可达 */
  checkServer() {
    const baseUrl = this.globalData.apiBaseUrl;
    wx.request({
      url: `${baseUrl}/health`,
      method: 'GET',
      timeout: 3000,
      success: (res) => {
        if (res.statusCode === 200 && res.data && res.data.status === 'ok') {
          this.globalData.serverOnline = true;
          console.log('[启动] 后端连接成功');
          return;
        }
        this.globalData.serverOnline = false;
        this.showServerOffline();
      },
      fail: () => {
        this.globalData.serverOnline = false;
        this.showServerOffline();
      }
    });
  },

  /** 后端不可用时的提示 */
  showServerOffline() {
    wx.showModal({
      title: '后端未连接',
      content: '无法连接到后端检测服务，请先运行 start_backend.bat 启动后端，再重新进入小程序。',
      showCancel: false,
      confirmText: '我知道了'
    });
    console.warn('[启动] 后端连接失败');
  },

  // 从本地存储加载设置
  loadSettings() {
    try {
      const settings = wx.getStorageSync('app_settings');
      if (settings) {
        if (settings.apiBaseUrl) this.globalData.apiBaseUrl = settings.apiBaseUrl;
        if (settings.confThreshold !== undefined) this.globalData.confThreshold = settings.confThreshold;
        if (settings.iouThreshold !== undefined) this.globalData.iouThreshold = settings.iouThreshold;
        if (settings.trackerType !== undefined) this.globalData.trackerType = settings.trackerType;
        if (settings.currentModel) this.globalData.currentModel = settings.currentModel;
      }
    } catch (e) {
      console.error('加载设置失败:', e);
    }
  },

  // 保存设置到本地存储
  saveSettings() {
    try {
      wx.setStorageSync('app_settings', {
        apiBaseUrl: this.globalData.apiBaseUrl,
        confThreshold: this.globalData.confThreshold,
        iouThreshold: this.globalData.iouThreshold,
        trackerType: this.globalData.trackerType,
        currentModel: this.globalData.currentModel
      });
    } catch (e) {
      console.error('保存设置失败:', e);
    }
  }
});
