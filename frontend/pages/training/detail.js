const { getExerciseById, exerciseDetail } = require("../../utils/mock")
const { getExercise } = require("../../utils/api")
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


const DEFAULT_COVER = "/images/exercises/barbell-bench-press.png"

function buildFallbackExercise(id) {
  const exercise = getExerciseById(id || "bench")
  const detail = exerciseDetail[exercise.id] || {
    title: exercise.title,
    part: `${exercise.part || "训练"} · ${exercise.equipment || "徒手"}`,
    main: exercise.muscle || "目标肌群",
    assist: "核心稳定",
    steps: ["保持身体稳定，先用轻重量熟悉动作。", "按照动作轨迹完成目标次数。", "控制还原，避免借力。"],
    notes: "训练中如出现疼痛，请停止动作并降低强度。",
    coverSrc: exercise.coverSrc || DEFAULT_COVER
  }
  return {
    exercise,
    detail: {
      ...detail,
      coverSrc: detail.coverSrc || DEFAULT_COVER
    }
  }
}

Page({
  data: {
    exercise: getExerciseById("bench"),
    detail: {
      ...exerciseDetail.bench,
      coverSrc: DEFAULT_COVER
    }
  },

  onLoad(query) {
    const id = String(query.id || "bench")
    this.loadExercise(id)
  },

  loadExercise(id) {
    const fallback = buildFallbackExercise(id)
    this.setData(fallback)
    getExercise(id).then((remoteExercise) => {
      this.setData({
        exercise: remoteExercise,
        detail: remoteExercise.detail
      })
    }).catch(() => {})
  },

  goBack() {
    navigateBackOrRedirect("/pages/training/home")
  },

  startRecord() {
    wx.setStorageSync("currentWorkoutExercise", this.data.exercise)
    wx.navigateTo({
      url: "/pages/training/record"
    })
  },

  onBottomNav(event) {
    wx.redirectTo({
      url: event.detail.route
    })
  }
})
