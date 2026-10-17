const { getMealSummary } = require("../../utils/meal")
const { getTodayDashboard, getMeals, getTodayInsight, quickLog, parseFood, quickLogFull } = require("../../utils/api")
const { getUser, calculateNutritionTargets } = require("../../utils/user")

function mapMealItems(records) {
  const localItems = getMealSummary().items
  const mealRecords = Array.isArray(records) ? records : []
  const slots = [
    { key: "breakfast", label: "早餐" },
    { key: "lunch", label: "午餐" },
    { key: "dinner", label: "晚餐" }
  ]
  return slots.map((slot) => {
    const matches = mealRecords.filter((item) => item.meal_type === slot.label || item.meal_type === slot.key)
    const record = matches.length ? { ...matches[0], calories_kcal: matches.reduce((sum, meal) => sum + Number(meal.calories_kcal || 0), 0) } : null
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
    greeting: `${getGreeting()}，${getUser().name || "用户"}`,
    date: `${new Date().getMonth() + 1}月${new Date().getDate()}日`,
    protein: { current: 0, target: targets.proteinTargetG },
    carbs: { current: 0, target: targets.carbTargetG },
    fat: { current: 0, target: targets.fatTargetG },
    proteinPercent: "0%", carbsPercent: "0%", fatPercent: "0%"
  }
}

Page({
  data: {
    summary: { greeting: "你好", protein: { current: 0, target: 0 }, carbs: { current: 0, target: 0 }, fat: { current: 0, target: 0 }, proteinPercent: "0%", carbsPercent: "0%", fatPercent: "0%" },
    meals: [], remain: 0, targetText: "—", totalText: "0", intakePercent: "0%", ringAngle: 0, dietScore: 0, insightText: "记录一餐后，食练周期会分析这一天的饮食是否适合你的目标。", quickInput: "", quickSaving: false, mealTypes: ["早餐", "午餐", "晚餐", "加餐"], mealTypeIndex: new Date().getHours() < 11 ? 0 : new Date().getHours() < 17 ? 1 : 2, loadError: ""
  },

  onShow() { this.loadMeals() },

  loadMeals() {
    const user = getUser()
    const targets = calculateNutritionTargets(user)
    const localSummary = buildLocalSummary(targets)

    return Promise.all([
      getTodayDashboard(),
      getMeals(),
      getTodayInsight()
    ]).then(([dashboard, records, insight]) => {
      const target = (dashboard && Number(dashboard.daily_calorie_target)) || targets.dailyCalorieTarget
      const intake = (dashboard && Number(dashboard.intake_calories_kcal)) || 0
      const percentNum = target > 0 ? Math.min(100, (intake / target) * 100) : 0
      const nutrition = dashboard && dashboard.nutrition || {}
      const proteinCurrent = Number(nutrition.protein && nutrition.protein.consumed) || 0
      const carbsCurrent = Number(nutrition.carb && nutrition.carb.consumed) || 0
      const fatCurrent = Number(nutrition.fat && nutrition.fat.consumed) || 0
      const proteinTarget = Number(nutrition.protein && nutrition.protein.target) || targets.proteinTargetG
      const carbsTarget = Number(nutrition.carb && nutrition.carb.target) || targets.carbTargetG
      const fatTarget = Number(nutrition.fat && nutrition.fat.target) || targets.fatTargetG

      const summary = {
        ...localSummary,
        protein: { current: proteinCurrent, target: proteinTarget },
        carbs: { current: carbsCurrent, target: carbsTarget },
        fat: { current: fatCurrent, target: fatTarget },
        proteinPercent: `${Math.min(100, (proteinCurrent / Math.max(1, proteinTarget)) * 100).toFixed(0)}%`,
        carbsPercent: `${Math.min(100, (carbsCurrent / Math.max(1, carbsTarget)) * 100).toFixed(0)}%`,
        fatPercent: `${Math.min(100, (fatCurrent / Math.max(1, fatTarget)) * 100).toFixed(0)}%`
      }

      this.setData({
        loadError: "", summary, remain: Math.max(0, Math.round(target - intake)), targetText: Math.round(target).toLocaleString(),
        totalText: Math.round(intake).toLocaleString(), intakePercent: `${percentNum.toFixed(0)}%`, ringAngle: Math.round(percentNum * 3.6),
        meals: Array.isArray(records) ? mapMealItems(records) : getMealSummary().items, dietScore: Math.round(insight && insight.diet_score || 0), insightText: pickAdvice(insight)
      })
    }).catch((err) => {
      this.setData({ summary: localSummary, loadError: err.message || "云端记录加载失败，请重试" })
    })
  },

  onQuickInput(event) { this.setData({ quickInput: event.detail.value }) },

  onMealTypeChange(event) {
    this.setData({ mealTypeIndex: Number(event.detail.value) })
  },

  saveQuickLog() {
    if (this.data.quickSaving) return
    const text = String(this.data.quickInput || "").trim()
    if (!text) { wx.showToast({ title: "请先输入饮食或运动", icon: "none" }); return }
    this.setData({ quickSaving: true })
    if (/分钟|跑步|游泳|蛙泳|骑行|跳绳|快走/.test(text)) {
      return quickLog(text).then(() => this.afterQuickSave()).catch(error => {
        wx.showToast({ title: error.message || "记录失败，请重试", icon: "none" })
      }).finally(() => this.setData({ quickSaving: false }))
    }
    wx.showLoading({ title: "解析中" })
    return parseFood(text).then(result => {
      wx.hideLoading()
      return new Promise((resolve, reject) => wx.showModal({
        title: result.source === "ingredient_catalog" ? "按食材库估算，请确认" : result.matched ? "确认饮食记录" : "请核对估算结果",
        content: `${result.food_name}，约 ${result.quantity_g}g\n热量 ${result.kcal} kcal\n蛋白质 ${result.protein_g}g，碳水 ${result.carbs_g}g，脂肪 ${result.fat_g}g`,
        confirmText: "记录", cancelText: "取消",
        success: res => resolve(res.confirm), fail: reject
      })).then(confirmed => confirmed ? this.confirmAndSave(text, result) : undefined)
    }).catch(error => {
      wx.showToast({ title: error.message || "解析失败，请重试", icon: "none" })
    }).finally(() => { wx.hideLoading(); this.setData({ quickSaving: false }) })
  },

  confirmAndSave(text, result) {
    wx.showLoading({ title: "保存中" })
    return quickLogFull({ text, meal_type: this.data.mealTypes[this.data.mealTypeIndex], food_name: result.food_name, ingredient_id: result.ingredient_id, quantity_g: result.quantity_g, kcal: result.kcal, protein_g: result.protein_g, carbs_g: result.carbs_g, fat_g: result.fat_g })
      .then(() => this.afterQuickSave())
  },

  afterQuickSave() {
    wx.showToast({ title: "已记录", icon: "success" })
    this.setData({ quickInput: "" })
    this.loadMeals()
  },

  goFood() { wx.redirectTo({ url: "/pages/food/home" }) },
  goTraining() { wx.redirectTo({ url: "/pages/training/home" }) },

  onBottomNav(e) {
    const route = e.detail.route;
    if (!route) return;
    wx.redirectTo({ url: route });
  },

  goMealDetail(e) {
    const item = this.data.meals[e.currentTarget.dataset.index]
    if (!item) return
    if (!item.recorded) { wx.navigateTo({ url: `/pages/food/input?mealType=${encodeURIComponent(item.label)}` }); return }
    if (item.recipe) wx.setStorageSync("selectedRecipe", item.recipe)
    if (item.recipeId) { wx.navigateTo({ url: `/pages/food/detail?id=${item.recipeId}` }) }
  }
})
