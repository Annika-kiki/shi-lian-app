const { getUser, calculateNutritionTargets } = require("./user")
const { getEnvVersion, getTransportConfig } = require("../config/env")
let loginPromise = null
let cloudInitPromise = null
const PRIVACY_AGREEMENT_VERSION = "2026-09-05"

function request(path, options = {}) {
  const accessToken = wx.getStorageSync("accessToken")
  if (!accessToken && !path.startsWith("/api/auth/") && path !== "/health") {
    return ensureLogin(getUser()).then(() => request(path, options))
  }
  const headers = {
    "content-type": "application/json",
    ...(options.header || {})
  }

  if (accessToken) headers.Authorization = `Bearer ${accessToken}`

  return new Promise((resolve, reject) => {
    let transport
    try { transport = getTransportConfig() } catch (error) { reject(error); return }
    const handleSuccess = (res) => {
      const body = res.data || {}
      if (res.statusCode >= 200 && res.statusCode < 300 && body.code === 0) {
        resolve(body.data)
        return
      }
      const error = new Error(body.message || `请求失败 ${res.statusCode}`)
      error.statusCode = res.statusCode
      reject(error)
    }
    if (transport.type === "cloud") {
      if (!wx.cloud || typeof wx.cloud.callContainer !== "function") {
        reject(new Error("当前微信版本不支持云托管调用，请升级微信后重试"))
        return
      }
      if (!cloudInitPromise) {
        try { cloudInitPromise = Promise.resolve(wx.cloud.init({ traceUser: false })) }
        catch (error) { cloudInitPromise = Promise.reject(error) }
      }
      cloudInitPromise.then(() => wx.cloud.callContainer({
        config: { env: transport.env }, path,
        header: { ...headers, "X-WX-SERVICE": transport.service },
        method: options.method || "GET", data: options.data || {}
      })).then(handleSuccess, reject)
      return
    }
    wx.request({
      url: `${transport.base}${path}`,
      method: options.method || "GET",
      data: options.data || {},
      header: headers,
      success: handleSuccess,
      fail: reject
    })
  }).catch((error) => {
    const canRetry = error.statusCode === 401 && options.authRetry !== false && !path.startsWith("/api/auth/")
    if (!canRetry) throw error
    wx.removeStorageSync("accessToken")
    return ensureLogin(getUser()).then(() => request(path, { ...options, authRetry: false }))
  })
}

function ensureLogin(user = {}) {
  const cachedToken = wx.getStorageSync("accessToken")
  if (cachedToken) return Promise.resolve(cachedToken)
  if (loginPromise) return loginPromise
  if (wx.getStorageSync("privacyAgreedVersion") !== PRIVACY_AGREEMENT_VERSION) {
    return Promise.reject(new Error("请先阅读并同意用户协议和隐私政策"))
  }
  wx.removeStorageSync("userId")

  const nickname = user.name || user.nickName || "练食记用户"
  const loginWithWechat = () => new Promise((resolve, reject) => wx.login({
    success: (result) => result.code ? resolve(result.code) : reject(new Error("微信登录未返回有效凭证")),
    fail: reject
  })).then((code) => request("/api/auth/wechat-login", { method: "POST", data: { code } }))
  const loginForDevelopment = () => request("/api/auth/mock-login", {
    method: "POST",
    data: { nickname, avatar: user.avatar || user.avatarUrl || "", mock_openid: `mock_${nickname}` }
  })
  const loginRequest = getEnvVersion() === "develop"
    ? loginWithWechat().catch((error) => error.statusCode === 501 ? loginForDevelopment() : Promise.reject(error))
    : request("/api/auth/cloud-login", { method: "POST" })
  loginPromise = loginRequest.then((data) => {
    wx.setStorageSync("accessToken", data.access_token)
    return data.access_token
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
