import type { Sentence, BookmarkItem } from '../types/index'

export interface GardenState {
  themeCounts: Record<string, number>
  lastSeedEchoAt: number
  sessionEchoCount: number
  totalSeeds: number
}

export type GardenStage = 'empty' | 'seed' | 'sprout' | 'plant' | 'tree'

interface StageConfig {
  icon: string
  text: string
}

export const STAGE_CONFIG: Record<GardenStage, StageConfig> = {
  empty: { icon: '', text: '还没有种子' },
  seed: { icon: '🌱', text: '{n} 颗种子' },
  sprout: { icon: '🌿', text: '{n} 颗种子，开始发芽了' },
  plant: { icon: '🪴', text: '{n} 颗种子，长势不错' },
  tree: { icon: '🌳', text: '{n} 颗种子，已经是一片小林了' },
}

const STORAGE_KEY = 'garden_state'

/**
 * 从本地存储加载花园状态。
 */
export function loadGardenState(): GardenState {
  const raw = wx.getStorageSync(STORAGE_KEY)
  if (raw && typeof raw === 'object') return raw as GardenState
  return { themeCounts: {}, lastSeedEchoAt: -10, sessionEchoCount: 0, totalSeeds: 0 }
}

/**
 * 保存花园状态到本地存储。
 */
export function saveGardenState(state: GardenState): void {
  wx.setStorageSync(STORAGE_KEY, state)
}

/**
 * 收藏时更新主题计数，返回更新后的 state。
 */
export function updateThemeCounts(state: GardenState, themes: string[]): GardenState {
  const counts = { ...state.themeCounts }
  for (let i = 0; i < themes.length; i++) {
    counts[themes[i]] = (counts[themes[i]] || 0) + 1
  }
  const next: GardenState = {
    themeCounts: counts,
    lastSeedEchoAt: state.lastSeedEchoAt,
    sessionEchoCount: state.sessionEchoCount,
    totalSeeds: state.totalSeeds + 1,
  }
  saveGardenState(next)
  return next
}

/**
 * 判断是否应该触发落种文案。
 */
export function shouldTriggerSeedEcho(state: GardenState): boolean {
  if (state.totalSeeds < 3) return false
  if (state.sessionEchoCount >= 2) return false
  if (state.totalSeeds - state.lastSeedEchoAt < 3) return false
  return Math.random() < 0.25
}

/**
 * 标记已触发一次落种文案。
 */
export function markSeedEchoTriggered(state: GardenState): GardenState {
  const next: GardenState = {
    themeCounts: state.themeCounts,
    lastSeedEchoAt: state.totalSeeds,
    sessionEchoCount: state.sessionEchoCount + 1,
    totalSeeds: state.totalSeeds,
  }
  saveGardenState(next)
  return next
}

/**
 * 重置会话内的落种计数（每次 app 打开时调用）。
 */
export function resetSessionEchoCount(state: GardenState): GardenState {
  const next: GardenState = { ...state, sessionEchoCount: 0 }
  saveGardenState(next)
  return next
}

/**
 * 生成落种文案，返回 null 表示无合适文案。
 */
export function generateSeedEcho(
  state: GardenState,
  sentence: Sentence,
  bookmarks: BookmarkItem[],
): string | null {
  const crossAuthors = collectUniqueAuthors(bookmarks)

  if (crossAuthors.length >= 2 && Math.random() < 0.4) {
    return generateCrossBookEcho(crossAuthors, sentence, bookmarks)
  }

  const topTheme = getTopThemeEntry(state)
  if (topTheme && topTheme[1] >= 2) {
    return generateThemeEcho(topTheme)
  }

  return null
}

function collectUniqueAuthors(bookmarks: BookmarkItem[]): string[] {
  const seen: Record<string, boolean> = {}
  const result: string[] = []
  for (let i = 0; i < bookmarks.length; i++) {
    if (!seen[bookmarks[i].book_author]) {
      seen[bookmarks[i].book_author] = true
      result.push(bookmarks[i].book_author)
    }
  }
  return result
}

function generateCrossBookEcho(
  authors: string[],
  _sentence: Sentence,
  _bookmarks: BookmarkItem[],
): string {
  const a1 = authors[0]
  const a2 = authors[authors.length - 1]
  const templates = [
    a1 + '和' + a2 + '，隔了好远，你倒是把他们安排成了邻居。',
    a1 + '那颗和' + a2 + '那颗，地下好像悄悄接上了。',
    '有意思，' + a1 + '和' + a2 + '在你的花园里变成了邻居。',
  ]
  return templates[Math.floor(Math.random() * templates.length)]
}

function generateThemeEcho(topTheme: [string, number]): string {
  const templates = [
    '这是你种下的第' + topTheme[1] + '颗关于"' + topTheme[0] + '"的种子了。',
    '你好像对"' + topTheme[0] + '"这个词特别敏感。',
    '又一颗关于"' + topTheme[0] + '"的。你在想什么呢。',
  ]
  return templates[Math.floor(Math.random() * templates.length)]
}

function getTopThemeEntry(state: GardenState): [string, number] | null {
  const entries = Object.keys(state.themeCounts)
  if (entries.length === 0) return null
  let maxKey = entries[0]
  let maxVal = state.themeCounts[maxKey]
  for (let i = 1; i < entries.length; i++) {
    const v = state.themeCounts[entries[i]]
    if (v > maxVal) {
      maxKey = entries[i]
      maxVal = v
    }
  }
  return [maxKey, maxVal]
}

/**
 * 从主题计数中取 top N 主题词。
 */
export function getTopThemes(themeCounts: Record<string, number>, n: number): string[] {
  const entries = Object.keys(themeCounts)
  const sorted: Array<{ key: string; val: number }> = []
  for (let i = 0; i < entries.length; i++) {
    if (themeCounts[entries[i]] > 0) {
      sorted.push({ key: entries[i], val: themeCounts[entries[i]] })
    }
  }
  sorted.sort(function (a, b) { return b.val - a.val })
  const result: string[] = []
  for (let i = 0; i < Math.min(n, sorted.length); i++) {
    result.push(sorted[i].key)
  }
  return result
}

/**
 * 根据种子数量返回花园生长阶段。
 */
export function getGardenStage(seedCount: number): GardenStage {
  if (seedCount <= 0) return 'empty'
  if (seedCount <= 4) return 'seed'
  if (seedCount <= 9) return 'sprout'
  if (seedCount <= 19) return 'plant'
  return 'tree'
}

/**
 * 获取阶段文案，替换 {n} 为实际数量。
 */
export function getStageText(stage: GardenStage, seedCount: number): string {
  return STAGE_CONFIG[stage].text.replace('{n}', String(seedCount))
}

/**
 * 从收藏列表构建主题计数（用于花园页）。
 */
export function buildThemeCountsFromBookmarks(bookmarks: BookmarkItem[]): Record<string, number> {
  const counts: Record<string, number> = {}
  for (let i = 0; i < bookmarks.length; i++) {
    const themes = bookmarks[i].themes
    if (themes) {
      for (let j = 0; j < themes.length; j++) {
        counts[themes[j]] = (counts[themes[j]] || 0) + 1
      }
    }
  }
  return counts
}
