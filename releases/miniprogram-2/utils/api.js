const CLOUD_ENV_ID = "prod-d4gls6f9gaef2c320"
const CLOUD_SERVICE = "flask-3xwi"
const CLOUD_AUTH_TARGET = `${CLOUD_ENV_ID}/${CLOUD_SERVICE}`
const { getUser, calculateNutritionTargets } = require("./user")
let loginPromise = null
let cloudInitPromise = null
// Re-establish the session once per runtime; cached userId alone is never login.
let sessionValidated = false
let privacyConsent = false

function setPrivacyConsent(agreed) {
  privacyConsent = agreed === true
}

function requirePrivacyConsent() {
  return privacyConsent ? null : new Error("请先阅读并同意用户服务协议和隐私政策")
}

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
  const consentError = requirePrivacyConsent()
  if (consentError) return Promise.reject(consentError)
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
  const consentError = requirePrivacyConsent()
  if (consentError) return Promise.reject(consentError)
  // Keep the existing user ID return value for compatibility with your pages.
  // Requests authenticate with the server-issued token, never X-User-Id.
  if (sessionValidated && getAccessToken() && wx.getStorageSync("userId")) {
    return Promise.resolve(wx.getStorageSync("userId"))
  }
  if (loginPromise) return loginPromise
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

function saveProfile(user) {
  const targets = calculateNutritionTargets(user)
  return ensureLogin(user).then(() => request("/api/users/me/profile", {
    method: "PUT",
    data: {
      nickname: String(user.name || "用户").trim() || "用户",
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
  return ensureLogin().then(() => request("/api/meals", {
    method: "POST",
    data: {
      meal_type: mealType,
      name: recipe.name,
      recipe_id: Number(recipe.id)
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
  "杠铃卧推": "/images/exercises/barbell-bench-press.png",
  "哑铃上斜卧推": "/images/exercises/incline-dumbbell-press.png",
  "上斜哑铃卧推": "/images/exercises/incline-dumbbell-press.png",
  "跪姿俯卧撑": "/images/exercises/kneeling-push-up.png",
  "俯卧撑": "/images/exercises/kneeling-push-up.png",
  "绳索夹胸": "/images/exercises/cable-fly.png",
  "高位下拉": "/images/exercises/lat-pulldown.png",
  "坐姿划船": "/images/exercises/seated-cable-row.png",
  "单臂哑铃划船": "/images/exercises/one-arm-dumbbell-row.png",
  "哑铃单臂划船": "/images/exercises/one-arm-dumbbell-row.png",
  "绳索面拉": "/images/exercises/face-pull.png",
  "高脚杯深蹲": "/images/exercises/goblet-squat.png",
  "深蹲": "/images/exercises/goblet-squat.png",
  "罗马尼亚硬拉": "/images/exercises/dumbbell-romanian-deadlift.png",
  "保加利亚分腿蹲": "/images/exercises/bulgarian-split-squat.png",
  "臀桥推髋": "/images/exercises/hip-thrust.png",
  "坐姿哑铃推举": "/images/exercises/seated-dumbbell-press.png",
  "哑铃推举": "/images/exercises/seated-dumbbell-press.png",
  "哑铃侧平举": "/images/exercises/dumbbell-lateral-raise.png",
  "杠铃弯举": "/images/exercises/barbell-curl.png",
  "锤式弯举": "/images/exercises/hammer-curl.png",
  "绳索下压": "/images/exercises/triceps-pushdown.png",
  "坐姿臂屈伸": "/images/exercises/overhead-triceps-extension.png",
  "平板支撑": "/images/exercises/forearm-plank.png",
  "死虫式": "/images/exercises/dead-bug.png",
  "自行车卷腹": "/images/exercises/bicycle-crunch.png"
}

function getExerciseCover(item) {
  if (item.thumbnail_url) {
    const cover = String(item.thumbnail_url)
    if (cover.startsWith("/")) {
      return cover.replace("/assets/exercises/", "/images/exercises/")
    }
    return `/images/exercises/${cover}`
  }
  if (EXERCISE_COVERS[item.name]) return EXERCISE_COVERS[item.name]
  if (item.body_part === "背部") return "/images/exercises/seated-cable-row.png"
  if (item.body_part === "腿部") return "/images/exercises/dumbbell-romanian-deadlift.png"
  if (item.body_part === "肩部") return "/images/exercises/dumbbell-lateral-raise.png"
  if (item.body_part === "核心") return "/images/exercises/dead-bug.png"
  if (item.body_part === "手臂") return "/images/exercises/barbell-curl.png"
  return "/images/exercises/barbell-bench-press.png"
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
    icon: item.equipment === "杠铃" ? "杠" : item.equipment === "哑铃" ? "哑" : "›",
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
      record_date: new Date().toISOString().slice(0, 10)
    }
  }))
}

let foodParseUnavailable = false

function parseFoodFromIngredients(text) {
  const input = String(text || "").trim().replace(/^(早餐|午餐|晚餐|加餐)\s*/, "")
  const match = input.match(/^(?:(\d+(?:\.\d+)?)\s*(?:g|克)\s*(.+)|(.+?)\s*(\d+(?:\.\d+)?)\s*(?:g|克))$/i)
  if (!match) return Promise.reject(new Error("请输入一种食物及克数，如鸡胸肉150g"))
  const name = String(match[2] || match[3]).trim()
  const grams = Number(match[1] || match[4])
  if (!Number.isFinite(grams) || grams <= 0 || grams > 3000) return Promise.reject(new Error("克数须大于0且不超过3000g"))
  return getIngredients(name).then(items => {
    const item = (items || []).find(row => row.name === name || String(row.aliases || "").split(/[,，;；]/).map(s => s.trim()).includes(name))
    if (!item) throw new Error("食材库暂未收录该食物，请换用已收录的食材名称")
    const values = [item.calories_kcal_per_100g, item.protein_g, item.carb_g, item.fat_g]
    if (!Number.isInteger(Number(item.id)) || Number(item.id) <= 0 || values.some(value => value == null || !Number.isFinite(Number(value)) || Number(value) < 0)) throw new Error("该食材营养资料不完整，暂不能记录")
    const scale = value => Math.round(Number(value) * grams / 100 * 10) / 10
    return { matched: true, source: "ingredient_catalog", ingredient_id: Number(item.id), food_name: item.name, quantity_g: grams, kcal: scale(values[0]), protein_g: scale(values[1]), carbs_g: scale(values[2]), fat_g: scale(values[3]) }
  })
}

function parseFood(text) {
  if (foodParseUnavailable) return parseFoodFromIngredients(text)
  return request("/api/food/parse", { method: "POST", data: { text } }).catch(error => {
    if (error.statusCode !== 404) throw error
    foodParseUnavailable = true
    return parseFoodFromIngredients(text)
  })
}

function quickLogFull(data) {
  if (Number.isInteger(data.ingredient_id) && data.ingredient_id > 0) {
    return request("/api/meals", { method: "POST", data: { meal_type: data.meal_type, name: data.food_name, ingredients: [{ ingredient_id: data.ingredient_id, amount_g: data.quantity_g }] } })
  }
  return request("/api/quick-log", { method: "POST", data })
}

module.exports = {
  parseFood,
  quickLogFull,
  setPrivacyConsent,
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
  normalizeRecipe,
  normalizeExercise,
  getExerciseCover
}
