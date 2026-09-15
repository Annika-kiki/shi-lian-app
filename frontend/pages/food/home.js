const { getMealSummary } = require("../../utils/meal")
const { getTodayDashboard, getMeals, getTodayInsight, quickLog } = require("../../utils/api")

function mapMealItems(records) {
  const slots = [
    { key: "breakfast", label: "早餐" },
    { key: "lunch", label: "午餐" },
    { key: "dinner", label: "晚餐" }
  ]
  return slots.map((slot) => {
    const record = records.find((item) => item.meal_type === slot.label || item.meal_type === slot.key)
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
      kcal: Math.round(record.calories_kcal),
      detail: record.name || record.note || "已记录",
      recipeId: record.recipe_id || ""
    }
  })
}

function pickAdvice(insight) {
  return insight && insight.advice && insight.advice.length
    ? insight.advice[0]
    : "记录一餐后，食练周期会分析这一天的饮食是否适合你的目标。"
}

Page({
  data: {
    meals: [],
    remain: 1800,
    targetText: "1,800",
    totalText: "0",
    intakePercent: "0%",
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
      getMeals().catch(() => []),
      getTodayInsight().catch(() => null)
    ]).then(([dashboard, records, insight]) => {
      if (dashboard) {
        const target = Number(dashboard.daily_calorie_target) || 1800
        this.setData({
          remain: Math.round(dashboard.remaining_calories_kcal),
          targetText: Math.round(target).toLocaleString(),
          totalText: Math.round(dashboard.intake_calories_kcal).toLocaleString(),
          intakePercent: `${Math.min(100, (dashboard.intake_calories_kcal / target) * 100)}%`,
          meals: mapMealItems(records),
          dietScore: Math.round(insight && insight.diet_score || 0),
          insightText: pickAdvice(insight)
        })
        return
      }

      const local = getMealSummary()
      this.setData({
        meals: local.items,
        remain: local.remain,
        targetText: Math.round(local.dailyTarget || 1800).toLocaleString(),
        totalText: local.total.toLocaleString(),
        intakePercent: local.percent,
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

  goInput() {
    wx.navigateTo({ url: "/pages/food/input" })
  },

  goRecipe(event) {
    const item = this.data.meals[event.currentTarget.dataset.index]
    if (!item) return
    if (!item.recorded) {
      this.goInput()
      return
    }
    wx.navigateTo({ url: `/pages/food/detail?id=${item.recipeId}` })
  },

  onBottomNav(event) {
    wx.redirectTo({ url: event.detail.route })
  }
})
