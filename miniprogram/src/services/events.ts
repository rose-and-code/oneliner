import { request } from '../utils/request'
import { isLoggedIn } from './auth'
import { checkUnreadSprout } from './garden'

interface EventItem {
  event_type: string
  sentence_id: string
  book_id: string
  duration_ms: number
}

let buffer: EventItem[] = []
let flushTimer = 0
let _sproutCallback: ((payload: { has_unread_sprout: boolean; sprout_id?: string; sprout_hook?: string }) => void) | null = null

export function setSproutCheckCallback(cb: typeof _sproutCallback) {
  _sproutCallback = cb
}

function flush() {
  if (buffer.length === 0) return
  if (!isLoggedIn()) return
  const events = buffer.slice()
  buffer = []
  request({ url: '/api/events/batch', method: 'POST', data: { events }, needAuth: true }).then(() => {
    if (!_sproutCallback) return
    setTimeout(async () => {
      const resp = await checkUnreadSprout()
      if (resp.has_unread_sprout && _sproutCallback) {
        _sproutCallback(resp)
      }
    }, 3000)
  })
}

function scheduleFlush() {
  if (flushTimer) return
  flushTimer = setTimeout(() => {
    flushTimer = 0
    flush()
  }, 2000) as unknown as number
}

export function trackDwell(sentenceId: string, bookId: string, durationMs: number) {
  if (durationMs < 3000) return
  buffer.push({ event_type: 'dwell', sentence_id: sentenceId, book_id: bookId, duration_ms: durationMs })
  scheduleFlush()
}

export function trackContextOpen(sentenceId: string, bookId: string) {
  buffer.push({ event_type: 'context_open', sentence_id: sentenceId, book_id: bookId, duration_ms: 0 })
  scheduleFlush()
}

export function trackFlip(sentenceId: string, bookId: string) {
  buffer.push({ event_type: 'flip', sentence_id: sentenceId, book_id: bookId, duration_ms: 0 })
  scheduleFlush()
}

export function flushEvents() {
  flush()
}
