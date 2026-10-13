const { getRecipe, getMeals, createMealFromRecipe } = require("../../utils/api")
const { saveMeal: saveMealRecord, getMealSummary, MEAL_SLOTS } = require("../../utils/meal")
const { navigateBackOrRedirect } = require("../../utils/navigation")


function findLocalRecipe(id) {
  const cached = wx.getStorageSync("generatedRecipes")
  if (!Array.isArray(cached)) return null
  return cached.find((item) => String(item.id) === String(id)) || null
}

function findSelectedRecipe(id) {
  const selected = wx.getStorageSync("selectedRecipe")
  if (!selected || String(selected.id) !== String(id)) return null
  return selected
}

function findSavedRecipe(id) {
  const item = getMealSummary().items.find((meal) => (
    String(meal.recipeId) === String(id) && meal.recipe
  ))
  return item ? item.recipe : null
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
    if (!id) {
      wx.showToast({ title: "这餐没有可查看的菜谱", icon: "none" })
      return
    }

    const local = findSelectedRecipe(id) || findLocalRecipe(id) || findSavedRecipe(id)
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
    navigateBackOrRedirect("/pages/food/home")
  },

  saveMeal() {
    if (!this.data.recipe) return

    wx.showLoading({ title: "保存中" })
    getMeals()
      .catch(() => [])
      .then((records) => {
        const slot = pickMealSlot(records)
        saveMealRecord(this.data.recipe, slot.key)
        // 本地记录是主流程；后端同步失败不应阻止用户看到已保存的结果。
        return createMealFromRecipe(this.data.recipe, slot.label).catch(() => null)
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
