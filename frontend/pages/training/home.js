const { bodyParts, trainingSummary } = require("../../utils/mock")
const { getWorkoutRecommendation, getWorkoutSessions, getExerciseCover, createCardioSession } = require("../../utils/api")
const { getUser } = require("../../utils/user")

const CARDIO_MET = {
  "快走": 4.3,
  "坡度走": 5.3,
  "爬坡": 6.5,
  "椭圆机": 5.0,
  "骑行": 6.0,
  "慢跑": 7.0,
  "跑步": 8.0,
  "划船机": 7.0,
  "风阻单车": 7.5,
  "跳绳": 10,
  "游泳": 8,
  "蛙泳": 10.3,
  "自由泳": 8.3
}

const CARDIO_ALIASES = [
  ["蛙泳", "蛙泳"],
  ["自由泳", "自由泳"],
  ["游泳", "游泳"],
  ["爬坡", "爬坡"],
  ["坡度", "爬坡"],
  ["快走", "快走"],
  ["椭圆", "椭圆机"],
  ["骑行", "骑行"],
  ["单车", "骑行"],
  ["慢跑", "慢跑"],
  ["跑步", "跑步"],
  ["划船", "划船机"],
  ["跳绳", "跳绳"]
]

function formatDate(dateValue) {
  if (!dateValue) return "最近"
  const text = String(dateValue)
  const match = text.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  if (!match) return text
  return `${Number(match[2])} 月 ${Number(match[3])} 日`
}

function buildFallbackSummary() {
  return {
    ...trainingSummary,
    recentDate: trainingSummary.recent.date
  }
}

function buildFallbackPlan() {
  return {
    title: "减脂推荐训练",
    goalName: "减脂",
    description: "覆盖全身大肌群，在保留肌肉的前提下提高能量消耗",
    resistance: "以复合动作为主，动作质量优先。",
    cardio: {
      mode: "快走",
      modes: ["快走", "椭圆机", "骑行"],
      summary: "快走 / 椭圆机 / 骑行 · 每周 3-5 次 · 每次 25-40 分钟",
      notes: "能够说短句的强度即可。"
    },
    exercises: [
      {
        id: "bench",
        name: "杠铃卧推",
        coverSrc: "/images/exercises/barbell-bench-press.png",
        meta: "胸部 · 杠铃 · 中级",
        dose: "3-4组 · 8-12次 · 休息60秒",
        notes: "使用安全架并保持手腕中立"
      },
      {
        id: "plank",
        name: "平板支撑",
        coverSrc: "/images/exercises/forearm-plank.png",
        meta: "核心 · 徒手 · 初级",
        dose: "3组 · 40秒 · 休息30秒",
        notes: "保持自然呼吸和躯干稳定"
      }
    ]
  }
}

function getCardioMode(plan) {
  const cardio = plan && plan.cardio || {}
  if (cardio.mode) return cardio.mode
  if (Array.isArray(cardio.modes) && cardio.modes.length) return cardio.modes[0]
  return "快走"
}

function getDefaultMinutes(plan) {
  const text = plan && plan.cardio && plan.cardio.summary || ""
  const matches = text.match(/(\d+)-(\d+)\s*分钟/)
  if (matches) return Math.round((Number(matches[1]) + Number(matches[2])) / 2)
  return 30
}

function detectCardioMode(text, fallback) {
  const value = String(text || "")
  const found = CARDIO_ALIASES.find(([keyword]) => value.indexOf(keyword) >= 0)
  return found ? found[1] : fallback || "快走"
}

function formatCardioNumber(value) {
  return Number(value).toString()
}

function parseCardioSegments(input, fallbackMode, fallbackMinutes) {
  const text = String(input || "").trim()
  const segments = []
  const inclinePattern = /(?:爬坡|坡度走)?\s*坡度\s*(\d+(?:\.\d+)?)\s*(?:速度|时速)\s*(\d+(?:\.\d+)?)\s*(?:公里\/小时|km\/h|kmh)?\s*(\d+(?:\.\d+)?)\s*分钟/g
  let inclineMatch = inclinePattern.exec(text)
  while (inclineMatch) {
    const incline = Number(inclineMatch[1])
    const speed = Number(inclineMatch[2])
    const minutes = Math.round(Number(inclineMatch[3]))
    segments.push({
      mode: "爬坡",
      durationMin: minutes,
      inclinePercent: incline,
      speedKmh: speed,
      label: `坡度${formatCardioNumber(incline)}速度${formatCardioNumber(speed)} ${minutes}分钟`
    })
    inclineMatch = inclinePattern.exec(text)
  }
  if (segments.length) return segments

  const normalPattern = /(蛙泳|自由泳|游泳|快走|坡度走|爬坡|椭圆机|椭圆|骑行|慢跑|跑步|划船机|划船|风阻单车|跳绳)\s*(\d+(?:\.\d+)?)\s*分钟/g
  let normalMatch = normalPattern.exec(text)
  while (normalMatch) {
    const mode = detectCardioMode(normalMatch[1], fallbackMode)
    const minutes = Math.round(Number(normalMatch[2]))
    segments.push({
      mode,
      durationMin: minutes,
      label: `${mode}${minutes}分钟`
    })
    normalMatch = normalPattern.exec(text)
  }
  if (segments.length) return segments

  const timeMatch = text.match(/(\d+(?:\.\d+)?)\s*分钟/)
  if (timeMatch) {
    const minutes = Math.round(Number(timeMatch[1]))
    const mode = detectCardioMode(text, fallbackMode)
    return [{ mode, durationMin: minutes, label: `${mode}${minutes}分钟` }]
  }

  if (fallbackMinutes) {
    return [{ mode: fallbackMode || "快走", durationMin: fallbackMinutes, label: `${fallbackMode || "快走"}${fallbackMinutes}分钟` }]
  }

  return []
}

function cardioSegmentMet(segment) {
  if (segment.speedKmh && segment.inclinePercent !== undefined) {
    const metersPerMin = segment.speedKmh * 1000 / 60
    const vo2 = 0.1 * metersPerMin + 1.8 * metersPerMin * (segment.inclinePercent / 100) + 3.5
    return Math.max(3, vo2 / 3.5)
  }
  return CARDIO_MET[segment.mode] || 5
}

function estimateCardioCalories(user, segments) {
  const weight = Number(user.weight || user.current_weight_kg) || 60
  const height = Number(user.height || user.height_cm) || 165
  const heightFactor = Math.min(1.1, Math.max(0.95, height / 170))
  return Math.round(segments.reduce((total, segment) => {
    return total + cardioSegmentMet(segment) * 3.5 * weight / 200 * segment.durationMin * heightFactor
  }, 0))
}

function buildCardioEstimateText(input, plan) {
  const mode = getCardioMode(plan)
  const segments = parseCardioSegments(input, mode, 0)
  if (!segments.length) return "请输入有氧方式和时间"
  const minutes = segments.reduce((total, segment) => total + segment.durationMin, 0)
  const kcal = estimateCardioCalories(getUser(), segments)
  return `${segments.map((segment) => segment.label).join(" + ")}，共 ${minutes} 分钟，预计消耗约 ${kcal} kcal`
}

function normalizePlanExercise(item) {
  const rest = item.rest_seconds ? `休息${item.rest_seconds}秒` : "按状态休息"
  return {
    id: String(item.exercise_id || item.id || ""),
    name: item.name || item.title || "训练动作",
    coverSrc: getExerciseCover({
      name: item.name || item.title,
      body_part: item.body_part,
      thumbnail_url: item.thumbnail_url,
      equipment: item.equipment
    }),
    meta: `${item.body_part || "训练"} · ${item.equipment || "徒手"} · ${item.difficulty || "新手"}`,
    dose: `${item.sets || "3组"} · ${item.reps || "10-12次"} · ${rest}`,
    notes: item.notes || item.movement_pattern || ""
  }
}

function normalizePlan(recommendation) {
  if (!recommendation) return buildFallbackPlan()
  const cardio = recommendation.cardio || {}
  const modeList = Array.isArray(cardio.modes) && cardio.modes.length ? cardio.modes : ["快走", "骑行"]
  const modes = modeList.join(" / ")
  return {
    title: recommendation.title || "定制训练计划",
    goalName: recommendation.goal && recommendation.goal.name || "训练",
    description: recommendation.goal && recommendation.goal.description || "",
    resistance: recommendation.principles && recommendation.principles.resistance || "",
    cardio: {
      mode: modeList[0],
      modes: modeList,
      summary: `${modes} · 每周 ${cardio.sessions_per_week || "2-3次"} · 每次 ${cardio.minutes_per_session || "20-40分钟"}`,
      notes: cardio.notes || recommendation.safety_note || ""
    },
    exercises: (recommendation.exercises || []).map(normalizePlanExercise)
  }
}

Page({
  data: {
    bodyParts,
    summary: buildFallbackSummary(),
    plan: buildFallbackPlan(),
    recentExerciseId: "bench",
    showCardioModal: false,
    cardioInput: "",
    cardioEstimateText: "",
    savingCardio: false
  },

  onShow() {
    this.loadSummary()
  },

  loadSummary() {
    Promise.all([
      getWorkoutRecommendation().catch(() => null),
      getWorkoutSessions().catch(() => [])
    ]).then(([recommendation, sessions]) => {
      const latest = Array.isArray(sessions) && sessions.length ? sessions[0] : null
      const recommendationExercises = recommendation && recommendation.exercises ? recommendation.exercises : []
      if (latest) {
        const recentSet = latest.sets && latest.sets[0]
        const plan = normalizePlan(recommendation)
        this.setData({
          summary: {
            focus: latest.title || (recommendation && recommendation.title) || trainingSummary.focus,
            moves: latest.sets ? latest.sets.length : recommendationExercises.length || trainingSummary.moves,
            minutes: latest.duration_min || (recommendation && recommendation.estimated_duration_min) || trainingSummary.minutes,
            recent: {
              title: latest.title || trainingSummary.recent.title,
              date: formatDate(latest.workout_date),
              detail: `${latest.sets ? latest.sets.length : 0} 个动作 · ${latest.duration_min || 0} 分钟 · ${Math.round(latest.calories_kcal || 0)} kcal`
            },
            recentDate: formatDate(latest.workout_date)
          },
          plan,
          recentExerciseId: String((recentSet && recentSet.exercise_id) || (recommendationExercises[0] && recommendationExercises[0].exercise_id) || "bench")
        })
        return
      }

      if (recommendation) {
        const nextExerciseId = recommendationExercises[0] && recommendationExercises[0].exercise_id || "bench"
        const plan = normalizePlan(recommendation)
        this.setData({
          summary: {
            focus: recommendation.title || trainingSummary.focus,
            moves: recommendationExercises.length || trainingSummary.moves,
            minutes: recommendation.estimated_duration_min || trainingSummary.minutes,
            recent: {
              title: recommendation.title || trainingSummary.recent.title,
              date: "今天",
              detail: `${recommendationExercises.length || 0} 个动作 · 计划训练`
            },
            recentDate: "今天"
          },
          plan,
          recentExerciseId: String(nextExerciseId)
        })
        return
      }

      this.setData({
        summary: buildFallbackSummary(),
        plan: buildFallbackPlan(),
        recentExerciseId: "bench"
      })
    }).catch(() => {
      this.setData({
        summary: buildFallbackSummary(),
        plan: buildFallbackPlan(),
        recentExerciseId: "bench"
      })
    })
  },

  openList(event) {
    const part = event.currentTarget.dataset.part || "chest"
    wx.navigateTo({
      url: `/pages/training/list?part=${part}`
    })
  },

  openRecent() {
    wx.navigateTo({
      url: `/pages/training/detail?id=${this.data.recentExerciseId || "bench"}`
    })
  },

  openPlanExercise(event) {
    const id = event.currentTarget.dataset.id
    if (!id) return
    wx.navigateTo({
      url: `/pages/training/detail?id=${id}`
    })
  },

  openCardio() {
    const minutes = getDefaultMinutes(this.data.plan)
    const mode = getCardioMode(this.data.plan)
    const input = `${mode}${minutes}分钟`
    this.setData({
      showCardioModal: true,
      cardioInput: input,
      cardioEstimateText: buildCardioEstimateText(input, this.data.plan)
    })
  },

  closeCardio() {
    if (this.data.savingCardio) return
    this.setData({ showCardioModal: false })
  },

  noop() {},

  onCardioInput(event) {
    const input = event.detail.value
    this.setData({
      cardioInput: input,
      cardioEstimateText: buildCardioEstimateText(input, this.data.plan)
    })
  },

  saveCardio() {
    const input = String(this.data.cardioInput || "").trim()
    const segments = parseCardioSegments(input, getCardioMode(this.data.plan), 0)
    if (!segments.length) {
      wx.showToast({ title: "请输入方式和时间", icon: "none" })
      return
    }
    this.setData({ savingCardio: true })
    createCardioSession({
      detail: input
    }).then((session) => {
      wx.showToast({
        title: `消耗 ${Math.round(session.calories_kcal || 0)} kcal`,
        icon: "none"
      })
      this.setData({
        showCardioModal: false,
        savingCardio: false
      })
      this.loadSummary()
    }).catch(() => {
      const kcal = estimateCardioCalories(getUser(), segments)
      wx.showToast({
        title: `后端未启动，估算 ${kcal} kcal`,
        icon: "none"
      })
      this.setData({ savingCardio: false })
    })
  },

  onBottomNav(event) {
    wx.redirectTo({
      url: event.detail.route
    })
  }
})
