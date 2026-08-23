const { ingredientChips, calorieOptions, tasteOptions } = require("../../utils/mock")

Page({
  data: {
    chips: ingredientChips,
    inputValue: "",
    calories: "约 500 kcal",
    tastes: tasteOptions.map((label) => ({ label, selected: false })),
    calorieOptions
  },

  onInput(event) {
    this.setData({ inputValue: event.detail.value })
  },

  addChip() {
    const value = (this.data.inputValue || "").trim()
    if (!value) return
    this.setData({
      chips: [...this.data.chips, value],
      inputValue: ""
    })
  },

  removeChip(event) {
    const index = event.currentTarget.dataset.index
    const chips = this.data.chips.slice()
    chips.splice(index, 1)
    this.setData({ chips })
  },

  setCalories(event) {
    this.setData({ calories: event.currentTarget.dataset.value })
  },

  toggleTaste(event) {
    const value = event.currentTarget.dataset.value
    const tastes = this.data.tastes.map((item) => {
      if (item.label !== value) return item
      return {
        ...item,
        selected: !item.selected
      }
    })
    this.setData({ tastes })
  },

  generate() {
    wx.navigateTo({
      url: "/pages/food/result"
    })
  },

  onBottomNav(event) {
    wx.redirectTo({
      url: event.detail.route
    })
  }
})
