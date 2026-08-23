const { recipePlans } = require("../../utils/mock")

Page({
  data: {
    recipes: recipePlans
  },

  goDetail(event) {
    const id = event.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/food/detail?id=${id}`
    })
  },

  regenerate() {
    wx.showToast({
      title: "已重新生成",
      icon: "none"
    })
  },

  onBottomNav(event) {
    wx.redirectTo({
      url: event.detail.route
    })
  }
})
