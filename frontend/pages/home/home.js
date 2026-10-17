const { getMealSummary } = require("../../utils/meal")
const { getTodayDashboard, getMeals, getTodayInsight, quickLog, parseFood, quickLogFull } = require("../../utils/api")
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

function getGreeting() {
  const hour = new Date().getHours()
  if (hour < 6) return "夜深了，注意休息"
  if (hour < 11) return "早上好"
  if (hour < 14) return "中午好"
  if (hour < 18) return "下午好"
  return "晚上好"
}

function buildLocalSummary(targets) {
  return {
    greeting: getGreeting(),
    protein: { current: 0, target: targets.proteinTargetG },
    carbs: { current: 0, target: targets.carbTargetG },
    fat: { current: 0, target: targets.fatTargetG },
    proteinPercent: "0%", carbsPercent: "0%", fatPercent: "0%"
  }
}

Page({
  data: {
    summary: { greeting: "你好", protein: { current: 0, target: 0 }, carbs: { current: 0, target: 0 }, fat: { current: 0, target: 0 }, proteinPercent: "0%", carbsPercent: "0%", fatPercent: "0%" },
    meals: [], remain: 0, targetText: "—", totalText: "0", intakePercent: "0%", ringAngle: 0, dietScore: 0, insightText: "记录一餐后，食练周期会分析这一天的饮食是否适合你的目标。", quickInput: "", quickSaving: false
  },

  onShow() { this.loadMeals() },

  loadMeals() {
    const user = getUser()
    const targets = calculateNutritionTargets(user)
    const localSummary = buildLocalSummary(targets)

    Promise.all([
      getTodayDashboard().catch(() => null),
      getMeals().catch(() => null),
      getTodayInsight().catch(() => null)
    ]).then(([dashboard, records, insight]) => {
      const target = (dashboard && Number(dashboard.daily_calorie_target)) || targets.dailyCalorieTarget
      const intake = (dashboard && Number(dashboard.intake_calories_kcal)) || 0
      const percentNum = target > 0 ? Math.min(100, (intake / target) * 100) : 0
      const proteinCurrent = (dashboard && Number(dashboard.protein_g)) || 0
      const carbsCurrent = (dashboard && Number(dashboard.carbs_g)) || 0
      const fatCurrent = (dashboard && Number(dashboard.fat_g)) || 0

      const summary = {
        ...localSummary,
        protein: { current: proteinCurrent, target: targets.proteinTargetG },
        carbs: { current: carbsCurrent, target: targets.carbTargetG },
        fat: { current: fatCurrent, target: targets.fatTargetG },
        proteinPercent: `${Math.min(100, (proteinCurrent / targets.proteinTargetG) * 100).toFixed(0)}%`,
        carbsPercent: `${Math.min(100, (carbsCurrent / targets.carbTargetG) * 100).toFixed(0)}%`,
        fatPercent: `${Math.min(100, (fatCurrent / targets.fatTargetG) * 100).toFixed(0)}%`
      }

      this.setData({
        summary, remain: Math.max(0, Math.round(target - intake)), targetText: Math.round(target).toLocaleString(),
        totalText: Math.round(intake).toLocaleString(), intakePercent: `${percentNum.toFixed(0)}%`, ringAngle: Math.round(percentNum * 3.6),
        meals: Array.isArray(records) ? mapMealItems(records) : getMealSummary().items, dietScore: Math.round(insight && insight.diet_score || 0), insightText: pickAdvice(insight)
      })
    }).catch((err) => { this.setData({ summary: localSummary }) })
  },

  onQuickInput(event) { this.setData({ quickInput: event.detail.value }) },

  saveQuickLog() {
    const text = String(this.data.quickInput || "").trim()
    if (!text) { wx.showToast({ title: "请先输入饮食", icon: "none" }); return }
    this.setData({ quickSaving: true })
    wx.showLoading({ title: "解析中..." })
    parseFood(text).then((result) => {
      wx.hideLoading()
      const info = result.matched ? `已识别：${result.food_name}\n约 ${result.quantity_g}g\n热量 ${result.kcal} kcal\n蛋白质 ${result.protein_g}g\n碳水 ${result.carbs_g}g\n脂肪 ${result.fat_g}g` : `未精确匹配"${result.food_name}"\n按默认估算：约 ${result.kcal} kcal`
      wx.showModal({ title: "记录饮食", content: info, confirmText: "记录", cancelText: "取消", success: (res) => { if (res.confirm) this.confirmAndSave(text, result) } })
    }).catch((error) => {
      wx.hideLoading()
      wx.showToast({ title: (error && error.message) || "解析失败，请重试", icon: "none" })
    }).finally(() => { this.setData({ quickSaving: false }) })
  },

  confirmAndSave(text, result) {
    wx.showLoading({ title: "保存中..." })
    quickLogFull({ text, meal_type: "早餐", food_name: result.food_name, quantity_g: result.quantity_g, kcal: result.kcal, protein_g: result.protein_g, carbs_g: result.carbs_g, fat_g: result.fat_g })
      .then(() => {
        wx.hideLoading(); wx.showToast({ title: "已记录", icon: "success" }); this.setData({ quickInput: "" }); this.loadMeals()
      }).catch((error) => { wx.hideLoading(); wx.showToast({ title: (error && error.message) || "保存失败", icon: "none" }) })
  },

  goFood() { wx.redirectTo({ url: "/pages/food/home" }) },
  goTraining() { wx.redirectTo({ url: "/pages/training/home" }) },
  
  onBottomNav(e) {
    const route = e.currentTarget.dataset.route;
    if (!route) return;
    wx.redirectTo({ url: route });
  },

  goMealDetail(e) {
    const item = this.data.meals[e.currentTarget.dataset.index]
    if (!item) return
    if (!item.recorded) { wx.navigateTo({ url: `/pages/food/input?mealType=${encodeURIComponent(item.label)}` }); return }
    if (item.recipeId) { wx.navigateTo({ url: `/pages/food/detail?id=${item.recipeId}` }) }
  }
})