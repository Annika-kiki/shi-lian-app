const { getRecipe, getMeals, createMealFromRecipe } = require("../../utils/api")
const { MEAL_SLOTS } = require("../../utils/meal")
function navigateBackOrRedirect(fallbackUrl) {
  const pages = getCurrentPages()
  if (pages.length > 1) {
    wx.navigateBack({ delta: 1 })
    return
  }
  if (fallbackUrl) {
    wx.redirectTo({ url: fallbackUrl })
  }
}


function findLocalRecipe(id) {
  const cached = wx.getStorageSync("generatedRecipes")
  if (!Array.isArray(cached)) return null
  return cached.find((item) => String(item.id) === String(id)) || null
}

function pickMealSlot(records = []) {
  const used = new Set(records.map((item) => String(item.meal_type || "").toLowerCase()))
  return MEAL_SLOTS.find((slot) => !used.has(slot.key) && !used.has(slot.label)) || MEAL_SLOTS[0]
}

Page({
  data: {
    recipe: null
  },

  onLoad(query) {
    const id = String(query.id || "")
    if (!id) return

    const local = findLocalRecipe(id)
    if (local) {
      this.setData({ recipe: local })
      return
    }

    getRecipe(id)
      .then((recipe) => {
        this.setData({ recipe })
      })
      .catch(() => {
        const fallback = findLocalRecipe(id)
        if (fallback) {
          this.setData({ recipe: fallback })
          return
        }
        wx.showToast({
          title: "菜谱加载失败",
          icon: "none"
        })
      })
  },

  goBack() {
    navigateBackOrRedirect("/pages/food/result")
  },

  saveMeal() {
    if (!this.data.recipe) return

    wx.showLoading({ title: "保存中" })
    let selectedSlot
    getMeals()
      .then((records) => {
        selectedSlot = pickMealSlot(records)
        return createMealFromRecipe(this.data.recipe, selectedSlot.label)
      })
      .then(() => {
        wx.showToast({
          title: "已记入今日饮食",
          icon: "success",
          duration: 800,
          complete: () => {
            wx.redirectTo({
              url: "/pages/food/home"
            })
          }
        })
      })
      .catch((error) => {
        wx.showToast({
          title: error.message || "保存失败，请稍后重试",
          icon: "none"
        })
      })
      .finally(() => {
        wx.hideLoading()
      })
  },

  onBottomNav(event) {
    wx.redirectTo({
      url: event.detail.route
    })
  }
})
