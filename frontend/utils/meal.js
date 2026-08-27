const MEAL_SLOTS = [
  { key: "breakfast", label: "早餐", icon: "🥣" },
  { key: "lunch", label: "午餐", icon: "🍱" },
  { key: "dinner", label: "晚餐", icon: "🌙" }
]

const { getUser, calculateNutritionTargets } = require("./user")

const DAILY_TARGET = 1800
const STORAGE_KEY = "mealRecords"

function getTodayKey() {
  const now = new Date()
  const year = now.getFullYear()
  const month = `${now.getMonth() + 1}`.padStart(2, "0")
  const day = `${now.getDate()}`.padStart(2, "0")
  return `${year}-${month}-${day}`
}

function readMealRecords() {
  try {
    const stored = wx.getStorageSync(STORAGE_KEY) || {}
    const today = getTodayKey()

    if (stored.date === today && stored.records) {
      return stored.records
    }

    if (stored.date !== today) {
      wx.setStorageSync(STORAGE_KEY, {
        date: today,
        records: {}
      })
    }

    return {}
  } catch (error) {
    return {}
  }
}

function writeMealRecords(records) {
  wx.setStorageSync(STORAGE_KEY, {
    date: getTodayKey(),
    records
  })
}

function formatIngredientPreview(recipe) {
  if (!recipe || !recipe.ingredients) return ""
  return recipe.ingredients.slice(0, 3).map((item) => item.name).join(" · ")
}

function buildMealItems() {
  const records = readMealRecords()
  return MEAL_SLOTS.map((slot) => {
    const record = records[slot.key]
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
      kcal: record.kcal,
      detail: record.detail,
      recipeId: record.recipeId
    }
  })
}

function getMealSummary() {
  const items = buildMealItems()
  const total = items.reduce((sum, item) => sum + (item.recorded ? Number(item.kcal) || 0 : 0), 0)
  const dailyTarget = calculateNutritionTargets(getUser()).dailyCalorieTarget || DAILY_TARGET
  const remain = Math.max(0, dailyTarget - total)
  return {
    items,
    total,
    remain,
    dailyTarget,
    percent: `${Math.min(100, (total / dailyTarget) * 100)}%`
  }
}

function saveMeal(recipe, preferredSlot) {
  const records = readMealRecords()
  const emptySlot = MEAL_SLOTS.find((slot) => !records[slot.key])
  const nextSlot = preferredSlot || (emptySlot && emptySlot.key) || MEAL_SLOTS[0].key

  records[nextSlot] = {
    recipeId: recipe.id,
    label: recipe.name,
    kcal: recipe.kcal,
    detail: formatIngredientPreview(recipe) || "已记录"
  }

  writeMealRecords(records)
  return getMealSummary()
}

module.exports = {
  DAILY_TARGET,
  MEAL_SLOTS,
  getMealSummary,
  saveMeal,
  getTodayKey
}
