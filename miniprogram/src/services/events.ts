import { request } from '../utils/request'
import { isLoggedIn } from './auth'

interface EventItem {
  event_type: string
  sentence_id: string
  book_id: string
  duration_ms: number
}

let buffer: EventItem[] = []
let flushTimer = 0

function flush() {
  if (buffer.length === 0) return
  if (!isLoggedIn()) return
  const events = buffer.slice()
  buffer = []
  request({ url: '/api/events/batch', method: 'POST', data: { events }, needAuth: true })
}

function scheduleFlush() {
  if (flushTimer) return
  flushTimer = setTimeout(() => {
    flushTimer = 0
    flush()
  }, 5000) as unknown as number
}

/**
 * 记录用户在某句话上的停留时长
 */
export function trackDwell(sentenceId: string, bookId: string, durationMs: number) {
  if (durationMs < 3000) return
  buffer.push({ event_type: 'dwell', sentence_id: sentenceId, book_id: bookId, duration_ms: durationMs })
  scheduleFlush()
}

/**
 * 记录用户展开了上下文
 */
export function trackContextOpen(sentenceId: string, bookId: string) {
  buffer.push({ event_type: 'context_open', sentence_id: sentenceId, book_id: bookId, duration_ms: 0 })
  scheduleFlush()
}

/**
 * 记录用户翻了面
 */
export function trackFlip(sentenceId: string, bookId: string) {
  buffer.push({ event_type: 'flip', sentence_id: sentenceId, book_id: bookId, duration_ms: 0 })
  scheduleFlush()
}

/**
 * 页面隐藏时立即上报
 */
export function flushEvents() {
  flush()
}
