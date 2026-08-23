const { getMealSummary } = require("../../utils/meal")

Page({
  data: {
    meals: [],
    remain: 1800,
    totalText: "0",
    intakePercent: "0%"
  },

  onShow() {
    const { items, total, remain } = getMealSummary()
    this.setData({
      meals: items,
      remain,
      totalText: total.toLocaleString(),
      intakePercent: `${Math.min(100, (total / 1800) * 100)}%`
    })
  },

  goInput() {
    wx.navigateTo({
      url: "/pages/food/input"
    })
  },

  goRecipe(event) {
    const item = this.data.meals[event.currentTarget.dataset.index]
    if (!item) return
    if (!item.recorded) {
      this.goInput()
      return
    }
    wx.navigateTo({
      url: `/pages/food/detail?id=${item.recipeId}`
    })
  },

  onBottomNav(event) {
    wx.redirectTo({
      url: event.detail.route
    })
  }
})
