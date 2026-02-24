import type { BookWithSentences } from '../types/index'
import { request } from '../utils/request'
import { isLoggedIn } from './auth'

/**
 * 获取所有书籍和句子，登录后自动带 token 以获取收藏状态
 */
export async function fetchAllBooks(): Promise<BookWithSentences[]> {
  const res = await request<{ items: BookWithSentences[] }>({
    url: '/api/books/all',
    needAuth: isLoggedIn(),
  })
  return res.items
}
