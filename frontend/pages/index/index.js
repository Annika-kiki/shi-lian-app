const { saveUser, getUser } = require("../../utils/user")

Page({
  goProfile() {
    const fallback = getUser()
    wx.getUserProfile({
      desc: "用于完善练食记的个人资料和首页称呼",
      success: (res) => {
        const userInfo = res.userInfo || {}
        saveUser({
          ...fallback,
          name: userInfo.nickName || fallback.name,
          avatar: userInfo.avatarUrl || fallback.avatar
        })
        wx.redirectTo({
          url: "/pages/profile/profile"
        })
      },
      fail: () => {
        saveUser(fallback)
        wx.redirectTo({
          url: "/pages/profile/profile"
        })
      }
    })
  },

  skip() {
    saveUser(getUser())
    wx.redirectTo({
      url: "/pages/home/home"
    })
  }
})
