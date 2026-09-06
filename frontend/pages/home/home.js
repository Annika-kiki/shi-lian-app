const { getUser, calculateNutritionTargets } = require("../../utils/user")
const { getMealSummary } = require("../../utils/meal")
const { getTodayDashboard, getMeals, getTodayInsight, quickLog } = require("../../utils/api")

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
const fallbackInsight = {
  score: 0,
  dietScore: 0,
  workoutScore: 0,
  advice: ["记录一餐或一次训练后，食练周期会给出今日评分和建议。"],
  dimensions: [
    { label: "热量", score: 0, width: "0%" },
    { label: "蛋白质", score: 0, width: "0%" },
    { label: "均衡", score: 0, width: "0%" },
    { label: "训练", score: 0, width: "0%" }
  ]
}

function normalizeInsight(insight) {
  if (!insight) return fallbackInsight
  return {
    score: Math.round(insight.score || 0),
    dietScore: Math.round(insight.diet_score || 0),
    workoutScore: Math.round(insight.workout_score || 0),
    advice: insight.advice && insight.advice.length ? insight.advice : fallbackInsight.advice,
    dimensions: (insight.dimensions || []).map((item) => ({
      label: item.label,
      score: Math.round(item.score || 0),
      width: `${Math.min(100, Math.max(0, item.score || 0))}%`
    }))
  }
}

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
    meals: [],
    insight: fallbackInsight,
    quickInput: "",
    quickSaving: false
  },

  onShow() {
    this.loadDashboard()
  },

  loadDashboard() {
    const user = getUser()
    const localTargets = calculateNutritionTargets(user)
    Promise.all([
      getTodayDashboard().catch(() => null),
      getMeals().catch(() => []),
      getTodayInsight().catch(() => null)
    ]).then(([dashboard, records, insight]) => {
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
          meals: mapMealItems(records),
          insight: normalizeInsight(insight)
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
        meals: local.items,
        insight: normalizeInsight(insight)
      })
    }).catch(() => {})
  },

  onQuickInput(event) {
    this.setData({ quickInput: event.detail.value })
  },

  saveQuickLog() {
    const text = String(this.data.quickInput || "").trim()
    if (!text) {
      wx.showToast({ title: "先输入一餐或运动", icon: "none" })
      return
    }
    this.setData({ quickSaving: true })
    quickLog(text).then(() => {
      wx.showToast({ title: "已记录", icon: "success" })
      this.setData({ quickInput: "" })
      this.loadDashboard()
    }).catch((error) => {
      wx.showToast({ title: error.message || "记录失败", icon: "none" })
    }).finally(() => {
      this.setData({ quickSaving: false })
    })
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
