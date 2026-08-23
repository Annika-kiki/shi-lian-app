const { getRecipeById } = require("../../utils/mock")
const { saveMeal: saveMealRecord } = require("../../utils/meal")

Page({
  data: {
    recipe: getRecipeById("1")
  },

  onLoad(query) {
    const recipe = getRecipeById(query.id || "1")
    this.setData({ recipe })
  },

  saveMeal() {
    saveMealRecord(this.data.recipe)
    wx.showToast({
      title: "已记入今日饮食",
      icon: "success"
    })
    setTimeout(() => {
      wx.redirectTo({
        url: "/pages/food/home"
      })
    }, 300)
  },

  onBottomNav(event) {
    wx.redirectTo({
      url: event.detail.route
    })
  }
})
