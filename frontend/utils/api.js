const CLOUD_ENV_ID = "prod-d4gls6f9gaef2c320"
const CLOUD_SERVICE = "flask-3xwi"
const CLOUD_AUTH_TARGET = `${CLOUD_ENV_ID}/${CLOUD_SERVICE}`
const { getUser, calculateNutritionTargets } = require("./user")
let loginPromise = null
let cloudInitPromise = null
// Re-establish the session once per runtime; cached userId alone is never login.
let sessionValidated = false
const PRIVACY_AGREEMENT_VERSION = "2026-09-05"

function getAccessToken() {
  return wx.getStorageSync("cloudAuthTarget") === CLOUD_AUTH_TARGET
    ? wx.getStorageSync("accessToken") || ""
    : ""
}

function initCloud() {
  if (!wx.cloud || typeof wx.cloud.callContainer !== "function") {
    return Promise.reject(new Error("当前基础库不支持云托管，请更新微信开发者工具或微信版本"))
  }
  if (!cloudInitPromise) {
    cloudInitPromise = Promise.resolve().then(() => wx.cloud.init({ env: CLOUD_ENV_ID, traceUser: false })).catch((error) => {
      cloudInitPromise = null
      throw error
    })
  }
  return cloudInitPromise
}

function request(path, options = {}) {
  const accessToken = getAccessToken()
  if ((!accessToken || !sessionValidated) && !path.startsWith("/api/auth/") && path !== "/health") {
    return ensureLogin(getUser()).then(() => request(path, options))
  }
  const headers = {
    "content-type": "application/json",
    ...(options.header || {}),
    "X-WX-SERVICE": CLOUD_SERVICE
  }
  Object.keys(headers).forEach((key) => {
    if (["authorization", "x-user-id"].includes(key.toLowerCase())) delete headers[key]
  })
  if (accessToken && !path.startsWith("/api/auth/")) headers.Authorization = `Bearer ${accessToken}`

  return initCloud().then(() => wx.cloud.callContainer({
    config: { env: CLOUD_ENV_ID },
    path,
    method: options.method || "GET",
    data: options.data || {},
    header: headers
  })).then((res) => {
    const body = res.data || {}
    if (res.statusCode >= 200 && res.statusCode < 300 && body.code === 0) {
      return body.data
    }
    const error = new Error(body.message || `请求失败 ${res.statusCode}`)
    error.statusCode = res.statusCode
    throw error
  }).catch((error) => {
    if (error.statusCode !== 401 || path.startsWith("/api/auth/") || path === "/health") throw error
    if (getAccessToken() === accessToken) {
      sessionValidated = false
      wx.removeStorageSync("accessToken")
    }
    if (options.authRetry === false) throw error
    return ensureLogin(getUser()).then(() => request(path, { ...options, authRetry: false }))
  })
}

function ensureLogin(user = {}) {
  // Keep the existing user ID return value for compatibility with your pages.
  // Requests authenticate with the server-issued token, never X-User-Id.
  if (sessionValidated && getAccessToken() && wx.getStorageSync("userId")) {
    return Promise.resolve(wx.getStorageSync("userId"))
  }
  if (loginPromise) return loginPromise
  if (wx.getStorageSync("privacyAgreedVersion") !== PRIVACY_AGREEMENT_VERSION) {
    return Promise.reject(new Error("请先阅读并同意用户协议和隐私政策"))
  }
  loginPromise = request("/api/auth/cloud-login", {
    method: "POST",
    data: {}
  }).then((data) => {
    if (!data || !data.access_token || !data.user_id) throw new Error("云托管登录未返回有效会话")
    wx.setStorageSync("accessToken", data.access_token)
    wx.setStorageSync("userId", data.user_id)
    wx.setStorageSync("cloudAuthTarget", CLOUD_AUTH_TARGET)
    sessionValidated = true
    return data.user_id
  }).finally(() => { loginPromise = null })
  return loginPromise
}

function toNumber(value, fallback = 0) {
  const number = Number(value)
  return Number.isFinite(number) ? number : fallback
}

function ingredientAmount(item) {
  if (item.amount_g || item.grams) return Number(item.amount_g || item.grams)
  const match = String(item.amount || "").match(/[\d.]+/)
  return Number(match ? match[0] : 0)
}

function localDateString(now = new Date()) {
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, "0")
  const day = String(now.getDate()).padStart(2, "0")
  return `${year}-${month}-${day}`
}

function saveProfile(user) {
  const targets = calculateNutritionTargets(user)
  return ensureLogin(user).then(() => request("/api/users/me/profile", {
    method: "PUT",
    data: {
      nickname: String(user.name || "").trim() || "食练周期用户",
      gender: user.gender,
      age: toNumber(user.age, 21),
      height_cm: toNumber(user.height, 165),
      current_weight_kg: toNumber(user.weight, 56.5),
      target_weight_kg: toNumber(user.targetWeight, 53),
      goal_type: user.goal || "保持健康",
      daily_calorie_target: targets.dailyCalorieTarget,
      protein_target_g: targets.proteinTargetG,
      carb_target_g: targets.carbTargetG,
      fat_target_g: targets.fatTargetG
    }
  }))
}

function getMe() {
  return request("/api/users/me")
}

function getTodayDashboard() {
  return request("/api/dashboard/today")
}

function getTodayInsight() {
  return request("/api/insights/today")
}

function getMeals(date) {
  const query = date ? `?date=${date}` : ""
  return request(`/api/meals${query}`)
}

function createMealFromRecipe(recipe, mealType = "午餐") {
  const recipeId = Number(recipe.id)
  const isPersistedRecipe = Number.isInteger(recipeId) && recipeId > 0
  const ingredients = (recipe.ingredients || []).map((item) => ({
    ingredient_id: Number(item.id),
    amount_g: ingredientAmount(item)
  })).filter((item) => item.ingredient_id > 0 && item.amount_g > 0)
  return ensureLogin().then(() => request("/api/meals", {
    method: "POST",
    data: {
      meal_type: mealType,
      name: recipe.name,
      recipe_id: isPersistedRecipe ? recipeId : null,
      ingredients: isPersistedRecipe ? [] : ingredients
    }
  }))
}

function getIngredients(keyword = "") {
  const q = keyword ? `?q=${encodeURIComponent(keyword)}` : ""
  return request(`/api/ingredients${q}`)
}

function generateRecipes(ingredients, targetCalories, preferences = [], recipeRound = 0) {
  return request("/api/recipes/generate", {
    method: "POST",
    data: {
      ingredients,
      meal_type: "午餐",
      target_calories: targetCalories,
      preference: preferences.join(","),
      recipe_round: recipeRound
    }
  }).then((items) => items.map(normalizeRecipe))
}

function getRecipe(id) {
  return request(`/api/recipes/${id}`).then(normalizeRecipe)
}

function normalizeRecipe(recipe) {
  const nutrition = recipe.nutrition || {}
  const ingredients = (recipe.ingredients || []).map((item) => ({
    name: item.name,
    amount: item.amount || `${item.amount_g || item.grams || 0} g`
  }))

  return {
    id: String(recipe.id),
    name: recipe.name,
    minutes: recipe.minutes || recipe.estimated_minutes || 15,
    kcal: Math.round(nutrition.calories_kcal || nutrition.kcal || recipe.kcal || 0),
    protein: Math.round(nutrition.protein_g || nutrition.protein || recipe.protein || 0),
    fat: Math.round(nutrition.fat_g || nutrition.fat || recipe.fat || 0),
    tags: recipe.tags || recipe.preferences || [],
    ingredients,
    steps: recipe.steps || [],
    description: recipe.description || ""
  }
}

const BODY_PART_MAP = {
  chest: "胸部",
  back: "背部",
  shoulder: "肩部",
  arm: "手臂",
  leg: "腿部",
  core: "核心"
}

const EXERCISE_COVERS = {
  "杠铃卧推": "/assets/exercises/barbell-bench-press.jpg",
  "哑铃上斜卧推": "/assets/exercises/incline-dumbbell-press.jpg",
  "上斜哑铃卧推": "/assets/exercises/incline-dumbbell-press.jpg",
  "高位下拉": "/assets/exercises/lat-pulldown.jpg",
  "坐姿划船": "/assets/exercises/seated-cable-row.jpg",
  "高脚杯深蹲": "/assets/exercises/goblet-squat.jpg",
  "罗马尼亚硬拉": "/assets/exercises/dumbbell-romanian-deadlift.jpg",
  "哑铃侧平举": "/assets/exercises/dumbbell-lateral-raise.jpg",
  "平板支撑": "/assets/exercises/forearm-plank.jpg",
  "死虫式": "/assets/exercises/dead-bug.jpg"
}

const EXERCISE_FALLBACK_COVERS = {
  "背部": "/assets/exercises/seated-cable-row.jpg",
  "腿部": "/assets/exercises/dumbbell-romanian-deadlift.jpg",
  "肩部": "/assets/exercises/dumbbell-lateral-raise.jpg",
  "核心": "/assets/exercises/dead-bug.jpg",
  "手臂": "/assets/exercises/barbell-bench-press.jpg",
  "胸部": "/assets/exercises/barbell-bench-press.jpg"
}

function getExerciseCover(item) {
  if (EXERCISE_COVERS[item.name]) return EXERCISE_COVERS[item.name]
  return EXERCISE_FALLBACK_COVERS[item.body_part] || EXERCISE_FALLBACK_COVERS["胸部"]
}

function getExercises(part = "chest") {
  const bodyPart = BODY_PART_MAP[part] || ""
  const query = bodyPart ? `?body_part=${encodeURIComponent(bodyPart)}` : ""
  return request(`/api/exercises${query}`).then((items) => items.map(normalizeExercise))
}

function getExercise(id) {
  return request(`/api/exercises/${id}`).then(normalizeExercise)
}

function getWorkoutRecommendation(level = "新手") {
  return request(`/api/workouts/recommendation?level=${encodeURIComponent(level)}`)
}

function getWorkoutSessions(date) {
  const query = date ? `?date=${date}` : ""
  return request(`/api/workouts/sessions${query}`)
}

function createWorkoutSession(data) {
  return ensureLogin().then(() => request("/api/workouts/sessions", {
    method: "POST",
    data
  }))
}

function getWorkoutSession(sessionId) {
  return request(`/api/workouts/sessions/${sessionId}`)
}

function addWorkoutSet(sessionId, data) {
  return ensureLogin().then(() => request(`/api/workouts/sessions/${sessionId}/sets`, {
    method: "POST",
    data
  }))
}

function updateWorkoutSet(setId, data) {
  return ensureLogin().then(() => request(`/api/workouts/sets/${setId}`, {
    method: "PUT",
    data
  }))
}

function completeWorkoutSession(sessionId) {
  return ensureLogin().then(() => request(`/api/workouts/sessions/${sessionId}/complete`, {
    method: "POST"
  }))
}

function createCardioSession(data) {
  return ensureLogin().then(() => request("/api/workouts/cardio", {
    method: "POST",
    data
  }))
}

function quickLog(text) {
  return ensureLogin().then(() => request("/api/quick-log", {
    method: "POST",
    data: { text }
  }))
}

function normalizeExercise(item) {
  const steps = Array.isArray(item.steps)
    ? item.steps
    : String(item.steps || "").split(/[。；;]/).filter(Boolean)
  const cautions = Array.isArray(item.cautions)
    ? item.cautions.join("；")
    : item.cautions || "保持动作稳定，身体不适请停止训练。"

  return {
    id: String(item.id),
    title: item.name,
    muscle: item.primary_muscle || item.body_part,
    equipment: item.equipment || "徒手",
    level: item.difficulty || "新手",
    part: item.body_part,
    icon: item.equipment === "杠铃" ? "🏋️" : item.equipment === "哑铃" ? "💪" : "›",
    coverSrc: getExerciseCover(item),
    detail: {
      part: `${item.body_part || "训练"} · ${item.equipment || "徒手"}`,
      main: item.primary_muscle || item.body_part,
      assist: item.secondary_muscle || "核心稳定",
      steps,
      notes: cautions,
      coverSrc: getExerciseCover(item)
    }
  }
}

function getCalendar(year, month) {
  return request(`/api/stats/calendar?year=${year}&month=${month}`)
}

function getBodyTrend(days = 30) {
  return request(`/api/stats/body-trend?days=${days}`)
}

function getReportSummary(days = 7) {
  return request(`/api/reports/summary?days=${days}`)
}

function recordWeight(weight) {
  return ensureLogin().then(() => request("/api/users/me/weights", {
    method: "POST",
    data: {
      weight_kg: toNumber(weight),
      record_date: localDateString()
    }
  }))
}

function deleteAccount() {
  return ensureLogin().then(() => request("/api/users/me", {
    method: "DELETE",
    data: { confirmation: "DELETE" }
  })).then((result) => {
    const personalKeys = [
      "accessToken", "userId", "apiUserId", "apiMockOpenid", "userProfile", "profileForm",
      "mealRecords", "generatedRecipes", "generatedRecipesRequestKey", "lastRecipeRequest",
      "currentWorkoutExercise", "privacyAgreedVersion"
    ]
    personalKeys.forEach((key) => wx.removeStorageSync(key))
    return result
  })
}

module.exports = {
  PRIVACY_AGREEMENT_VERSION,
  ensureLogin,
  saveProfile,
  getMe,
  getTodayDashboard,
  getTodayInsight,
  getMeals,
  createMealFromRecipe,
  getIngredients,
  generateRecipes,
  getRecipe,
  getExercises,
  getExercise,
  getWorkoutRecommendation,
  getWorkoutSessions,
  createWorkoutSession,
  getWorkoutSession,
  addWorkoutSet,
  updateWorkoutSet,
  completeWorkoutSession,
  createCardioSession,
  quickLog,
  getCalendar,
  getBodyTrend,
  getReportSummary,
  recordWeight,
  deleteAccount,
  normalizeRecipe,
  normalizeExercise,
  getExerciseCover
}
