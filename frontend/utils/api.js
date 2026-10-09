const DEFAULT_BASE_URL = "http://127.0.0.1:8010"

function getBaseUrl() {
  return wx.getStorageSync("apiBaseUrl") || DEFAULT_BASE_URL
}

function request(path, options = {}) {
  const userId = wx.getStorageSync("apiUserId")
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${getBaseUrl()}${path}`,
      method: options.method || "GET",
      data: options.data,
      header: {
        "content-type": "application/json",
        ...(userId ? { "X-User-Id": String(userId) } : {}),
        ...(options.header || {})
      },
      success(response) {
        const body = response.data || {}
        if (response.statusCode >= 200 && response.statusCode < 300 && body.code === 0) {
          resolve(body.data)
          return
        }
        reject(new Error(body.message || `请求失败 (${response.statusCode})`))
      },
      fail(error) {
        reject(new Error(error.errMsg || "无法连接后端服务"))
      }
    })
  })
}

async function ensureLogin(profile = {}) {
  const existing = wx.getStorageSync("apiUserId")
  if (existing) return existing
  const data = await request("/api/auth/mock-login", {
    method: "POST",
    data: {
      nickname: profile.name || "食练周期用户",
      avatar: profile.avatar || null,
      mock_openid: wx.getStorageSync("mockOpenid") || "miniprogram-dev-user"
    }
  })
  wx.setStorageSync("apiUserId", data.user_id)
  return data.user_id
}

function showApiError(error) {
  wx.showToast({ title: error.message || "服务暂不可用", icon: "none", duration: 2500 })
}

module.exports = { DEFAULT_BASE_URL, getBaseUrl, request, ensureLogin, showApiError }
