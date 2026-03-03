import type { BookmarkItem, AgentReplyItem } from '../../types/index'
import { fetchBookmarks, toggleBookmark } from '../../services/bookmarks'
import { isLoggedIn } from '../../services/auth'
import { fetchReplies, submitReaction } from '../../services/garden'
import { getGardenStage, getStageText, getTopThemes, buildThemeCountsFromBookmarks, STAGE_CONFIG } from '../../utils/garden'

interface BookmarkGroup {
  bookTitle: string
  bookAuthor: string
  items: BookmarkItem[]
}

function groupBookmarks(bookmarks: BookmarkItem[]): BookmarkGroup[] {
  const map: Record<string, BookmarkGroup> = {}
  const order: string[] = []
  for (let i = 0; i < bookmarks.length; i++) {
    const b = bookmarks[i]
    if (!map[b.book_title]) {
      map[b.book_title] = { bookTitle: b.book_title, bookAuthor: b.book_author, items: [] }
      order.push(b.book_title)
    }
    map[b.book_title].items.push(b)
  }
  const groups: BookmarkGroup[] = []
  for (let i = 0; i < order.length; i++) groups.push(map[order[i]])
  return groups
}

function relativeTime(isoStr: string): string {
  const now = Date.now()
  const then = new Date(isoStr).getTime()
  const diff = Math.floor((now - then) / 1000)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  return `${Math.floor(diff / 86400)}天前`
}

Page({
  data: {
    bookmarks: [] as BookmarkItem[],
    groups: [] as BookmarkGroup[],
    totalCount: 0,
    loading: false,
    empty: false,
    needLogin: false,
    stageIcon: '',
    stageText: '',
    topThemes: [] as string[],
    showThemes: false,
    scrollHeight: 0,
    replies: [] as (AgentReplyItem & { timeAgo: string })[],
    hasReplies: false,
  },

  onLoad() {
    const info = wx.getWindowInfo()
    this._windowHeight = info.windowHeight
    this._headerHeight = 96
    this._bottomNavHeight = 66
    this._stageHeight = 76
    this.setData({ scrollHeight: info.windowHeight - this._headerHeight - this._bottomNavHeight })
  },

  _windowHeight: 0,
  _headerHeight: 96,
  _bottomNavHeight: 66,
  _stageHeight: 76,

  _updateScrollHeight(hasStage: boolean) {
    const extra = hasStage ? this._stageHeight : 0
    this.setData({ scrollHeight: this._windowHeight - this._headerHeight - this._bottomNavHeight - extra })
  },

  onShow() {
    if (!isLoggedIn()) {
      this.setData({ needLogin: true, loading: false })
      this._updateScrollHeight(false)
      return
    }
    this.loadBookmarks()
    this.loadReplies()
  },

  async loadBookmarks() {
    this.setData({ loading: true, needLogin: false })
    const bookmarks = await fetchBookmarks()
    const stage = getGardenStage(bookmarks.length)
    const themeCounts = buildThemeCountsFromBookmarks(bookmarks)
    const topThemes = getTopThemes(themeCounts, 2)
    const hasContent = bookmarks.length > 0
    this.setData({
      bookmarks,
      groups: groupBookmarks(bookmarks),
      totalCount: bookmarks.length,
      loading: false,
      empty: !hasContent,
      stageIcon: STAGE_CONFIG[stage].icon,
      stageText: getStageText(stage, bookmarks.length),
      topThemes,
      showThemes: bookmarks.length >= 3 && topThemes.length > 0,
    })
    this._updateScrollHeight(hasContent)
  },

  async loadReplies() {
    if (!isLoggedIn()) return
    const resp = await fetchReplies(20)
    const items = resp.items || []
    const replies = items.map((r: AgentReplyItem) => ({
      ...r,
      timeAgo: relativeTime(r.created_at),
    }))
    this.setData({ replies, hasReplies: replies.length > 0 })
  },

  async onTapReaction(e: WechatMiniprogram.TouchEvent) {
    const dataset = (e.currentTarget as unknown as { dataset: { replyId: string; reaction: string } }).dataset
    if (!dataset.replyId || !dataset.reaction) return
    await submitReaction(dataset.replyId, dataset.reaction)
    const replies = this.data.replies.map(r => {
      if (r.id === dataset.replyId) return { ...r, reaction: dataset.reaction }
      return r
    })
    this.setData({ replies })
    wx.vibrateShort({ type: 'light' })
  },

  onTapReplyTarget(e: WechatMiniprogram.TouchEvent) {
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
    const sid = (e.currentTarget as unknown as { dataset: { sentenceId: string } }).dataset.sentenceId
    if (!sid) return
    const bookmarks = this.data.bookmarks.filter((b: BookmarkItem) => b.sentence_id !== sid)
    this.setData({
      bookmarks,
      groups: groupBookmarks(bookmarks),
      totalCount: bookmarks.length,
      empty: bookmarks.length === 0,
    })
    await toggleBookmark(sid)
    wx.vibrateShort({ type: 'light' })
  },

  onTapLogin() {
    wx.navigateTo({ url: '/pages/login/login' })
  },

  goToIndex() {
    wx.navigateBack()
  },

  goToProfile() {
    wx.navigateTo({ url: '/pages/profile/profile' })
  },
})
