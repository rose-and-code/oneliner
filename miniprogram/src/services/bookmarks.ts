import type { BookmarkItem } from '../types/index'
import { request } from '../utils/request'

/**
 * 切换收藏状态
 */
export function toggleBookmark(sentenceId: string): Promise<{ is_bookmarked: boolean }> {
  return request<{ is_bookmarked: boolean }>({
    url: '/api/bookmarks/toggle',
    method: 'POST',
    data: { sentence_id: sentenceId },
    needAuth: true,
  })
}

/**
 * 获取收藏列表
 */
export function fetchBookmarks(): Promise<BookmarkItem[]> {
  return request<BookmarkItem[]>({
    url: '/api/bookmarks/list',
    needAuth: true,
  })
}
