import type { AgentReplyItem, NotificationPayload } from '../types/index'
import { request } from '../utils/request'

interface SproutData {
  id: string
  text: string
  target_sentence_id: string | null
  created_at: string
}

interface GardenStatus {
  seed_count: number
  stage: string
  top_themes: string[]
  has_unread_sprout: boolean
}

interface CheckReplyResponse {
  has_unread_reply: boolean
  reply_id?: string
  reply_hook?: string
}

interface ReplyListResponse {
  items: AgentReplyItem[]
}

export async function fetchSprout(): Promise<SproutData | null> {
  const res = await new Promise<{ statusCode: number; data: SproutData }>((resolve, reject) => {
    const token = wx.getStorageSync('token') as string
    wx.request({
      url: `${require('../utils/constants').API_BASE}/api/garden/sprout`,
      method: 'GET',
      header: { Authorization: `Bearer ${token}` },
      success(res) { resolve(res as unknown as { statusCode: number; data: SproutData }) },
      fail(err) { reject(err) },
    })
  })
  if (res.statusCode === 204) return null
  if (res.statusCode === 200) return res.data
  return null
}

export function markSproutShown(sproutId: string): Promise<void> {
  return request({ url: '/api/garden/sprout/shown', method: 'POST', data: { sprout_id: sproutId }, needAuth: true }) as Promise<void>
}

export function fetchGardenStatus(): Promise<GardenStatus> {
  return request<GardenStatus>({ url: '/api/garden/status', needAuth: true })
}

export function checkUnreadReply(): Promise<CheckReplyResponse> {
  return request<CheckReplyResponse>({ url: '/api/garden/check', needAuth: true })
}

export function fetchReplies(limit: number = 20): Promise<ReplyListResponse> {
  return request<ReplyListResponse>({ url: `/api/garden/replies?limit=${limit}`, needAuth: true })
}

export function submitReaction(replyId: string, reaction: string): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>({ url: `/api/garden/replies/${replyId}/react`, method: 'POST', data: { reaction }, needAuth: true })
}

export function markReplyRead(replyId: string): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>({ url: `/api/garden/replies/${replyId}/read`, method: 'POST', needAuth: true })
}

let _notificationCallback: ((payload: NotificationPayload) => void) | null = null
let _heartbeatTimer = 0

export function setNotificationCallback(cb: (payload: NotificationPayload) => void) {
  _notificationCallback = cb
}

export function handleNotificationFromResponse(data: Record<string, unknown>) {
  if (!data || !_notificationCallback) return
  const n = data['_notification'] as NotificationPayload | undefined
  if (n && n.has_unread_reply) {
    _notificationCallback(n)
  }
}

export function startHeartbeat() {
  stopHeartbeat()
  _heartbeatTimer = setInterval(async () => {
    const token = wx.getStorageSync('token') as string
    if (!token) return
    const resp = await checkUnreadReply()
    if (resp.has_unread_reply && _notificationCallback) {
      _notificationCallback({
        has_unread_reply: true,
        reply_id: resp.reply_id,
        reply_hook: resp.reply_hook,
      })
    }
  }, 60000) as unknown as number
}

export function stopHeartbeat() {
  if (_heartbeatTimer) {
    clearInterval(_heartbeatTimer)
    _heartbeatTimer = 0
  }
}

export function resetHeartbeat() {
  stopHeartbeat()
  startHeartbeat()
}
