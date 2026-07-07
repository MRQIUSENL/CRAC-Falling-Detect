/**
 * 本地存储工具
 * 封装 wx.Storage 操作，用于管理检测历史记录
 */

const HISTORY_KEY = 'detection_history';
const MAX_HISTORY = 100; // 最多保存 100 条记录

/**
 * 获取所有历史记录
 * @returns {Array}
 */
function getHistory() {
  try {
    const data = wx.getStorageSync(HISTORY_KEY);
    return data || [];
  } catch (e) {
    console.error('读取历史记录失败:', e);
    return [];
  }
}

/**
 * 添加一条检测记录
 * @param {Object} record - 检测记录
 * @param {string} record.id - 唯一ID
 * @param {string} record.imageUrl - 原图路径(本地)
 * @param {string} record.annotatedImage - 标注后的图片(base64)
 * @param {Array} record.detections - 检测结果列表
 * @param {Object} record.counts - 各类别计数
 * @param {number} record.inferenceTimeMs - 推理耗时
 * @param {string} record.timestamp - 时间戳
 * @param {Object} record.params - 检测参数
 */
function addHistory(record) {
  try {
    const history = getHistory();

    // 添加新记录到开头
    history.unshift({
      id: record.id || generateId(),
      imageUrl: record.imageUrl || '',
      annotatedImage: record.annotatedImage || '',
      detections: record.detections || [],
      counts: record.counts || {},
      totalObjects: record.totalObjects || 0,
      inferenceTimeMs: record.inferenceTimeMs || 0,
      timestamp: record.timestamp || new Date().toISOString(),
      params: record.params || {}
    });

    // 限制最大记录数
    if (history.length > MAX_HISTORY) {
      history.splice(MAX_HISTORY);
    }

    wx.setStorageSync(HISTORY_KEY, history);
    return true;
  } catch (e) {
    console.error('保存历史记录失败:', e);
    return false;
  }
}

/**
 * 删除指定记录
 * @param {string} id - 记录ID
 */
function removeHistory(id) {
  try {
    const history = getHistory();
    const filtered = history.filter(item => item.id !== id);
    wx.setStorageSync(HISTORY_KEY, filtered);
    return true;
  } catch (e) {
    console.error('删除历史记录失败:', e);
    return false;
  }
}

/**
 * 清空所有历史记录
 */
function clearHistory() {
  try {
    wx.setStorageSync(HISTORY_KEY, []);
    return true;
  } catch (e) {
    console.error('清空历史记录失败:', e);
    return false;
  }
}

/**
 * 获取单条记录
 * @param {string} id - 记录ID
 * @returns {Object|null}
 */
function getRecordById(id) {
  const history = getHistory();
  return history.find(item => item.id === id) || null;
}

/**
 * 生成唯一ID
 */
function generateId() {
  return 'det_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

module.exports = {
  getHistory,
  addHistory,
  removeHistory,
  clearHistory,
  getRecordById
};
