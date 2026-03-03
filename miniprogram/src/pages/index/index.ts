import type { BookWithSentences, Sentence } from '../../types/index'
import { fetchAllBooks } from '../../services/sentences'
import { toggleBookmark } from '../../services/bookmarks'
import { isLoggedIn } from '../../services/auth'
import { trackDwell, trackContextOpen, trackFlip, flushEvents } from '../../services/events'
import { fetchSprout, markSproutShown, setNotificationCallback, startHeartbeat, stopHeartbeat, markReplyRead } from '../../services/garden'
import type { NotificationPayload } from '../../types/index'
import { FLIP_DURATION_MS } from '../../utils/constants'
import { loadGardenState, updateThemeCounts, shouldTriggerSeedEcho, markSeedEchoTriggered, generateSeedEcho, resetSessionEchoCount } from '../../utils/garden'
import type { GardenState } from '../../utils/garden'

const worklet = wx.worklet || {}
const { shared, timing, repeat, sequence, Easing } = worklet
const isSkyline = typeof shared === 'function'


interface JumpHistoryEntry {
  bookIndex: number
  sentenceIndex: number
  isFlipped: boolean
}

interface SheetBook {
  title: string
  bookIndex: number
  sentenceCount: number
}

interface IndexData {
  books: BookWithSentences[]
  bookIndex: number
  sentenceIndex: number
  currentSentence: Sentence | null
  currentBookTitle: string
  currentAuthor: string
  currentAuthorMultiBook: boolean
  totalSentences: number
  progressDots: number[]
  contextOpen: boolean
  isFlipped: boolean
  loading: boolean
  tabIndex: number
  hintVisible: boolean
  hasHistory: boolean
  showSheet: boolean
  sheetAuthor: string
  sheetBooks: SheetBook[]
  currentFontSize: number
  showBookOverlay: boolean
  overlayBookTitle: string
  overlayBookAuthor: string
  overlayBookCount: number
}

function buildArray(count: number): number[] {
  const arr: number[] = []
  for (let i = 0; i < count; i++) arr.push(i)
  return arr
}

function calcFontSize(textLen: number): number {
  if (textLen <= 20) return 24
  if (textLen <= 40) return 20
  if (textLen <= 60) return 17
  return 15
}

const CARD_ILLUSTRATIONS = [
  '/assets/illustrations/mascot.png',
  '/assets/illustrations/doodle-groovy.svg',
  '/assets/illustrations/doodle-reading.svg',
  '/assets/illustrations/mushroom.svg',
  '/assets/illustrations/teacup.svg',
  '/assets/illustrations/bloom.svg',
]

const OVERLAY_ILLUSTRATIONS = [
  '/assets/illustrations/doodle-levitate.svg',
  '/assets/illustrations/hole.svg',
  '/assets/illustrations/keyhole.svg',
]

const FLIP_ILLUSTRATIONS = [
  '/assets/illustrations/key.svg',
  '/assets/illustrations/roots.svg',
  '/assets/illustrations/sparkle.svg',
  '/assets/illustrations/card.svg',
]

Page({
  data: {
    books: [],
    bookIndex: 0,
    sentenceIndex: 0,
    currentSentence: null,
    currentBookTitle: '',
    currentAuthor: '',
    currentAuthorMultiBook: false,
    totalSentences: 0,
    progressDots: [],
    contextOpen: false,
    isFlipped: false,
    loading: true,
    tabIndex: 0,
    hintVertical: true,
    hintHorizontal: false,
    currentFontSize: 17,
    cardIllustration: CARD_ILLUSTRATIONS[0],
    flipIllustration: FLIP_ILLUSTRATIONS[0],
    hasHistory: false,
    showSheet: false,
    sheetAuthor: '',
    sheetBooks: [],
    flipSq: {} as Record<string, unknown>,
    flipOq: {} as Record<string, unknown>,
    sproutText: '',
    sproutId: '',
    sproutTargetId: '',
    showSprout: false,
    showBookOverlay: false,
    overlayBookTitle: '',
    overlayBookAuthor: '',
    overlayBookCount: 0,
    overlayIllustration: OVERLAY_ILLUSTRATIONS[0],
    seedEchoText: '',
    seedEchoVisible: false,
    toastVisible: false,
    toastHook: '',
    toastReplyId: '',
  } as IndexData,

  jumpHistory: [] as JumpHistoryEntry[],
  dwellStart: 0,
  gardenState: null as GardenState | null,
  seedEchoTimer: 0,
  seedDotVal: null as ReturnType<typeof shared<number>> | null,
  seedEchoVal: null as ReturnType<typeof shared<number>> | null,
  _seedSharedStart: null as { x: ReturnType<typeof shared<number>>; y: ReturnType<typeof shared<number>>; dx: ReturnType<typeof shared<number>>; dy: ReturnType<typeof shared<number>> } | null,
  seedDotBound: false,
  seedEchoBound: false,
  toastTimer: 0,

  onLoad() {
    wx.showShareMenu({ withShareTicket: true, menus: ['shareAppMessage', 'shareTimeline'] })
    this.gardenState = loadGardenState()
    this.gardenState = resetSessionEchoCount(this.gardenState)
    setNotificationCallback((payload: NotificationPayload) => {
      this.showToastNotification(payload)
    })
    this.loadData()
  },

  onShareAppMessage(): WechatMiniprogram.Page.ICustomShareContent {
    const s = this.data.currentSentence
    const title = s ? s.text.slice(0, 30) + (s.text.length > 30 ? '...' : '') : 'OneLiner'
    return { title, path: '/pages/index/index' }
  },

  onShareTimeline(): WechatMiniprogram.Page.ICustomTimelineContent {
    const s = this.data.currentSentence
    const title = s ? s.text.slice(0, 30) + (s.text.length > 30 ? '...' : '') : 'OneLiner'
    return { title }
  },

  onShow() {
    if (isLoggedIn() && this.data.books.length > 0) {
      this.loadData()
    }
    const app = getApp()
    const sid = app.globalData.jumpToSentenceId
    if (sid) {
      app.globalData.jumpToSentenceId = ''
      const pos = this.findSentencePosition(sid)
      if (pos) this.jumpTo(pos.bookIndex, pos.sentenceIndex)
    }
    this.checkSprout()
    if (isLoggedIn()) startHeartbeat()
  },

  async checkSprout() {
    if (!isLoggedIn()) return
    const sprout = await fetchSprout()
    if (!sprout) return
    this.setData({
      sproutText: sprout.text,
      sproutId: sprout.id,
      sproutTargetId: sprout.target_sentence_id || '',
      showSprout: true,
    })
    markSproutShown(sprout.id)
    setTimeout(() => {
      this.setData({ showSprout: false })
    }, 6000)
  },

  onTapSprout() {
    if (!this.data.sproutTargetId) return
    const pos = this.findSentencePosition(this.data.sproutTargetId)
    if (pos) {
      this.setData({ showSprout: false })
      this.jumpTo(pos.bookIndex, pos.sentenceIndex)
    }
  },

  onHide() {
    this.reportDwell()
    flushEvents()
    stopHeartbeat()
  },

  async loadData() {
    const books = await fetchAllBooks()
    if (!books || books.length === 0) return
    const titleSet: Record<string, boolean> = {}
    const authorCount: Record<string, number> = {}
    for (let i = 0; i < books.length; i++) {
      titleSet[books[i].book.title] = true
      authorCount[books[i].book.author] = (authorCount[books[i].book.author] || 0) + 1
    }
    for (let i = 0; i < books.length; i++) {
      for (let j = 0; j < books[i].sentences.length; j++) {
        const s = books[i].sentences[j] as Record<string, unknown>
        const sq = (s.similar_quotes as Record<string, unknown>[]) || []
        const oq = (s.opposite_quotes as Record<string, unknown>[]) || []
        const allQuotes = sq.concat(oq)
        for (let k = 0; k < allQuotes.length; k++) {
          allQuotes[k].book_found = titleSet[allQuotes[k].book_title as string] || false
          allQuotes[k].author_multi_book = (authorCount[allQuotes[k].book_author as string] || 0) > 1
        }
        s.sq = sq[0] || {}
        s.oq = oq[0] || {}
      }
    }
    const isFirst = this.data.books.length === 0
    this.setData({ books, loading: false })
    if (isFirst) {
      const bi = Math.floor(Math.random() * books.length)
      const si = Math.floor(Math.random() * books[bi].sentences.length)
      this.setData({ bookIndex: bi, sentenceIndex: si })
    }
    this.syncHeader()
    this.setupHintAnimations()
    setTimeout(() => this.setupFlipAnimation(), 100)
    setTimeout(() => this.setupSeedDotAnimation(), 200)
  },

  hintVal: null as ReturnType<typeof shared<number>> | null,
  flipVal: null as ReturnType<typeof shared<number>> | null,
  flipAnimating: false,
  flipAnimBound: false,

  resetFlip() {
    this.flipAnimating = false
    this.flipAnimBound = false
    if (this.flipVal) this.flipVal.value = 0
    setTimeout(() => this.setupFlipAnimation(), 100)
  },

  setupFlipAnimation() {
    if (!isSkyline || this.flipAnimBound) return
    this.flipAnimBound = true
    const fv = shared(0)
    this.flipVal = fv

    this.applyAnimatedStyle('#card-front', () => {
      'worklet'
      const v = fv.value
      const s = v <= 0.5 ? 1 - v * 2 : 0
      return { transform: `scaleX(${s})`, opacity: s < 0.01 ? 0 : 1 }
    })
    this.applyAnimatedStyle('#card-back', () => {
      'worklet'
      const v = fv.value
      const s = v >= 0.5 ? (v - 0.5) * 2 : 0
      return { transform: `scaleX(${s})`, opacity: s < 0.01 ? 0 : 1 }
    })
  },

  setupHintAnimations() {
    if (!isSkyline) return
    const hv = shared(0)
    this.hintVal = hv
    const ease = Easing.inOut(Easing.ease)

    this.applyAnimatedStyle('#hint-down', () => {
      'worklet'
      return { transform: `translateX(-50%) translateY(${hv.value}px)` }
    })

    hv.value = repeat(sequence(
      timing(4, { duration: 800, easing: ease }),
      timing(0, { duration: 800, easing: ease }),
    ), -1)
  },

  setupHorizontalHints() {
    if (!isSkyline) return
    const hv = this.hintVal
    if (!hv) return

    this.applyAnimatedStyle('#hint-left', () => {
      'worklet'
      return { transform: `translateY(-50%) translateX(${-hv.value}px)` }
    })
    this.applyAnimatedStyle('#hint-right', () => {
      'worklet'
      return { transform: `translateY(-50%) translateX(${hv.value}px)` }
    })
  },

  reportDwell() {
    if (!this.dwellStart) return
    const elapsed = Date.now() - this.dwellStart
    const { books, bookIndex, sentenceIndex } = this.data
    const book = books[bookIndex]
    if (book) {
      const s = book.sentences[sentenceIndex]
      if (s) trackDwell(s.id, book.book.id, elapsed)
    }
    this.dwellStart = 0
  },

  syncHeader() {
    this.reportDwell()
    this.dwellStart = Date.now()
    const { books, bookIndex, sentenceIndex } = this.data
    const book = books[bookIndex]
    if (!book) return
    const sentence = book.sentences[sentenceIndex]
    const author = book.book.author
    let authorCount = 0
    for (let i = 0; i < books.length; i++) {
      if (books[i].book.author === author) authorCount++
    }
    this.setData({
      currentSentence: sentence,
      currentBookTitle: '《' + book.book.title + '》',
      currentAuthor: author,
      currentAuthorMultiBook: authorCount > 1,
      totalSentences: book.sentences.length,
      progressDots: buildArray(book.sentences.length),
      currentFontSize: calcFontSize(sentence.text.length),
      cardIllustration: CARD_ILLUSTRATIONS[(bookIndex * 7 + sentenceIndex) % CARD_ILLUSTRATIONS.length],
      flipIllustration: FLIP_ILLUSTRATIONS[(bookIndex + sentenceIndex) % FLIP_ILLUSTRATIONS.length],
    })
  },

  bookOverlayTimer: 0,

  onBookChange(e: WechatMiniprogram.SwiperChange) {
    if (e.detail.source !== 'touch') return
    if (this.data.hintHorizontal) this.setData({ hintHorizontal: false })
    const newIndex = e.detail.current
    if (newIndex === this.data.bookIndex) return
    const book = this.data.books[newIndex]
    if (book) {
      if (this.bookOverlayTimer) clearTimeout(this.bookOverlayTimer)
      this.setData({
        showBookOverlay: true,
        overlayBookTitle: '《' + book.book.title + '》',
        overlayBookAuthor: book.book.author,
        overlayBookCount: book.sentences.length,
        overlayIllustration: OVERLAY_ILLUSTRATIONS[newIndex % OVERLAY_ILLUSTRATIONS.length],
      })
      this.bookOverlayTimer = setTimeout(() => {
        this.setData({ showBookOverlay: false })
      }, 800) as unknown as number
    }
    this.setData({
      bookIndex: newIndex,
      sentenceIndex: 0,
      contextOpen: false,
      isFlipped: false,
    })
    this.resetFlip()
    this.syncHeader()
  },

  onSentenceChange(e: WechatMiniprogram.SwiperChange) {
    if (e.detail.source !== 'touch') return
    if (this.data.hintVertical) {
      this.setData({ hintVertical: false, hintHorizontal: true })
      setTimeout(() => this.setupHorizontalHints(), 50)
    }
    const bIdx = Number((e.currentTarget as unknown as { dataset: { bookIndex: number } }).dataset.bookIndex)
    if (bIdx !== this.data.bookIndex) return
    const newIndex = e.detail.current
    if (newIndex === this.data.sentenceIndex) return
    if (this.data.showSprout) this.setData({ showSprout: false })
    this.setData({
      sentenceIndex: newIndex,
      contextOpen: false,
      isFlipped: false,
    })
    this.resetFlip()
    this.syncHeader()
  },

  onTapSentence() {
    if (this.data.isFlipped) return
    const opening = !this.data.contextOpen
    this.setData({ contextOpen: opening })
    if (opening) {
      const { books, bookIndex, sentenceIndex } = this.data
      const book = books[bookIndex]
      if (book) trackContextOpen(book.sentences[sentenceIndex].id, book.book.id)
    }
  },

  enrichQuote(q: Record<string, unknown> | null): Record<string, unknown> {
    if (!q) return {}
    const { books } = this.data
    const titleSet: Record<string, boolean> = {}
    const authorCount: Record<string, number> = {}
    for (let i = 0; i < books.length; i++) {
      titleSet[books[i].book.title] = true
      authorCount[books[i].book.author] = (authorCount[books[i].book.author] || 0) + 1
    }
    return {
      text: q.text,
      book_title: q.book_title,
      book_author: q.book_author,
      sentence_id: q.sentence_id || null,
      book_found: titleSet[q.book_title as string] || false,
      author_multi_book: (authorCount[q.book_author as string] || 0) > 1,
    }
  },

  onTapFlip() {
    if (this.flipAnimating) return
    const { books, bookIndex, sentenceIndex } = this.data
    const s = books[bookIndex].sentences[sentenceIndex]
    trackFlip(s.id, books[bookIndex].book.id)
    const rawSq = s.similar_quotes && s.similar_quotes.length > 0 ? s.similar_quotes[0] : null
    const rawOq = s.opposite_quotes && s.opposite_quotes.length > 0 ? s.opposite_quotes[0] : null

    this.setData({
      isFlipped: true,
      flipSq: this.enrichQuote(rawSq as Record<string, unknown> | null),
      flipOq: this.enrichQuote(rawOq as Record<string, unknown> | null),
    })

    if (!isSkyline) return

    this.flipAnimating = true
    const fv = this.flipVal
    if (fv) {
      fv.value = timing(1, { duration: FLIP_DURATION_MS, easing: Easing.inOut(Easing.ease) })
    }
    setTimeout(() => { this.flipAnimating = false }, FLIP_DURATION_MS)
  },

  onTapBack() {
    if (!this.data.isFlipped || this.flipAnimating) return

    if (!isSkyline) {
      this.setData({ isFlipped: false, contextOpen: false })
      return
    }

    this.flipAnimating = true
    const fv = this.flipVal
    if (fv) {
      fv.value = timing(0, { duration: FLIP_DURATION_MS, easing: Easing.inOut(Easing.ease) })
    }
    setTimeout(() => {
      this.setData({ isFlipped: false, contextOpen: false })
      this.flipAnimating = false
    }, FLIP_DURATION_MS)
  },

  findSentencePosition(sentenceId: string): { bookIndex: number; sentenceIndex: number } | null {
    const { books } = this.data
    for (let bi = 0; bi < books.length; bi++) {
      const ss = books[bi].sentences
      for (let si = 0; si < ss.length; si++) {
        if (ss[si].id === sentenceId) return { bookIndex: bi, sentenceIndex: si }
      }
    }
    return null
  },

  jumpTo(bookIdx: number, sentenceIdx: number) {
    this.jumpHistory.push({
      bookIndex: this.data.bookIndex,
      sentenceIndex: this.data.sentenceIndex,
      isFlipped: this.data.isFlipped,
    })
    this.setData({
      bookIndex: bookIdx,
      sentenceIndex: sentenceIdx,
      isFlipped: false,
      contextOpen: false,
      hasHistory: true,
    })
    this.resetFlip()
    this.syncHeader()
  },

  onTapRelatedQuote(e: WechatMiniprogram.TouchEvent) {
    const sid = (e.currentTarget as unknown as { dataset: { sentenceId: string } }).dataset.sentenceId
    if (!sid) return
    const pos = this.findSentencePosition(sid)
    if (!pos) return
    this.jumpTo(pos.bookIndex, pos.sentenceIndex)
  },

  onGoBack() {
    if (this.jumpHistory.length === 0) return
    const prev = this.jumpHistory.pop()!
    this.setData({
      bookIndex: prev.bookIndex,
      sentenceIndex: prev.sentenceIndex,
      isFlipped: prev.isFlipped,
      contextOpen: false,
      hasHistory: this.jumpHistory.length > 0,
    })
    this.resetFlip()
    if (prev.isFlipped && this.flipVal) this.flipVal.value = 1
    this.syncHeader()
  },

  onTapAuthorName(e: WechatMiniprogram.TouchEvent) {
    const author = (e.currentTarget as unknown as { dataset: { author: string } }).dataset.author
    if (!author) return
    this.showAuthorSheet(author)
  },

  onTapRelatedBookTitle(e: WechatMiniprogram.TouchEvent) {
    const title = (e.currentTarget as unknown as { dataset: { bookTitle: string } }).dataset.bookTitle
    if (!title) return
    const { books } = this.data
    for (let i = 0; i < books.length; i++) {
      if (books[i].book.title === title) {
        const randomIdx = Math.floor(Math.random() * books[i].sentences.length)
        this.jumpTo(i, randomIdx)
        return
      }
    }
  },

  onTapRelatedAuthor(e: WechatMiniprogram.TouchEvent) {
    const author = (e.currentTarget as unknown as { dataset: { author: string } }).dataset.author
    if (!author) return
    this.showAuthorSheet(author)
  },

  showAuthorSheet(author: string) {
    const { books } = this.data
    const authorBooks: SheetBook[] = []
    for (let i = 0; i < books.length; i++) {
      if (books[i].book.author === author) {
        authorBooks.push({ title: books[i].book.title, bookIndex: i, sentenceCount: books[i].sentences.length })
      }
    }
    if (authorBooks.length <= 1) return
    this.setData({ showSheet: true, sheetAuthor: author, sheetBooks: authorBooks })
  },

  onSheetBookTap(e: WechatMiniprogram.TouchEvent) {
    const idx = (e.currentTarget as unknown as { dataset: { bookIndex: number } }).dataset.bookIndex
    this.setData({ showSheet: false })
    this.jumpTo(idx, 0)
  },

  onCloseSheet() {
    this.setData({ showSheet: false })
  },

  ensureLogin(): boolean {
    if (isLoggedIn()) return true
    wx.navigateTo({ url: '/pages/login/login' })
    return false
  },

  seedStartX: 0,
  seedStartY: 0,
  seedEndX: 0,
  seedEndY: 0,

  setupSeedDotAnimation() {
    if (!isSkyline || this.seedDotBound) return
    this.seedDotBound = true
    const sv = shared(0)
    this.seedDotVal = sv
    const startX = shared(0)
    const startY = shared(0)
    const deltaX = shared(0)
    const deltaY = shared(0)
    this._seedSharedStart = { x: startX, y: startY, dx: deltaX, dy: deltaY }
    this.applyAnimatedStyle('#seed-dot', () => {
      'worklet'
      const p = sv.value
      const x = startX.value + deltaX.value * p
      const yProgress = p * p
      const y = startY.value + deltaY.value * yProgress
      const fade = p < 0.85 ? 1 : 1 - (p - 0.85) / 0.15
      return { transform: `translate(${x}px, ${y}px)`, opacity: fade }
    })
  },

  measureSeedPath() {
    const query = this.createSelectorQuery()
    query.select('#tab-garden').boundingClientRect()
    query.exec((res: Array<WechatMiniprogram.BoundingClientRectCallbackResult>) => {
      if (res && res[0]) {
        this.seedEndX = res[0].left + res[0].width / 2
        this.seedEndY = res[0].top
      }
    })
  },

  setupSeedEchoAnimation() {
    if (!isSkyline || this.seedEchoBound) return
    this.seedEchoBound = true
    const ev = shared(0)
    this.seedEchoVal = ev
    this.applyAnimatedStyle('#seed-echo', () => {
      'worklet'
      return { transform: `translateY(${(1 - ev.value) * 8}px)`, opacity: ev.value }
    })
  },

  triggerSeedDot() {
    if (!isSkyline) return
    if (!this.seedDotBound) this.setupSeedDotAnimation()
    const sv = this.seedDotVal
    if (!sv) return
    const query = this.createSelectorQuery()
    query.select('.bookmark-btn').boundingClientRect()
    query.select('#tab-garden').boundingClientRect()
    query.exec((res: Array<WechatMiniprogram.BoundingClientRectCallbackResult>) => {
      if (!res || !res[0] || !res[1]) return
      const btn = res[0]
      const tab = res[1]
      const sx = btn.left + btn.width / 2 - 3
      const sy = btn.top + btn.height / 2 - 3
      const ex = tab.left + tab.width / 2 - 3
      const ey = tab.top - 3
      const s = this._seedSharedStart
      if (s) {
        s.x.value = sx
        s.y.value = sy
        s.dx.value = ex - sx
        s.dy.value = ey - sy
      }
      sv.value = 0
      sv.value = timing(1, { duration: 650, easing: Easing.in(Easing.quad) })
    })
  },

  showSeedEcho(text: string) {
    if (this.seedEchoTimer) clearTimeout(this.seedEchoTimer)
    this.setData({ seedEchoText: text, seedEchoVisible: true })
    if (!this.seedEchoBound) {
      setTimeout(() => this.setupSeedEchoAnimation(), 50)
    }
    setTimeout(() => {
      const ev = this.seedEchoVal
      if (ev && isSkyline) {
        ev.value = 0
        ev.value = timing(1, { duration: 400, easing: Easing.out(Easing.ease) })
      }
    }, 100)
    this.seedEchoTimer = setTimeout(() => {
      const ev = this.seedEchoVal
      if (ev && isSkyline) {
        ev.value = timing(0, { duration: 600, easing: Easing.in(Easing.ease) })
      }
      setTimeout(() => {
        this.setData({ seedEchoVisible: false, seedEchoText: '' })
        this.seedEchoBound = false
      }, 650)
    }, 2500) as unknown as number
  },

  async onTapBookmark(e: WechatMiniprogram.TouchEvent) {
    const dataset = (e.currentTarget as unknown as { dataset: { sentenceId: string; bookIdx: number; sentenceIdx: number } }).dataset
    if (!dataset.sentenceId) return
    if (!this.ensureLogin()) return
    const res = await toggleBookmark(dataset.sentenceId)
    const key = `books[${dataset.bookIdx}].sentences[${dataset.sentenceIdx}].is_bookmarked`
    this.setData({ [key]: res.is_bookmarked, 'currentSentence.is_bookmarked': res.is_bookmarked })
    if (res.is_bookmarked) {
      wx.vibrateShort({ type: 'light' })
      this.triggerSeedDot()
      if (!this.gardenState) this.gardenState = loadGardenState()
      const sentence = this.data.currentSentence
      const themes = sentence && sentence.themes ? sentence.themes : []
      this.gardenState = updateThemeCounts(this.gardenState, themes)
      if (shouldTriggerSeedEcho(this.gardenState)) {
        const bookmarks = this.collectCurrentBookmarks()
        const echoText = generateSeedEcho(this.gardenState, sentence as import('../../types/index').Sentence, bookmarks)
        if (echoText) {
          this.gardenState = markSeedEchoTriggered(this.gardenState)
          this.showSeedEcho(echoText)
        }
      }
    } else {
      wx.showToast({ title: '已取消', icon: 'none', duration: 800 })
    }
  },

  collectCurrentBookmarks(): import('../../types/index').BookmarkItem[] {
    const result: import('../../types/index').BookmarkItem[] = []
    const { books } = this.data
    for (let i = 0; i < books.length; i++) {
      for (let j = 0; j < books[i].sentences.length; j++) {
        const s = books[i].sentences[j]
        if (s.is_bookmarked) {
          result.push({
            id: s.id,
            sentence_id: s.id,
            text: s.text,
            context_before: s.context_before,
            context_after: s.context_after,
            book_title: books[i].book.title,
            book_author: books[i].book.author,
            chapter: s.chapter,
            similar_quotes: s.similar_quotes,
            opposite_quotes: s.opposite_quotes,
            themes: s.themes || [],
            created_at: '',
          })
        }
      }
    }
    return result
  },

  showToastNotification(payload: NotificationPayload) {
    if (!payload.has_unread_reply || !payload.reply_hook) return
    if (this.data.toastVisible) return
    if (this.toastTimer) clearTimeout(this.toastTimer)
    this.setData({
      toastVisible: true,
      toastHook: payload.reply_hook,
      toastReplyId: payload.reply_id || '',
    })
    this.toastTimer = setTimeout(() => {
      this.setData({ toastVisible: false })
    }, 4000) as unknown as number
  },

  onTapToast() {
    if (this.toastTimer) clearTimeout(this.toastTimer)
    const replyId = this.data.toastReplyId
    this.setData({ toastVisible: false })
    if (replyId) markReplyRead(replyId)
    wx.navigateTo({ url: '/pages/mine/mine' })
  },

  goToMine() {
    wx.navigateTo({ url: '/pages/mine/mine' })
  },

  goToProfile() {
    wx.navigateTo({ url: '/pages/profile/profile' })
  },

  jumpToSentenceId(sentenceId: string) {
    const pos = this.findSentencePosition(sentenceId)
    if (!pos) return
    this.setData({
      bookIndex: pos.bookIndex,
      sentenceIndex: pos.sentenceIndex,
      isFlipped: false,
      contextOpen: false,
    })
    this.resetFlip()
    this.syncHeader()
  },
})
