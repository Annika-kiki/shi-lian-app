const MEAL_SLOTS = [
  { key: "breakfast", label: "早餐", icon: "🥣" },
  { key: "lunch", label: "午餐", icon: "🍱" },
  { key: "dinner", label: "晚餐", icon: "🌙" }
]

const DAILY_TARGET = 1800

function readMealRecords() {
  try {
    return wx.getStorageSync("mealRecords") || {}
  } catch (error) {
    return {}
  }
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
  const remain = Math.max(0, DAILY_TARGET - total)
  return {
    items,
    total,
    remain,
    percent: `${Math.min(100, (total / DAILY_TARGET) * 100)}%`
  }
}

function saveMeal(recipe, preferredSlot) {
  const records = readMealRecords()
  const nextSlot =
    preferredSlot ||
    MEAL_SLOTS.find((slot) => !records[slot.key])?.key ||
    MEAL_SLOTS[0].key

  records[nextSlot] = {
    recipeId: recipe.id,
    label: recipe.name,
    kcal: recipe.kcal,
    detail: formatIngredientPreview(recipe) || "已记录"
  }

  wx.setStorageSync("mealRecords", records)
  return getMealSummary()
}

module.exports = {
  DAILY_TARGET,
  MEAL_SLOTS,
  getMealSummary,
  saveMeal
}
