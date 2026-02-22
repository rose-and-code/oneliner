import { login, isLoggedIn, updateProfile } from '../../services/auth'

Page({
  data: {
    avatarUrl: '',
    nickname: '',
    canSubmit: false,
  },

  onChooseAvatar(e: WechatMiniprogram.CustomEvent) {
    const url = e.detail.avatarUrl
    if (url) {
      this.setData({ avatarUrl: url })
      this.checkCanSubmit()
    }
  },

  onNicknameInput(e: WechatMiniprogram.Input) {
    this.setData({ nickname: e.detail.value })
    this.checkCanSubmit()
  },

  onNicknameBlur(e: WechatMiniprogram.Input) {
    this.setData({ nickname: e.detail.value })
    this.checkCanSubmit()
  },

  checkCanSubmit() {
    const can = this.data.nickname.trim().length > 0 && this.data.avatarUrl.length > 0
    if (can !== this.data.canSubmit) {
      this.setData({ canSubmit: can })
    }
  },

  async onTapConfirm() {
    if (!this.data.canSubmit) return
    wx.showLoading({ title: '登录中...' })
    try {
      if (!isLoggedIn()) {
        await login()
      }
      await updateProfile(this.data.nickname.trim(), this.data.avatarUrl)
      wx.hideLoading()
      wx.showToast({ title: '登录成功', icon: 'success', duration: 1000 })
      setTimeout(() => wx.navigateBack(), 800)
    } catch (_) {
      wx.hideLoading()
      wx.showToast({ title: '登录失败，请重试', icon: 'none' })
    }
  },

  onTapSkip() {
    wx.navigateBack()
  },
})
