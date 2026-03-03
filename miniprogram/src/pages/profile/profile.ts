import { isLoggedIn } from '../../services/auth'

Page({
  data: {
    loggedIn: false,
    nickname: '',
    avatarUrl: '',
    version: 'v2.0.0',
  },

  onShow() {
    const loggedIn = isLoggedIn()
    if (loggedIn) {
      const nickname = wx.getStorageSync('nickname') as string || ''
      const avatarUrl = wx.getStorageSync('avatar_url') as string || ''
      this.setData({ loggedIn: true, nickname, avatarUrl })
    } else {
      this.setData({ loggedIn: false, nickname: '', avatarUrl: '' })
    }
  },

  onTapLogin() {
    wx.navigateTo({ url: '/pages/login/login' })
  },

  onTapLogout() {
    wx.removeStorageSync('token')
    wx.removeStorageSync('user_id')
    wx.removeStorageSync('nickname')
    wx.removeStorageSync('avatar_url')
    this.setData({ loggedIn: false, nickname: '', avatarUrl: '' })
    wx.showToast({ title: '已退出', icon: 'none', duration: 1000 })
  },

  goToIndex() {
    wx.navigateBack({ delta: 10 })
  },

  goToMine() {
    wx.redirectTo({ url: '/pages/mine/mine' })
  },
})
