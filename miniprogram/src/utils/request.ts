import { API_BASE } from './constants'

interface RequestOptions {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: Record<string, unknown>
  needAuth?: boolean
}

/**
 * 统一请求封装，自动注入 token
 */
export function request<T>(options: RequestOptions): Promise<T> {
  const { url, method = 'GET', data, needAuth = false } = options
  const header: Record<string, string> = { 'Content-Type': 'application/json' }

  if (needAuth) {
    const token = wx.getStorageSync('token') as string
    if (token) {
      header['Authorization'] = `Bearer ${token}`
    }
  }

  return new Promise((resolve, reject) => {
    wx.request({
      url: `${API_BASE}${url}`,
      method,
      data,
      header,
      success(res) {
        if (res.statusCode === 401) {
          wx.removeStorageSync('token')
          wx.removeStorageSync('user_id')
          reject(new Error('未登录'))
          return
        }
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as T)
        } else {
          reject(new Error(`请求失败: ${res.statusCode}`))
        }
      },
      fail(err) {
        reject(new Error(err.errMsg))
      },
    })
  })
}
