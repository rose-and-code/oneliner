import type { BookWithSentences, Sentence } from '../../types/index'
import { fetchAllBooks } from '../../services/sentences'
import { toggleBookmark } from '../../services/bookmarks'
import { isLoggedIn } from '../../services/auth'

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
}

function buildArray(count: number): number[] {
  const arr: number[] = []
  for (let i = 0; i < count; i++) arr.push(i)
  return arr
}

const UNDERLINE_ROWS = buildArray(10)

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
    underlineRows: UNDERLINE_ROWS,
    hasHistory: false,
    showSheet: false,
    sheetAuthor: '',
    sheetBooks: [],
    flipSq: {} as Record<string, unknown>,
    flipOq: {} as Record<string, unknown>,
  } as IndexData,

  jumpHistory: [] as JumpHistoryEntry[],

  onLoad() {
    this.loadData()
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
    this.setData({ books, loading: false })
    this.syncHeader()
    this.setupHintAnimations()
  },

  hintVal: null as ReturnType<typeof shared<number>> | null,

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

  syncHeader() {
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
    })
  },

  onBookChange(e: WechatMiniprogram.SwiperChange) {
    if (e.detail.source !== 'touch') return
    if (this.data.hintHorizontal) this.setData({ hintHorizontal: false })
    const newIndex = e.detail.current
    if (newIndex === this.data.bookIndex) return
    this.setData({
      bookIndex: newIndex,
      sentenceIndex: 0,
      contextOpen: false,
      isFlipped: false,
    })
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
    this.setData({
      sentenceIndex: newIndex,
      contextOpen: false,
      isFlipped: false,
    })
    this.syncHeader()
  },

  onTapSentence() {
    if (this.data.isFlipped) return
    this.setData({ contextOpen: !this.data.contextOpen })
  },

  onTapFlip() {
    const { books, bookIndex, sentenceIndex } = this.data
    const s = books[bookIndex].sentences[sentenceIndex]
    const rawSq = s.similar_quotes && s.similar_quotes.length > 0 ? s.similar_quotes[0] : null
    const rawOq = s.opposite_quotes && s.opposite_quotes.length > 0 ? s.opposite_quotes[0] : null
    const titleSet: Record<string, boolean> = {}
    const authorCount: Record<string, number> = {}
    for (let i = 0; i < books.length; i++) {
      titleSet[books[i].book.title] = true
      authorCount[books[i].book.author] = (authorCount[books[i].book.author] || 0) + 1
    }
    const enrich = (q: Record<string, unknown> | null): Record<string, unknown> => {
      if (!q) return {}
      return {
        text: q.text,
        book_title: q.book_title,
        book_author: q.book_author,
        sentence_id: q.sentence_id || null,
        book_found: titleSet[q.book_title as string] || false,
        author_multi_book: (authorCount[q.book_author as string] || 0) > 1,
      }
    }
    this.setData({
      isFlipped: true,
      flipSq: enrich(rawSq as Record<string, unknown> | null),
      flipOq: enrich(rawOq as Record<string, unknown> | null),
    })
  },

  onTapBack() {
    if (this.data.isFlipped) {
      this.setData({ isFlipped: false, contextOpen: false })
    }
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

  async onTapBookmark(e: WechatMiniprogram.TouchEvent) {
    const dataset = (e.currentTarget as unknown as { dataset: { sentenceId: string; bookIdx: number; sentenceIdx: number } }).dataset
    if (!dataset.sentenceId) return
    if (!this.ensureLogin()) return
    const res = await toggleBookmark(dataset.sentenceId)
    const key = `books[${dataset.bookIdx}].sentences[${dataset.sentenceIdx}].is_bookmarked`
    this.setData({ [key]: res.is_bookmarked, 'currentSentence.is_bookmarked': res.is_bookmarked })
    wx.showToast({ title: res.is_bookmarked ? '已收藏' : '已取消', icon: 'none', duration: 1000 })
  },

  goToMine() {
    wx.navigateTo({ url: '/pages/mine/mine' })
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
    this.syncHeader()
  },
})
