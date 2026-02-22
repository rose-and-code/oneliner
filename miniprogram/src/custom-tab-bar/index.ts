Component({
  data: {
    selected: 0,
    tabs: [
      { pagePath: '/pages/index/index', text: '阅读', icon: 'book' },
      { pagePath: '/pages/mine/mine', text: '我的', icon: 'star' },
    ],
  },
  methods: {
    switchTab(e: WechatMiniprogram.TouchEvent) {
      const idx = e.currentTarget.dataset.index as number
      const tab = this.data.tabs[idx]
      if (idx === this.data.selected) return
      wx.switchTab({ url: tab.pagePath })
    },
  },
})
