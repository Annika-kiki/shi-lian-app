const { ingredientChips: fallbackIngredientChips, calorieOptions, tasteOptions } = require("../../utils/mock")
const { generateRecipes, getIngredients } = require("../../utils/api")
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


const SUGGESTED_INGREDIENTS = [
  "鸡胸肉",
  "鸡蛋",
  "牛肉",
  "三文鱼",
  "虾仁",
  "北豆腐",
  "米饭",
  "糙米饭",
  "燕麦",
  "红薯",
  "西兰花",
  "番茄",
  "黄瓜",
  "菠菜",
  "香菇",
  "金针菇",
  "土豆",
  "玉米",
  "洋葱",
  "菜花",
  "生菜",
  "胡萝卜",
  "荞麦面"
]

function getCalorieValue(label) {
  const match = String(label || "").match(/\d+/)
  const value = Number(match ? match[0] : 500)
  return Number.isFinite(value) ? value : 500
}

function buildTasteState(preferences = []) {
  const selected = new Set((Array.isArray(preferences) ? preferences : []).map((item) => String(item || "").trim()).filter(Boolean))
  return tasteOptions.map((label) => ({
    label,
    selected: selected.has(label) || selected.has(label.replace(/\s+/g, ""))
  }))
}

function buildSeedChips(items = []) {
  const names = items.map((item) => String(item && item.name ? item.name : "").trim()).filter(Boolean)
  const chips = []
  SUGGESTED_INGREDIENTS.forEach((name) => {
    if (names.includes(name) && !chips.includes(name)) {
      chips.push(name)
    }
  })
  names.forEach((name) => {
    if (chips.length < 12 && !chips.includes(name)) {
      chips.push(name)
    }
  })
  return chips.length ? chips : fallbackIngredientChips.slice()
}

Page({
  data: {
    chips: fallbackIngredientChips.slice(),
    inputValue: "",
    calories: "约500 kcal",
    targetCalories: 500,
    tastes: buildTasteState(),
    calorieOptions
  },

  onLoad() {
    this.loadIngredients()
  },

  onShow() {
    const last = wx.getStorageSync("lastRecipeRequest")
    if (!last) return
    this.setData({
      calories: last.calories || `约${Number(last.targetCalories) || 500} kcal`,
      targetCalories: Number(last.targetCalories) || 500,
      tastes: buildTasteState(last.preferences || [])
    })
  },

  loadIngredients() {
    getIngredients()
      .then((items) => {
        const chips = buildSeedChips(items)
        if (chips.length) {
          this.setData({ chips })
        }
      })
      .catch(() => {})
  },

  goBack() {
    navigateBackOrRedirect("/pages/food/home")
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
    const calories = String(event.currentTarget.dataset.value || "").trim()
    this.setData({
      calories,
      targetCalories: getCalorieValue(calories)
    })
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
    const ingredients = this.data.chips.filter((item) => String(item || "").trim())
    const preferences = this.data.tastes.filter((item) => item.selected).map((item) => item.label)
    const targetCalories = getCalorieValue(this.data.targetCalories || this.data.calories)
    const request = {
      ingredients,
      targetCalories,
      calories: this.data.calories || `约${targetCalories} kcal`,
      preferences,
      recipeRound: 0,
      createdAt: Date.now()
    }
    request.requestKey = [
      request.ingredients.join("|"),
      request.targetCalories,
      request.preferences.join("|"),
      request.recipeRound
    ].join("::")

    wx.setStorageSync("lastRecipeRequest", request)
    wx.removeStorageSync("generatedRecipes")
    wx.removeStorageSync("generatedRecipesRequestKey")

    wx.showLoading({ title: "生成中" })
    generateRecipes(ingredients, targetCalories, preferences, 0)
      .then((recipes) => {
        wx.setStorageSync("generatedRecipes", recipes)
        wx.setStorageSync("generatedRecipesRequestKey", request.requestKey)
      })
      .catch(() => {
        wx.showToast({
          title: "后端未启动，先用本地食谱",
          icon: "none"
        })
      })
      .finally(() => {
        wx.hideLoading()
        wx.navigateTo({
          url: "/pages/food/result"
        })
      })
  },

  onBottomNav(event) {
    const route = (event.currentTarget && event.currentTarget.dataset && event.currentTarget.dataset.route) ||
      (event.detail && event.detail.route)
    if (!route) return
    wx.redirectTo({
      url: route
    })
  }
})
