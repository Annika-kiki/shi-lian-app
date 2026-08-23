const { homeSummary } = require("../../utils/mock")
const { getMealSummary } = require("../../utils/meal")
const { getUser } = require("../../utils/user")

function buildGreeting(name) {
  const hour = new Date().getHours()
  const prefix = hour < 12 ? "早上好" : hour < 18 ? "下午好" : "晚上好"
  return `${prefix}，${name}`
}

Page({
  data: {
    summary: {
      ...homeSummary,
      greeting: buildGreeting(getUser().name),
      kcalText: "0",
      proteinPercent: `${(homeSummary.protein.current / homeSummary.protein.target) * 100}%`,
      carbsPercent: `${(homeSummary.carbs.current / homeSummary.carbs.target) * 100}%`,
      fatPercent: `${(homeSummary.fat.current / homeSummary.fat.target) * 100}%`
    },
    meals: []
  },

  onShow() {
    const user = getUser()
    const { items, total, remain } = getMealSummary()
    this.setData({
      summary: {
        ...this.data.summary,
        greeting: buildGreeting(user.name),
        kcalText: total.toLocaleString(),
        remainText: remain,
        intakePercent: `${Math.min(100, (total / 1800) * 100)}%`
      },
      meals: items
    })
  },

  goFood() {
    wx.redirectTo({
      url: "/pages/food/home"
    })
  },

  goTraining() {
    wx.redirectTo({
      url: "/pages/training/home"
    })
  },

  goMealDetail(event) {
    const item = this.data.meals[event.currentTarget.dataset.index]
    if (!item) return
    if (!item.recorded) {
      wx.redirectTo({
        url: "/pages/food/input"
      })
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
