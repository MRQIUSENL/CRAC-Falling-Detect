const storage = require('../../utils/storage');

Page({
  data: { historyList: [] },

  onShow() { this.loadHistory(); },

  loadHistory() {
    const list = storage.getHistory();
    this.setData({
      historyList: list.map(item => ({
        ...item,
        timestamp: this.fmtTime(item.timestamp)
      }))
    });
  },

  fmtTime(iso) {
    try {
      const d = new Date(iso);
      const p = n => String(n).padStart(2, '0');
      return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
    } catch (e) { return iso || ''; }
  },

  viewDetail(e) {
    const record = storage.getRecordById(e.currentTarget.dataset.id);
    if (!record) return;

    let txt = `目标: ${record.totalObjects} | ${record.inferenceTimeMs}ms\n\n`;
    if (record.counts && Object.keys(record.counts).length) {
      Object.entries(record.counts).forEach(([k, v]) => txt += `  ${k}: ${v}\n`);
    }
    if (record.detections && record.detections.length) {
      txt += '\n详细:\n';
      record.detections.slice(0, 8).forEach(d =>
        txt += `  ${d.class} - ${(d.confidence*100).toFixed(1)}%\n`
      );
      if (record.detections.length > 8) txt += `  ... 还有 ${record.detections.length-8} 项\n`;
    }

    wx.showModal({ title: '检测详情', content: txt, showCancel: false, confirmText: '关闭' });
  },

  deleteItem(e) {
    wx.showModal({
      title: '删除', content: '确定删除这条记录？',
      success: res => {
        if (res.confirm) { storage.removeHistory(e.currentTarget.dataset.id); this.loadHistory(); }
      }
    });
  },

  clearAll() {
    wx.showModal({
      title: '清空全部', content: '此操作不可恢复', confirmColor: '#EF4444',
      success: res => {
        if (res.confirm) { storage.clearHistory(); this.setData({ historyList: [] }); }
      }
    });
  },

  goToDetect() { wx.switchTab({ url: '/pages/detect/detect' }); },

  onPullDownRefresh() { this.loadHistory(); wx.stopPullDownRefresh(); }
});
