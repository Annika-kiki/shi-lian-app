const DEFAULT_USER = {
  name: "用户",
  avatar: "🍃",
  goal: "减脂",
  gender: "女",
  age: "21",
  height: "165",
  weight: "56.5",
  targetWeight: "53.0"
}

function toNumber(value, fallback) {
  const number = Number(value)
  return Number.isFinite(number) && number > 0 ? number : fallback
}

function roundToFive(value) {
  return Math.max(0, Math.round(value / 5) * 5)
}

function calculateNutritionTargets(user = {}) {
  const profile = {
    ...DEFAULT_USER,
    ...user
  }
  const weight = toNumber(profile.weight || profile.current_weight_kg, 56.5)
  const height = toNumber(profile.height || profile.height_cm, 165)
  const age = toNumber(profile.age, 21)
  const goal = profile.goal || profile.goal_type || "保持健康"
  const isMale = profile.gender === "男" || String(profile.gender || "").toLowerCase() === "male"
  const bmr = (10 * weight) + (6.25 * height) - (5 * age) + (isMale ? 5 : -161)
  const activityCalories = Math.max(1200, bmr * 1.35)
  const dailyFactor = goal === "减脂" ? 0.85 : goal === "增肌" ? 1.1 : 1
  const dailyCalorieTarget = roundToFive(Math.min(3500, Math.max(1200, activityCalories * dailyFactor)))
  const proteinFactor = goal === "增肌" ? 1.8 : goal === "减脂" ? 1.6 : 1.2
  const fatFactor = goal === "增肌" ? 0.9 : 0.8
  const proteinTargetG = roundToFive(weight * proteinFactor)
  const fatTargetG = roundToFive(weight * fatFactor)
  const carbTargetG = roundToFive(Math.max(80, (dailyCalorieTarget - (proteinTargetG * 4) - (fatTargetG * 9)) / 4))

  return {
    dailyCalorieTarget,
    proteinTargetG,
    carbTargetG,
    fatTargetG
  }
}

function readStoredUser() {
  try {
    return wx.getStorageSync("userProfile") || wx.getStorageSync("profileForm") || {}
  } catch (error) {
    return {}
  }
}

function normalizeUser(user = {}) {
  return {
    ...DEFAULT_USER,
    ...readStoredUser(),
    ...user
  }
}

function saveUser(user = {}) {
  const next = normalizeUser(user)
  wx.setStorageSync("userProfile", next)
  return next
}

function getUser() {
  return normalizeUser()
}

module.exports = {
  DEFAULT_USER,
  getUser,
  saveUser,
  normalizeUser,
  calculateNutritionTargets
}
