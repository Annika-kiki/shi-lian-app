const { getMealSummary } = require("../../utils/meal")
const { getTodayDashboard, getMeals, getTodayInsight, quickLog } = require("../../utils/api")

function mapMealItems(records) {
  const localItems = getMealSummary().items
  const slots = [
    { key: "breakfast", label: "早餐" },
    { key: "lunch", label: "午餐" },
    { key: "dinner", label: "晚餐" }
  ]
  return slots.map((slot) => {
    const record = records.find((item) => item.meal_type === slot.label || item.meal_type === slot.key)
    const local = localItems.find((item) => item.key === slot.key) || {}
    if (!record) {
      return {
        ...slot,
        recorded: false,
        kcal: "尚未记录",
        detail: "点击添加一餐",
        recipeId: ""
      }
    }
    return {
      ...slot,
      recorded: true,
      kcal: record && record.calories_kcal != null
        ? Math.round(record.calories_kcal)
        : local.kcal,
      detail: record && (record.name || record.note) || local.detail || "已记录",
      recipeId: record && record.recipe_id || local.recipeId || "",
      recipe: local.recipe || null
    }
  })
}

function pickAdvice(insight) {
  return insight && insight.advice && insight.advice.length
    ? insight.advice[0]
    : "记录一餐后，食练周期会分析这一天的饮食是否适合你的目标。"
}

// ✅ 统一把百分比格式化成保留 1 位小数（例如 "32.8%"）
function formatPercent(value) {
  const num = parseFloat(value)
  if (!Number.isFinite(num)) return "0%"
  return `${Math.min(100, num).toFixed(1)}%`
}

Page({
  data: {
    meals: [],
    remain: 1800,
    targetText: "1,800",
    totalText: "0",
    intakePercent: "0%",
    ringAngle: 0,
    dietScore: 0,
    insightText: "记录一餐后，食练周期会分析这一天的饮食是否适合你的目标。",
    quickInput: "",
    quickSaving: false
  },

  onShow() {
    this.loadMeals()
  },

  loadMeals() {
    Promise.all([
      getTodayDashboard().catch(() => null),
      getMeals().catch(() => null),
      getTodayInsight().catch(() => null)
    ]).then(([dashboard, records, insight]) => {
      if (dashboard) {
        const target = Number(dashboard.daily_calorie_target) || 1800
        const intake = Number(dashboard.intake_calories_kcal) || 0
        const percentNum = Math.min(100, (intake / target) * 100)
        this.setData({
          remain: Math.round(dashboard.remaining_calories_kcal),
          targetText: Math.round(target).toLocaleString(),
          totalText: Math.round(intake).toLocaleString(),
          intakePercent: formatPercent(percentNum),          // ✅ 保留 1 位
          ringAngle: Math.round(percentNum * 3.6),
          meals: Array.isArray(records) ? mapMealItems(records) : getMealSummary().items,
          dietScore: Math.round(insight && insight.diet_score || 0),
          insightText: pickAdvice(insight)
        })
        return
      }

      const local = getMealSummary()
      const localPercent = parseFloat(local.percent) || 0
      this.setData({
        meals: local.items,
        remain: local.remain,
        targetText: Math.round(local.dailyTarget || 1800).toLocaleString(),
        totalText: local.total.toLocaleString(),
        intakePercent: formatPercent(localPercent),          // ✅ 保留 1 位
        ringAngle: Math.round(localPercent * 3.6),
        dietScore: Math.round(insight && insight.diet_score || 0),
        insightText: pickAdvice(insight)
      })
    }).catch(() => {})
  },

  onQuickInput(event) {
    this.setData({ quickInput: event.detail.value })
  },

  saveQuickLog() {
    const text = String(this.data.quickInput || "").trim()
    if (!text) {
      wx.showToast({ title: "先输入饮食或有氧", icon: "none" })
      return
    }
    this.setData({ quickSaving: true })
    quickLog(text).then(() => {
      wx.showToast({ title: "已记录", icon: "success" })
      this.setData({ quickInput: "" })
      this.loadMeals()
    }).catch((error) => {
      wx.showToast({ title: error.message || "记录失败", icon: "none" })
    }).finally(() => {
      this.setData({ quickSaving: false })
    })
  },

  goInput(e) {
    const mealType = (e && e.currentTarget && e.currentTarget.dataset.mealType) || "早餐"
    wx.navigateTo({
      url: `/pages/food/input?mealType=${encodeURIComponent(mealType)}`
    })
  },

  goCalendar() {
    wx.redirectTo({ url: "/pages/calendar/calendar" })
  },

  goRecipe(e) {
    const item = this.data.meals[e.currentTarget.dataset.index]
    if (!item) return
    if (!item.recorded) {
      const mealType = item.label || "早餐"
      wx.navigateTo({
        url: `/pages/food/input?mealType=${encodeURIComponent(mealType)}`
      })
      return
    }
    if (!item.recipeId) {
      wx.showToast({ title: "这餐没有可查看的菜谱", icon: "none" })
      return
    }
    if (item.recipe) wx.setStorageSync("selectedRecipe", item.recipe)
    wx.navigateTo({ url: `/pages/food/detail?id=${item.recipeId}` })
  },

  onBottomNav(event) {
    wx.redirectTo({ url: event.detail.route })
  }
})