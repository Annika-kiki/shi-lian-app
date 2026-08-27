const { generateRecipes } = require("../../utils/api")
function navigateBackOrRedirect(fallbackUrl) {
  const pages = getCurrentPages()
  if (pages.length > 1) {
    wx.navigateBack({ delta: 1 })
    return
  }
  if (fallbackUrl) {
    wx.redirectTo({ url: fallbackUrl })
  }
}


function toIngredientObject(item) {
  if (!item) return null
  if (typeof item === "string") {
    return { name: item.trim(), amount: "适量" }
  }
  const name = String(item.name || "").trim()
  if (!name) return null
  const amountValue = item.amount || item.amount_g || item.grams
  return {
    name,
    amount: amountValue ? `${amountValue} g` : "适量"
  }
}

function enrichRecipe(recipe) {
  const ingredients = (recipe.ingredients || [])
    .map(toIngredientObject)
    .filter(Boolean)
  const ingredientSummary = ingredients
    .slice(0, 3)
    .map((item) => `${item.name} ${item.amount}`)
    .join(" · ")

  return {
    ...recipe,
    ingredients,
    ingredientSummary
  }
}

function pickThree(list) {
  const items = list.filter(Boolean)
  if (!items.length) return ["鸡胸肉", "鸡蛋", "西兰花"]
  if (items.length === 1) return [items[0], items[0], "西兰花"]
  if (items.length === 2) return [items[0], items[1], items[0]]
  return items.slice(0, 3)
}

function uniqueNames(source) {
  const names = []
  source.forEach((item) => {
    const name = String(typeof item === "string" ? item : item && item.name || "").trim()
    if (name && !names.includes(name)) {
      names.push(name)
    }
  })
  return names
}

function rotateNames(names, offset) {
  if (!names.length) return names
  const start = offset % names.length
  return names.slice(start).concat(names.slice(0, start))
}

function buildTemplates(main, side, veg, target) {
  return [
    {
      key: "steam",
      title: () => `${main}${veg}清蒸碗`,
      minutes: 18,
      kcal: Math.max(360, target - 30),
      protein: 38,
      fat: 12,
      tags: ["清爽", "高蛋白"],
      ingredients: () => [
        { name: main, amount: "150 g" },
        { name: side, amount: "120 g" },
        { name: veg, amount: "180 g" }
      ],
      steps: () => [
        `把${main}和${veg}分层摆好。`,
        "上锅蒸至熟透，尽量保留原味。",
        "出锅后淋少量酱汁即可。"
      ]
    },
    {
      key: "soup",
      title: () => `${main}${veg}汤锅`,
      minutes: 22,
      kcal: Math.max(380, target - 10),
      protein: 34,
      fat: 10,
      tags: ["暖胃", "少油"],
      ingredients: () => [
        { name: main, amount: "130 g" },
        { name: side, amount: "100 g" },
        { name: veg, amount: "200 g" }
      ],
      steps: () => [
        `先把${main}和${veg}切好。`,
        "加水慢煮，先出鲜味再下配菜。",
        `最后放入${side}，调味后出锅。`
      ]
    },
    {
      key: "roast",
      title: () => `${main}${veg}烤盘`,
      minutes: 25,
      kcal: Math.max(400, target),
      protein: 36,
      fat: 14,
      tags: ["低脂", "烤箱"],
      ingredients: () => [
        { name: main, amount: "140 g" },
        { name: side, amount: "100 g" },
        { name: veg, amount: "180 g" }
      ],
      steps: () => [
        `把${main}和${veg}铺在烤盘里。`,
        "撒盐、黑胡椒和少量油。",
        "烤到表面微焦后直接出炉。"
      ]
    },
    {
      key: "bowl",
      title: () => `${main}${side}能量碗`,
      minutes: 15,
      kcal: Math.max(350, target - 50),
      protein: 32,
      fat: 11,
      tags: ["快手", "均衡"],
      ingredients: () => [
        { name: main, amount: "150 g" },
        { name: side, amount: "120 g" },
        { name: veg, amount: "120 g" }
      ],
      steps: () => [
        `先把${side}煮熟，${main}煎熟后切块。`,
        `把${veg}焯水或直接切配。`,
        "最后装碗，淋酱汁拌匀。"
      ]
    }
  ]
}

function readCachedRecipes() {
  const cached = wx.getStorageSync("generatedRecipes")
  return Array.isArray(cached) ? cached : []
}

function getRequestKey(request) {
  const ingredients = Array.isArray(request && request.ingredients) ? request.ingredients : []
  const preferences = Array.isArray(request && request.preferences) ? request.preferences : []
  return [
    ingredients.join("|"),
    Number(request && request.targetCalories) || 500,
    preferences.join("|"),
    Number(request && request.recipeRound) || 0
  ].join("::")
}

function buildSummaryText(request) {
  const target = Number(request && request.targetCalories) || 500
  const preferences = Array.isArray(request && request.preferences)
    ? request.preferences.filter(Boolean)
    : []
  const caloriesLabel = String(request && (request.calories || "")).trim() || `\u7ea6${target} kcal`
  const parts = [caloriesLabel]
  if (preferences.length) {
    parts.push(...preferences)
  }
  return parts.join(" \u00b7 ")
}

const LOCAL_STYLES = [
  {
    suffix: "清蒸盘",
    minutes: 20,
    tags: ["清爽", "蒸制", "少油"],
    steps: (names) => [
      `把${names.join("、")}处理成容易熟的大小。`,
      "上锅蒸到熟透，出锅后用盐、生抽或黑胡椒简单调味。",
      "只使用盐、味精、蚝油、油、黑胡椒、生抽、醋、蒜末、辣椒粉这些基础调料。"
    ]
  },
  {
    suffix: "暖汤",
    minutes: 22,
    tags: ["暖胃", "轻负担"],
    steps: (names) => [
      `先把${names[0]}和${names[1] || names[0]}加水煮出味道。`,
      `再放入${names[2] || names[1] || names[0]}小火煮熟。`,
      "最后用盐、生抽或蒜末调味即可。"
    ]
  },
  {
    suffix: "拌碗",
    minutes: 12,
    tags: ["快手", "均衡"],
    steps: (names) => [
      `把${names.join("、")}分别做熟或焯水。`,
      "全部装入碗中，用生抽、醋、黑胡椒拌匀。",
      "口味重时加一点蒜末或辣椒粉。"
    ]
  },
  {
    suffix: "香煎拼盘",
    minutes: 18,
    tags: ["少油", "香煎"],
    steps: (names) => [
      `${names[0]}用黑胡椒和盐轻轻抓匀。`,
      `平底锅少油煎熟${names[0]}，旁边放入${names.slice(1).join("、") || names[0]}煎到变软。`,
      "出锅前用少量生抽提味。"
    ]
  },
  {
    suffix: "焖煮锅",
    minutes: 25,
    tags: ["饱腹", "焖煮"],
    steps: (names) => [
      `锅里少油，先让${names[0]}表面定型。`,
      `加入${names.slice(1).join("、") || names[0]}和少量水，盖盖焖到软熟。`,
      "收汁后用盐或蚝油简单调味。"
    ]
  }
]

function pickLocalGroup(names, round) {
  const clean = uniqueNames(names)
  if (clean.length < 2) return []
  const rotated = rotateNames(clean, round * 2)
  return rotated.slice(0, Math.min(3, rotated.length))
}

function estimateLocalNutrition(names, target, styleIndex) {
  const kcal = Math.max(300, Math.min(600, Number(target) || 500))
  const protein = names.some((name) => /鸡|蛋|牛|鱼|虾|豆腐|奶/.test(name)) ? 32 : 14
  const fat = styleIndex === 3 ? 16 : 10
  return { kcal, protein, fat }
}

function buildFallbackRecipes(request) {
  const source = Array.isArray(request && request.ingredients) ? request.ingredients : []
  const target = Number(request && request.targetCalories) || 500
  const prefs = Array.isArray(request && request.preferences) ? request.preferences : []
  const recipeRound = Number(request && request.recipeRound) || 0
  const names = pickLocalGroup(source, recipeRound)
  if (!names.length) {
    wx.showToast({
      title: "食材不足，建议补充蛋白质、碳水、蔬菜类食材",
      icon: "none"
    })
    return []
  }

  return LOCAL_STYLES.map((style, index) => {
    const nutrition = estimateLocalNutrition(names, target + (index - 2) * 20, index)
    return enrichRecipe({
      id: `local-${Date.now()}-${recipeRound}-${index + 1}`,
      name: `${names.slice(0, 2).join("")}${style.suffix}`,
      minutes: style.minutes,
      kcal: nutrition.kcal,
      protein: nutrition.protein,
      fat: nutrition.fat,
      tags: [...prefs.slice(0, 2), ...style.tags],
      ingredients: names.map((name, ingredientIndex) => ({
        name,
        amount: `${ingredientIndex === 0 ? 150 : ingredientIndex === 1 ? 180 : 120} g`
      })),
      steps: style.steps(names),
      description: "本地兜底生成，严格只使用已输入食材和基础调料。"
    })
  })
}

Page({
  data: {
    recipes: [],
    loading: false,
    summaryText: "\u7ea6500 kcal"
  },

  goBack() {
    navigateBackOrRedirect("/pages/food/input")
  },

  onShow() {
    const last = wx.getStorageSync("lastRecipeRequest")
    this.requestKey = last ? getRequestKey(last) : ""
    if (last) {
      this.setData({ summaryText: buildSummaryText(last) })
    }
    const cached = readCachedRecipes()
    const cachedKey = wx.getStorageSync("generatedRecipesRequestKey")
    if (cached.length && cachedKey && cachedKey === this.requestKey) {
      this.setData({ recipes: cached })
    }
    this.reloadRecipes()
  },

  reloadRecipes() {
    const last = wx.getStorageSync("lastRecipeRequest")
    if (!last) {
      const cached = readCachedRecipes()
      this.setData({ recipes: cached })
      return
    }

    this.requestKey = getRequestKey(last)
    this.setData({ summaryText: buildSummaryText(last) })
    wx.showLoading({ title: "更新中" })
    generateRecipes(last.ingredients || [], last.targetCalories, last.preferences || [], Number(last.recipeRound) || 0)
      .then((recipes) => {
        const data = recipes.map(enrichRecipe)
        wx.setStorageSync("generatedRecipes", data)
        wx.setStorageSync("generatedRecipesRequestKey", this.requestKey)
        this.setData({ recipes: data })
      })
      .catch(() => {
        const fallback = buildFallbackRecipes(last)
        wx.setStorageSync("generatedRecipes", fallback)
        wx.setStorageSync("generatedRecipesRequestKey", this.requestKey)
        this.setData({ recipes: fallback })
        wx.showToast({
          title: "后端未启动，已显示本地食谱",
          icon: "none"
        })
      })
      .finally(() => {
        wx.hideLoading()
      })
  },

  goDetail(event) {
    const id = event.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/food/detail?id=${id}`
    })
  },

  regenerate() {
    const last = wx.getStorageSync("lastRecipeRequest")
    if (!last) {
      wx.navigateTo({ url: "/pages/food/input" })
      return
    }
    const request = {
      ...last,
      recipeRound: (Number(last.recipeRound) || 0) + 1
    }
    request.requestKey = getRequestKey(request)
    wx.setStorageSync("lastRecipeRequest", request)
    this.setData({ summaryText: buildSummaryText(request) })

    wx.showLoading({ title: "生成中" })
    generateRecipes(request.ingredients || [], request.targetCalories, request.preferences || [], request.recipeRound)
      .then((recipes) => {
        const data = recipes.map(enrichRecipe)
        wx.setStorageSync("generatedRecipes", data)
        wx.setStorageSync("generatedRecipesRequestKey", request.requestKey)
        this.setData({ recipes: data })
      })
      .catch(() => {
        const fallback = buildFallbackRecipes(request)
        wx.setStorageSync("generatedRecipes", fallback)
        wx.setStorageSync("generatedRecipesRequestKey", request.requestKey)
        this.setData({ recipes: fallback })
        wx.showToast({
          title: "后端未启动，已显示本地食谱",
          icon: "none"
        })
      })
      .finally(() => {
        wx.hideLoading()
      })
  },

  onBottomNav(event) {
    const route = (event.currentTarget && event.currentTarget.dataset && event.currentTarget.dataset.route) ||
      (event.detail && event.detail.route)
    if (!route) return
    wx.redirectTo({
      url: route
    })
  }
})
