import type { BookmarkItem } from '../types/index'
import { request } from '../utils/request'

interface ToggleResponse {
  is_favorited: boolean
}

interface FavListResponse {
  items: BookmarkItem[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

export function toggleBookmark(sentenceId: string): Promise<{ is_bookmarked: boolean }> {
  return request<ToggleResponse>({
    url: '/api/favorites/toggle',
    method: 'POST',
    data: { sentence_id: sentenceId },
    needAuth: true,
  }).then((res) => ({ is_bookmarked: res.is_favorited }))
}

export function fetchBookmarks(): Promise<BookmarkItem[]> {
  return request<FavListResponse>({
    url: '/api/favorites/list',
    needAuth: true,
  }).then((res) => res.items)
}
