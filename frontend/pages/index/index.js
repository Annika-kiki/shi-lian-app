const { saveUser, getUser } = require("../../utils/user")
const { ensureLogin } = require("../../utils/api")

function enterPage(url) {
  wx.redirectTo({ url })
}

function enterOffline(url) {
  wx.showToast({
    title: "后端未启动，已使用本地模式",
    icon: "none"
  })
  enterPage(url)
}

Page({
  goProfile() {
    const fallback = getUser()
    wx.getUserProfile({
      desc: "用于完善食练周期的个人资料和首页称呼",
      success: (res) => {
        const userInfo = res.userInfo || {}
        const user = saveUser({
          ...fallback,
          name: userInfo.nickName || fallback.name,
          avatar: userInfo.avatarUrl || fallback.avatar
        })
        ensureLogin(user)
          .then(() => enterPage("/pages/profile/profile"))
          .catch(() => enterOffline("/pages/profile/profile"))
      },
      fail: () => {
        const user = saveUser(fallback)
        ensureLogin(user)
          .then(() => enterPage("/pages/profile/profile"))
          .catch(() => enterOffline("/pages/profile/profile"))
      }
    })
  },

  skip() {
    const user = saveUser(getUser())
    ensureLogin(user)
      .then(() => enterPage("/pages/home/home"))
      .catch(() => enterOffline("/pages/home/home"))
  }
})
