const { getMealSummary } = require("../../utils/meal")
const { getTodayDashboard, getMeals } = require("../../utils/api")

function mapMealItems(records) {
  const slots = [
    { key: "breakfast", label: "早餐", icon: "🍲" },
    { key: "lunch", label: "午餐", icon: "🍱" },
    { key: "dinner", label: "晚餐", icon: "🌙" }
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

Page({
  data: {
    meals: [],
    remain: 1800,
    totalText: "0",
    intakePercent: "0%"
  },

  onShow() {
    this.loadMeals()
  },

  loadMeals() {
    Promise.all([
      getTodayDashboard().catch(() => null),
      getMeals().catch(() => [])
    ]).then(([dashboard, records]) => {
      if (dashboard) {
        this.setData({
          remain: Math.round(dashboard.remaining_calories_kcal),
          totalText: Math.round(dashboard.intake_calories_kcal).toLocaleString(),
          intakePercent: `${Math.min(100, (dashboard.intake_calories_kcal / 1800) * 100)}%`,
          meals: mapMealItems(records)
        })
        return
      }

      const local = getMealSummary()
      this.setData({
        meals: local.items,
        remain: local.remain,
        totalText: local.total.toLocaleString(),
        intakePercent: local.percent
      })
    }).catch(() => {})
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
