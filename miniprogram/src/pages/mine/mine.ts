import type { BookmarkItem } from '../../types/index'
import { fetchBookmarks, toggleBookmark } from '../../services/bookmarks'
import { isLoggedIn } from '../../services/auth'

Page({
  data: {
    bookmarks: [] as BookmarkItem[],
    loading: false,
    empty: false,
    needLogin: false,
  },

  onShow() {
    if (!isLoggedIn()) {
      this.setData({ needLogin: true, loading: false })
      return
    }
    this.loadBookmarks()
  },

  async loadBookmarks() {
    this.setData({ loading: true, needLogin: false })
    const bookmarks = await fetchBookmarks()
    this.setData({ bookmarks, loading: false, empty: bookmarks.length === 0 })
  },

  onTapCard(e: WechatMiniprogram.TouchEvent) {
    const sid = (e.currentTarget as unknown as { dataset: { sentenceId: string } }).dataset.sentenceId
    if (!sid) return
    wx.navigateBack()
    setTimeout(() => {
      const pages = getCurrentPages()
      const indexPage = pages[pages.length - 1]
      if (indexPage && (indexPage as unknown as { jumpToSentenceId: (id: string) => void }).jumpToSentenceId) {
        (indexPage as unknown as { jumpToSentenceId: (id: string) => void }).jumpToSentenceId(sid)
      }
    }, 300)
  },

  async onTapRemove(e: WechatMiniprogram.TouchEvent) {
    const idx = (e.currentTarget as unknown as { dataset: { index: number } }).dataset.index
    const item = this.data.bookmarks[idx]
    if (!item) return
    await toggleBookmark(item.sentence_id)
    const bookmarks = this.data.bookmarks.filter((_: BookmarkItem, i: number) => i !== idx)
    this.setData({ bookmarks, empty: bookmarks.length === 0 })
    wx.showToast({ title: '已取消收藏', icon: 'none', duration: 1000 })
  },

  onTapLogin() {
    wx.navigateTo({ url: '/pages/login/login' })
  },

  goToIndex() {
    wx.navigateBack()
  },
})
