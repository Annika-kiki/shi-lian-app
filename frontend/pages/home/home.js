const { getUser, calculateNutritionTargets } = require("../../utils/user")
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

function percent(current, target) {
  return `${Math.min(100, (Number(current || 0) / Number(target || 1)) * 100)}%`
}

function buildGreeting(name) {
  const hour = new Date().getHours()
  const prefix = hour < 12 ? "早上好" : hour < 18 ? "下午好" : "晚上好"
  return `${prefix}，${name}`
}

function buildDateText() {
  const now = new Date()
  const weekdays = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
  return `${now.getMonth() + 1}月${now.getDate()}日 · ${weekdays[now.getDay()]}`
}

const initialTargets = calculateNutritionTargets(getUser())

Page({
  data: {
    summary: {
      date: buildDateText(),
      greeting: buildGreeting(getUser().name || "用户"),
      kcalText: "0",
      remainText: initialTargets.dailyCalorieTarget,
      intakePercent: "0%",
      workout: 0,
      protein: { current: 0, target: initialTargets.proteinTargetG },
      carbs: { current: 0, target: initialTargets.carbTargetG },
      fat: { current: 0, target: initialTargets.fatTargetG },
      proteinPercent: "0%",
      carbsPercent: "0%",
      fatPercent: "0%"
    },
    meals: []
  },

  onShow() {
    this.loadDashboard()
  },

  loadDashboard() {
    const user = getUser()
    const localTargets = calculateNutritionTargets(user)
    Promise.all([
      getTodayDashboard().catch(() => null),
      getMeals().catch(() => [])
    ]).then(([dashboard, records]) => {
      if (dashboard) {
        const dailyTarget = Number(dashboard.daily_calorie_target) ||
          Number(dashboard.intake_calories_kcal || 0) + Number(dashboard.remaining_calories_kcal || 0) ||
          localTargets.dailyCalorieTarget
        this.setData({
          summary: {
            date: buildDateText(),
            greeting: buildGreeting(user.name || "用户"),
            kcalText: Math.round(dashboard.intake_calories_kcal).toLocaleString(),
            remainText: Math.round(dashboard.remaining_calories_kcal),
            intakePercent: percent(dashboard.intake_calories_kcal, dailyTarget),
            workout: dashboard.workout_duration_min,
            protein: {
              current: dashboard.nutrition.protein.consumed,
              target: dashboard.nutrition.protein.target || localTargets.proteinTargetG
            },
            carbs: {
              current: dashboard.nutrition.carb.consumed,
              target: dashboard.nutrition.carb.target || localTargets.carbTargetG
            },
            fat: {
              current: dashboard.nutrition.fat.consumed,
              target: dashboard.nutrition.fat.target || localTargets.fatTargetG
            },
            proteinPercent: percent(dashboard.nutrition.protein.consumed, dashboard.nutrition.protein.target),
            carbsPercent: percent(dashboard.nutrition.carb.consumed, dashboard.nutrition.carb.target),
            fatPercent: percent(dashboard.nutrition.fat.consumed, dashboard.nutrition.fat.target)
          },
          meals: mapMealItems(records)
        })
        return
      }

      const local = getMealSummary()
      this.setData({
        summary: {
          date: buildDateText(),
          greeting: buildGreeting(user.name || "用户"),
          kcalText: local.total.toLocaleString(),
          remainText: local.remain,
          intakePercent: local.percent,
          workout: 0,
          protein: { current: 0, target: localTargets.proteinTargetG },
          carbs: { current: 0, target: localTargets.carbTargetG },
          fat: { current: 0, target: localTargets.fatTargetG },
          proteinPercent: "0%",
          carbsPercent: "0%",
          fatPercent: "0%"
        },
        meals: local.items
      })
    }).catch(() => {})
  },

  goFood() {
    wx.redirectTo({ url: "/pages/food/home" })
  },

  goTraining() {
    wx.redirectTo({ url: "/pages/training/home" })
  },

  goMealDetail(event) {
    const item = this.data.meals[event.currentTarget.dataset.index]
    if (!item) return
    if (!item.recorded) {
      wx.redirectTo({ url: "/pages/food/input" })
      return
    }
    wx.navigateTo({ url: `/pages/food/detail?id=${item.recipeId}` })
  },

  onBottomNav(event) {
    wx.redirectTo({ url: event.detail.route })
  }
})
