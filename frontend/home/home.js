const { getMealSummary } = require("../../utils/meal")
const { getTodayDashboard, getMeals, getTodayInsight, quickLog } = require("../../utils/api")
const { getUser, calculateNutritionTargets } = require("../../utils/user")

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
      return { ...slot, recorded: false, kcal: "尚未记录", detail: "点击添加一餐", recipeId: "" }
    }
    return {
      ...slot,
      recorded: true,
      kcal: record && record.calories_kcal != null ? Math.round(record.calories_kcal) : local.kcal,
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

Page({
  data: {
    summary: { date: "", greeting: "你好", protein: {}, carbs: {}, fat: {} },
    meals: [],
    remain: 0,
    targetText: "—",
    totalText: "0",
    intakePercent: "0%",
    ringAngle: 0,
    dietScore: 0,
    insightText: "记录一餐后，食练周期会分析这一天的饮食是否适合你的目标。",
    quickInput: "",
    quickSaving: false
  },

  onShow() {
    console.log("【home】onShow 触发")
    this.loadMeals()
  },

  loadMeals() {
    // 先按用户资料本地算一遍兜底目标
    const user = getUser()
    const targets = calculateNutritionTargets(user)
    const localSummary = {
      date: new Date().toLocaleDateString("zh-CN", { month: "long", day: "numeric", weekday: "long" }),
      greeting: (() => {
        const h = new Date().getHours()
        if (h < 11) return "早上好"
        if (h < 14) return "中午好"
        if (h < 18) return "下午好"
        return "晚上好"
      })(),
      protein: { current: 0, target: targets.proteinTargetG },
      carbs: { current: 0, target: targets.carbTargetG },
      fat: { current: 0, target: targets.fatTargetG },
      proteinPercent: "0%",
      carbsPercent: "0%",
      fatPercent: "0%"
    }

    Promise.all([
      getTodayDashboard().catch(() => null),
      getMeals().catch(() => null),
      getTodayInsight().catch(() => null)
    ]).then(([dashboard, records, insight]) => {
      console.log("【home】dashboard =", dashboard)
      console.log("【home】records =", records)

      const target = (dashboard && Number(dashboard.daily_calorie_target)) || targets.dailyCalorieTarget
      const intake = (dashboard && Number(dashboard.intake_calories_kcal)) || 0
      const percentNum = target > 0 ? Math.min(100, (intake / target) * 100) : 0

      this.setData({
        summary: localSummary,
        remain: Math.max(0, Math.round(target - intake)),
        targetText: Math.round(target).toLocaleString(),
        totalText: Math.round(intake).toLocaleString(),
        intakePercent: `${percentNum.toFixed(0)}%`,
        ringAngle: Math.round(percentNum * 3.6),
        meals: Array.isArray(records) ? mapMealItems(records) : getMealSummary().items,
        dietScore: Math.round(insight && insight.diet_score || 0),
        insightText: pickAdvice(insight)
      })
    }).catch((err) => {
      console.log("【home】loadMeals 异常 =", err)
      // 兜底：即使接口全挂，也显示本地默认
      this.setData({ summary: localSummary })
    })
  },

  onQuickInput(event) { this.setData({ quickInput: event.detail.value }) },

  saveQuickLog() {
    const text = String(this.data.quickInput || "").trim()
    if (!text) { wx.showToast({ title: "先输入饮食或有氧", icon: "none" }); return }
    this.setData({ quickSaving: true })
    quickLog(text).then(() => {
      wx.showToast({ title: "已记录", icon: "success" })
      this.setData({ quickInput: "" })
      this.loadMeals()
    }).catch((error) => {
      wx.showToast({ title: error.message || "记录失败", icon: "none" })
    }).finally(() => { this.setData({ quickSaving: false }) })
  },

  goFood() { wx.redirectTo({ url: "/pages/food/home" }) },

  goTraining() { wx.redirectTo({ url: "/pages/training/home" }) },

  goMealDetail(e) {
    const item = this.data.meals[e.currentTarget.dataset.index]
    if (!item) return
    if (!item.recorded) {
      wx.navigateTo({ url: `/pages/food/input?mealType=${encodeURIComponent(item.label)}` })
      return
    }
    if (item.recipeId) {
      wx.navigateTo({ url: `/pages/food/detail?id=${item.recipeId}` })
    }
  },

  onBottomNav(event) { wx.redirectTo({ url: event.detail.route }) }
})