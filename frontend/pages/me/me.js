const { getUser } = require("../../utils/user")

Page({
  data: {
    me: (() => {
      const user = getUser()
      return {
        avatar: user.avatar || "🍃",
        name: user.name || "用户",
        goal: user.goal || "减脂",
        height: `${user.height} cm`,
        weight: `${user.weight} kg`,
        trainingCount: "6 次",
        streak: "16 天"
      }
    })()
  },

  onShow() {
    const user = getUser()
    this.setData({
      me: {
        avatar: user.avatar || "🍃",
        name: user.name || "用户",
        goal: user.goal || "减脂",
        height: `${user.height} cm`,
        weight: `${user.weight} kg`,
        trainingCount: "6 次",
        streak: "16 天"
      }
    })
  },

  goBody() {
    wx.navigateTo({
      url: "/pages/body/body"
    })
  },

  goTrainingHistory() {
    wx.redirectTo({
      url: "/pages/calendar/calendar"
    })
  },

  goFavorites() {
    wx.redirectTo({
      url: "/pages/training/home"
    })
  },

  goPrivacy() {
    wx.showToast({
      title: "隐私设置待接入",
      icon: "none"
    })
  },

  onBottomNav(event) {
    wx.redirectTo({
      url: event.detail.route
    })
  }
})
