const { bodyParts, trainingSummary } = require("../../utils/mock")

Page({
  data: {
    bodyParts,
    summary: {
      ...trainingSummary,
      recentDate: trainingSummary.recent.date
    }
  },

  openList(event) {
    const part = event.currentTarget.dataset.part || "chest"
    wx.navigateTo({
      url: `/pages/training/list?part=${part}`
    })
  },

  openRecent() {
    wx.navigateTo({
      url: "/pages/training/detail?id=bench"
    })
  },

  onBottomNav(event) {
    wx.redirectTo({
      url: event.detail.route
    })
  }
})
