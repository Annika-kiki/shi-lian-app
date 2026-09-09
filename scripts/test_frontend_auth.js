const assert = require("assert")

const storage = new Map([
  ["accessToken", "stale-token"],
  ["privacyAgreedVersion", "2026-09-05"]
])
let loginCalls = 0
let requestCalls = 0
let lastMealRequest = null
let envVersion = "develop"
let cloudInitCalls = 0
let cloudRequest = null

global.wx = {
  getStorageSync(key) { return storage.get(key) || "" },
  setStorageSync(key, value) { storage.set(key, value) },
  removeStorageSync(key) { storage.delete(key) },
  getAccountInfoSync() { return { miniProgram: { envVersion } } },
  login({ success }) {
    loginCalls += 1
    setTimeout(() => success({ code: "temporary-code" }), 0)
  },
  cloud: {
    init() { cloudInitCalls += 1 },
    callContainer(options) {
      cloudRequest = options
      return Promise.resolve({
        statusCode: 200,
        data: { code: 0, data: { access_token: "cloud-token" } }
      })
    }
  },
  request(options) {
    requestCalls += 1
    if (options.url.endsWith("/api/meals") && options.method === "POST") {
      lastMealRequest = options.data
    }
    if (options.url.endsWith("/api/auth/wechat-login")) {
      setTimeout(() => options.success({
        statusCode: 200,
        data: { code: 0, data: { access_token: "fresh-token" } }
      }), 0)
      return
    }
    if (options.header.Authorization === "Bearer stale-token") {
      setTimeout(() => options.success({
        statusCode: 401,
        data: { code: 401, message: "expired" }
      }), 0)
      return
    }
    setTimeout(() => options.success({
      statusCode: 200,
      data: { code: 0, data: { id: 7 } }
    }), 0)
  }
}

const api = require("../frontend/utils/api")

async function run() {
  const me = await api.getMe()
  assert.equal(me.id, 7)
  assert.equal(storage.get("accessToken"), "fresh-token")
  assert.equal(loginCalls, 1, "an expired session should trigger one login")
  assert.equal(requestCalls, 3, "request should login once and retry once")

  storage.delete("accessToken")
  loginCalls = 0
  await Promise.all([api.ensureLogin(), api.ensureLogin(), api.ensureLogin()])
  assert.equal(loginCalls, 1, "concurrent callers should share one login")

  await api.createMealFromRecipe({
    id: "generated-example",
    name: "临时食谱",
    ingredients: [{ id: 3, amount_g: 150, name: "鸡蛋" }]
  }, "午餐")
  assert.equal(lastMealRequest.recipe_id, null, "generated recipes must not require persistent recipe rows")
  assert.deepEqual(lastMealRequest.ingredients, [{ ingredient_id: 3, amount_g: 150 }])

  storage.set("mealRecords", { date: "2026-09-05" })
  storage.set("generatedRecipes", [{ id: 1 }])
  storage.set("lastRecipeRequest", { ingredients: ["鸡蛋"] })
  storage.set("currentWorkoutExercise", { id: 1 })
  storage.set("apiBaseUrl", "http://127.0.0.1:8001")
  await api.deleteAccount()
  for (const key of ["accessToken", "mealRecords", "generatedRecipes", "lastRecipeRequest", "currentWorkoutExercise"]) {
    assert.equal(storage.has(key), false, `${key} should be removed after account deletion`)
  }
  assert.equal(storage.get("apiBaseUrl"), "http://127.0.0.1:8001", "non-personal development settings should be preserved")

  loginCalls = 0
  await assert.rejects(api.ensureLogin(), /请先阅读并同意/)
  assert.equal(loginCalls, 0, "login must not run before current privacy consent")

  storage.set("privacyAgreedVersion", "2026-09-05")
  envVersion = "trial"
  await api.ensureLogin()
  assert.equal(storage.get("accessToken"), "cloud-token")
  assert.equal(loginCalls, 0, "trial builds must use the Cloud Hosting identity instead of wx.login")
  assert.equal(cloudInitCalls, 1)
  assert.equal(cloudRequest.config.env, "prod-d4g1s6f9gaef2c320")
  assert.equal(cloudRequest.header["X-WX-SERVICE"], "flask-3xwi")
  assert.equal(cloudRequest.path, "/api/auth/cloud-login")
  console.log("Frontend auth recovery checks passed.")
}

run().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
