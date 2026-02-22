import { request } from '../utils/request'

interface LoginResponse {
  token: string
  user_id: string
}

function saveLoginResult(data: LoginResponse) {
  wx.setStorageSync('token', data.token)
  wx.setStorageSync('user_id', data.user_id)
}

export function login(): Promise<LoginResponse> {
  return new Promise((resolve, reject) => {
    wx.login({
      success(res) {
        if (!res.code) {
          reject(new Error('wx.login 失败'))
          return
        }
        request<LoginResponse>({
          url: '/api/auth/login',
          method: 'POST',
          data: { code: res.code },
        })
          .then((data) => {
            saveLoginResult(data)
            console.log('微信登录成功')
            resolve(data)
          })
          .catch(() => {
            console.log('微信登录失败，尝试开发模式登录')
            request<LoginResponse>({
              url: '/api/auth/dev-login',
              method: 'POST',
            })
              .then((data) => {
                saveLoginResult(data)
                console.log('开发模式登录成功')
                resolve(data)
              })
              .catch(reject)
          })
      },
      fail: reject,
    })
  })
}

export function isLoggedIn(): boolean {
  return !!wx.getStorageSync('token')
}

export function updateProfile(nickname: string, avatarUrl: string): Promise<void> {
  return request<void>({
    url: '/api/auth/me',
    method: 'PUT',
    data: { nickname, avatar_url: avatarUrl },
    needAuth: true,
  })
}
