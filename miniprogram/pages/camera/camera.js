/**
 * 实时检测页面 — 摔倒告警逻辑
 * 检测到摔倒后持续超过 10s 自动触发警告
 */

const api = require('../../utils/api');
const storage = require('../../utils/storage');

const FALL_ALERT_THRESHOLD = 10;       // 摔倒持续多少秒触发告警
const FALL_ALERT_COOLDOWN = 30;        // 告警冷却时间（秒）
const FALL_CONFIRM_FRAMES = 3;         // 连续多少帧检测到摔倒才确认
const FALL_HIGH_CONF = 0.5;            // 高置信度阈值（单帧即可确认），防止重复告警

Page({
  data: {
    cameraOpened: false,
    detecting: false,
    manualDetecting: false,

    interval: 1000,
    confThreshold: 0.40,
    iouThreshold: 0.45,
    trackerOptions: ['不开启追踪', 'ByteTrack', 'BoT-SORT'],
    trackerIndex: 0,
    trackerValues: ['', 'bytetrack.yaml', 'botsort.yaml'],

    lastResult: null,
    annotatedFrame: '',
    countsArray: [],

    autoTimer: null,
    frameCount: 0,

    // 摔倒告警状态
    fallActive: false,
    fallDuration: 0,
    warningTriggered: false,
    demoRunning: false,
  },

  onLoad() {
    const app = getApp();
    this.setData({
      confThreshold: app.globalData.confThreshold,
      iouThreshold: app.globalData.iouThreshold
    });
  },

  onUnload() { this.stopAutoDetect(); this.stopDemo(); },
  onHide()   { this.stopAutoDetect(); },

  // ==================== 摄像头控制 ====================

  toggleCamera() {
    if (this.data.cameraOpened) {
      this.stopAutoDetect();
      this.stopDemo();
      this.resetFallState();
      this.setData({
        cameraOpened: false, detecting: false,
        lastResult: null, annotatedFrame: '', countsArray: [],
        demoRunning: false
      });
    } else {
      this.setData({ cameraOpened: true });
    }
  },

  onCameraError(e) {
    wx.showModal({
      title: '摄像头错误',
      content: '无法打开摄像头，请检查权限设置',
      showCancel: false
    });
    this.setData({ cameraOpened: false });
  },

  toggleAutoDetect() {
    this.data.detecting ? this.stopAutoDetect() : this.startAutoDetect();
  },

  startAutoDetect() {
    this.setData({ detecting: true });
    this.captureAndDetect();
    const timer = setInterval(() => this.captureAndDetect(), this.data.interval);
    this.setData({ autoTimer: timer });
  },

  stopAutoDetect() {
    if (this.data.autoTimer) {
      clearInterval(this.data.autoTimer);
      this.setData({ detecting: false, autoTimer: null });
    }
  },

  async captureOnce() {
    if (this.data.manualDetecting) return;
    this.setData({ manualDetecting: true });
    await this.captureAndDetect();
    this.setData({ manualDetecting: false });
  },

  // ==================== 核心检测逻辑 ====================

  async captureAndDetect() {
    if (!this.data.cameraOpened) return;

    try {
      const ctx = wx.createCameraContext();
      const res = await new Promise((resolve, reject) => {
        ctx.takePhoto({ quality: 'low', success: resolve, fail: reject });
      });

      const fs = wx.getFileSystemManager();
      const base64Data = fs.readFileSync(res.tempImagePath, 'base64');
      const base64Frame = `data:image/jpeg;base64,${base64Data}`;

      const result = await api.detectCameraFrame(base64Frame, {
        confThreshold: this.data.confThreshold,
        iouThreshold: this.data.iouThreshold,
        tracker: this.data.trackerValues[this.data.trackerIndex]
      });

      if (result.success) {
        const countsArray = Object.entries(result.counts || {}).map(
          ([name, count]) => ({ name, count })
        );

        this.setData({
          lastResult: result,
          annotatedFrame: result.annotated_image,
          countsArray: countsArray,
          frameCount: this.data.frameCount + 1
        });

        // 摔倒告警判定
        this.evaluateFallAlert(result.counts);

        // 历史记录
        if (this.data.frameCount % 30 === 0 && result.total_objects > 0) {
          storage.addHistory({
            imageUrl: res.tempImagePath,
            annotatedImage: result.annotated_image,
            detections: result.detections,
            counts: result.counts,
            totalObjects: result.total_objects,
            inferenceTimeMs: result.inference_time_ms,
            params: {
              confThreshold: this.data.confThreshold,
              iouThreshold: this.data.iouThreshold,
              tracker: this.data.trackerOptions[this.data.trackerIndex],
              source: 'camera'
            }
          });
        }
      }
    } catch (e) {
      console.error('帧检测失败:', e);
    }
  },

  // ==================== 摔倒告警逻辑 ====================

  evaluateFallAlert(counts) {
    const hasFall = counts && counts['摔倒'] && counts['摔倒'] > 0;
    const hasHighConfFall = hasFall && this.data.lastResult &&
      this.data.lastResult.detections.some(
        d => d.class === '摔倒' && d.confidence >= FALL_HIGH_CONF
      );
    const now = Date.now();

    if (hasFall) {
      this._consecutiveFall = (this._consecutiveFall || 0) + 1;

      // 需连续 N 帧 或 单帧高置信度才确认摔倒
      const confirmed = this._consecutiveFall >= FALL_CONFIRM_FRAMES || hasHighConfFall;

      if (confirmed && !this.data.fallActive) {
        this._fallStartTime = now;
        this.setData({ fallActive: true, fallDuration: 0, warningTriggered: false });
      } else if (confirmed && this.data.fallActive) {
        const elapsed = Math.floor((now - this._fallStartTime) / 1000);
        this.setData({ fallDuration: elapsed });
        if (elapsed >= FALL_ALERT_THRESHOLD && !this.data.warningTriggered) {
          this.triggerFallWarning(elapsed);
        }
      }
    } else {
      this._consecutiveFall = 0;
      if (this.data.fallActive) {
        if (this._lastWarningTime && (now - this._lastWarningTime) < FALL_ALERT_COOLDOWN * 1000) {
          // 冷却期内，维持告警
        } else {
          this.resetFallState();
        }
      }
    }
  },

  triggerFallWarning(duration) {
    this.setData({ warningTriggered: true });
    this._lastWarningTime = Date.now();

    // 1. 连续振动告警
    const vibratePattern = () => {
      wx.vibrateLong({ success: () => {
        setTimeout(() => wx.vibrateLong({ fail: () => {} }), 500);
      }, fail: () => {} });
    };
    vibratePattern();
    // 播放告警音频
    const alertAudio = wx.createInnerAudioContext();
    alertAudio.src = '/assets/alert.wav';
    alertAudio.loop = true;
    alertAudio.play();
    this._alertAudio = alertAudio;

    // 每 3 秒重复振动，直到用户处理
    this._alertVibrateTimer = setInterval(vibratePattern, 3000);

    // 2. 弹窗警告
    wx.showModal({
      title: '⚠️ 摔倒警报',
      content: `检测到人员摔倒已持续 ${duration} 秒！\n请立即查看并采取救助措施。`,
      confirmText: '立即查看',
      cancelText: '误报',
      success: (res) => {
        if (res.confirm) {
          // 用户确认，继续保持振动提醒
        } else {
          // 用户标记为误报，清除告警
          this.resetFallState();
        }
      }
    });

    // 3. 订阅消息推送（需在微信公众平台申请模板后填入ID）
    // 申请路径: mp.weixin.qq.com → 功能 → 订阅消息 → 选用模板
    const SUBSCRIBE_TEMPLATE_IDS = [];  // 填入模板ID，如: ['xxxxxxxx']
    if (SUBSCRIBE_TEMPLATE_IDS.length > 0) {
      wx.requestSubscribeMessage({
        tmplIds: SUBSCRIBE_TEMPLATE_IDS,
        success: (res) => {
          console.log('订阅消息授权:', res);
        },
        fail: (err) => {
          console.log('订阅消息失败:', err);
        }
      });
    }
  },

  stopVibrateTimer() {
    if (this._alertVibrateTimer) {
      clearInterval(this._alertVibrateTimer);
      this._alertVibrateTimer = null;
    }
  },

  resetFallState() {
    this._fallStartTime = null;
    this.stopVibrateTimer();
    this.stopDemo();
    if (this._alertAudio) {
      this._alertAudio.stop();
      this._alertAudio.destroy();
      this._alertAudio = null;
    }
    this.setData({
      fallActive: false,
      fallDuration: 0,
      warningTriggered: false,
      demoRunning: false
    });
  },

  stopDemo() {
    if (this._demoTimer) {
      clearInterval(this._demoTimer);
      this._demoTimer = null;
    }
    if (this._demoTimeout) {
      clearTimeout(this._demoTimeout);
      this._demoTimeout = null;
    }
  },

  // ==================== 告警演示 ====================

  demoAlert() {
    if (this.data.demoRunning) return;
    this.setData({ demoRunning: true });

    this.setData({ fallActive: true, fallDuration: 0, warningTriggered: false });
    this._fallStartTime = Date.now();

    let sec = 0;
    this._demoTimer = setInterval(() => {
      sec++;
      if (this.data.warningTriggered) return;  // 用户点了误报，停止计数
      this.setData({ fallDuration: sec });

      if (sec >= 10 && !this.data.warningTriggered) {
        this.triggerFallWarning(sec);
      }

      if (sec >= 15) {
        this.stopDemo();
        this.resetFallState();
        wx.showToast({ title: '演示结束', icon: 'none' });
      }
    }, 1000);

    wx.showToast({ title: '告警演示开始（15秒）', icon: 'none', duration: 1500 });
  },

  demoQuickAlert() {
    if (this.data.demoRunning) return;

    wx.showModal({
      title: '快速演示',
      content: '将直接触发完整告警状态，是否继续？',
      success: (res) => {
        if (!res.confirm) return;

        this.setData({ demoRunning: true, fallActive: true, fallDuration: 10 });
        this._fallStartTime = Date.now() - 10000;
        this.triggerFallWarning(10);

        this._demoTimeout = setTimeout(() => {
          this.resetFallState();
          wx.showToast({ title: '演示结束', icon: 'none' });
        }, 15000);
      }
    });
  },

  // ==================== 参数 ====================

  onIntervalChange(e) {
    this.setData({ interval: e.detail.value });
    if (this.data.detecting) {
      this.stopAutoDetect();
      this.startAutoDetect();
    }
  },

  onTrackerChange(e) {
    this.setData({ trackerIndex: parseInt(e.detail.value) });
  },

  onShareAppMessage() {
    return {
      title: '摔倒检测工具 - 实时检测',
      path: '/pages/camera/camera'
    };
  }
});
