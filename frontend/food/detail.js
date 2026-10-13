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

// ✅ 从 storage 里读用户真实选择的餐次
function resolveMealType() {
  const cached = wx.getStorageSync("currentMealType")
  const label = String(cached || "").trim()
  if (["早餐", "午餐", "晚餐"].includes(label)) {
    return label
  }
  return ""
}

// 兜底：从已有记录里挑一个空槽位
function pickMealSlot(records = []) {
  const used = new Set(records.map((item) => String(item.meal_type || "").toLowerCase()))
  return MEAL_SLOTS.find((slot) => !used.has(slot.key) && !used.has(slot.label)) || MEAL_SLOTS[0]
}

Page({
  data: {
    recipe: null,
    mealType: "早餐"
  },

  onLoad(query) {
    const id = String(query.id || "")
    if (!id) {
      wx.showToast({ title: "这餐没有可查看的菜谱", icon: "none" })
      return
    }

    const chosen = resolveMealType()
    if (chosen) {
      this.setData({ mealType: chosen })
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

    // 🔍 加个调试日志，测试完可以删掉
    console.log("【debug】saveMeal currentMealType =", wx.getStorageSync("currentMealType"))

    wx.showLoading({ title: "保存中" })

    const chosenMealType = resolveMealType()

    const finalize = (mealLabel, mealKey) => {
      saveMealRecord(this.data.recipe, mealKey)
      return createMealFromRecipe(this.data.recipe, mealLabel).catch(() => null)
    }

    if (chosenMealType) {
      const slot = MEAL_SLOTS.find((s) => s.label === chosenMealType) || MEAL_SLOTS[0]
      Promise.resolve(finalize(slot.label, slot.key))
        .then(() => {
          wx.showToast({
            title: `已记入${slot.label}`,
            icon: "success",
            duration: 800,
            complete: () => {
              wx.redirectTo({ url: "/pages/food/home" })
            }
          })
        })
        .finally(() => {
          wx.hideLoading()
        })
      return
    }

    getMeals()
      .catch(() => [])
      .then((records) => {
        const slot = pickMealSlot(records)
        return finalize(slot.label, slot.key)
      })
      .then(() => {
        wx.showToast({
          title: "已记入今日饮食",
          icon: "success",
          duration: 800,
          complete: () => {
            wx.redirectTo({ url: "/pages/food/home" })
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