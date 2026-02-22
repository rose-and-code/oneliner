import type { BookWithSentences } from '../types/index'
import { request } from '../utils/request'
import { isLoggedIn } from './auth'

/**
 * 获取所有书籍和句子，登录后自动带 token 以获取收藏状态
 */
export function fetchAllBooks(): Promise<BookWithSentences[]> {
  return request<BookWithSentences[]>({
    url: '/api/sentences/all',
    needAuth: isLoggedIn(),
  })
}
