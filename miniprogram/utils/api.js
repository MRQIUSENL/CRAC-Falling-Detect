/**
 * API 请求工具
 * 封装 wx.request，统一处理请求、响应和错误
 */

/**
 * 获取 API 基础地址
 * 注意：每次调用时动态获取 app 实例，避免模块加载时 App() 未初始化
 */
function getBaseUrl() {
  const app = getApp();
  return (app && app.globalData && app.globalData.apiBaseUrl)
    ? app.globalData.apiBaseUrl
    : 'http://localhost:8001';
}

/**
 * 通用请求方法
 * @param {Object} options - 请求配置
 * @returns {Promise}
 */
function request(options) {
  const baseUrl = getBaseUrl();
  const url = `${baseUrl}${options.url}`;

  return new Promise((resolve, reject) => {
    // 显示加载提示 (可选)
    if (options.showLoading !== false) {
      wx.showLoading({
        title: options.loadingTitle || '加载中...',
        mask: true
      });
    }

    wx.request({
      url: url,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        ...options.header
      },
      timeout: options.timeout || 30000,
      success: (res) => {
        wx.hideLoading();
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          const errMsg = res.data?.error || `请求失败 (${res.statusCode})`;
          reject(new Error(errMsg));
        }
      },
      fail: (err) => {
        wx.hideLoading();
        // 网络错误处理
        if (err.errMsg.includes('timeout')) {
          reject(new Error('请求超时，请检查网络连接'));
        } else if (err.errMsg.includes('fail')) {
          reject(new Error('网络连接失败，请检查后端服务是否启动'));
        } else {
          reject(new Error(err.errMsg || '请求失败'));
        }
      }
    });
  });
}

/**
 * 上传文件请求
 * @param {Object} options - 上传配置
 * @returns {Promise}
 */
function uploadFile(options) {
  const baseUrl = getBaseUrl();
  const url = `${baseUrl}${options.url}`;

  return new Promise((resolve, reject) => {
    wx.showLoading({
      title: options.loadingTitle || '检测中...',
      mask: true
    });

    wx.uploadFile({
      url: url,
      filePath: options.filePath,
      name: options.name || 'image',
      formData: options.formData || {},
      timeout: options.timeout || 60000,
      success: (res) => {
        wx.hideLoading();
        try {
          const data = JSON.parse(res.data);
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(data);
          } else {
            reject(new Error(data.error || `请求失败 (${res.statusCode})`));
          }
        } catch (e) {
          reject(new Error('返回数据解析失败'));
        }
      },
      fail: (err) => {
        wx.hideLoading();
        if (err.errMsg.includes('timeout')) {
          reject(new Error('请求超时，请检查网络连接'));
        } else {
          reject(new Error('网络连接失败，请检查后端服务是否启动'));
        }
      }
    });
  });
}

/**
 * 图片检测 - 上传图片文件
 * @param {string} imagePath - 图片本地路径
 * @param {Object} params - 检测参数
 * @returns {Promise}
 */
function detectImage(imagePath, params = {}) {
  const appInstance = getApp();
  return uploadFile({
    url: '/api/detect/image',
    filePath: imagePath,
    name: 'image',
    formData: {
      conf_threshold: params.confThreshold ?? appInstance.globalData.confThreshold,
      iou_threshold: params.iouThreshold ?? appInstance.globalData.iouThreshold,
      tracker: (params.tracker ?? appInstance.globalData.trackerType) || ''
    },
    loadingTitle: '正在检测...',
    timeout: 60000
  });
}

/**
 * 摄像头帧检测 - 发送 Base64 图像
 * @param {string} base64Frame - Base64 编码的图像帧
 * @param {Object} params - 检测参数
 * @returns {Promise}
 */
function detectCameraFrame(base64Frame, params = {}) {
  const appInstance = getApp();
  return request({
    url: '/api/detect/camera_frame',
    method: 'POST',
    header: { 'content-type': 'application/json' },
    data: {
      frame: base64Frame,
      conf_threshold: params.confThreshold ?? appInstance.globalData.confThreshold,
      iou_threshold: params.iouThreshold ?? appInstance.globalData.iouThreshold,
      tracker: (params.tracker ?? appInstance.globalData.trackerType) || ''
    },
    showLoading: false
  });
}

/**
 * 获取可用模型列表
 * @returns {Promise}
 */
function getModels() {
  return request({
    url: '/api/detect/models',
    method: 'GET'
  });
}

/**
 * 切换模型
 * @param {string} modelName - 模型名称
 * @returns {Promise}
 */
function switchModel(modelName) {
  return request({
    url: '/api/detect/models/switch',
    method: 'POST',
    header: { 'content-type': 'application/json' },
    data: { model_name: modelName },
    loadingTitle: '切换模型中...'
  });
}

/**
 * 健康检查
 * @returns {Promise}
 */
function healthCheck() {
  return request({
    url: '/health',
    method: 'GET',
    showLoading: false,
    timeout: 5000
  });
}

module.exports = {
  request,
  uploadFile,
  detectImage,
  detectCameraFrame,
  getModels,
  switchModel,
  healthCheck
};
