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


const DEFAULT_COVER = "/assets/exercises/barbell-bench-press.png"

function buildFallbackExercise(id) {
  const exercise = getExerciseById(id || "bench")
  const detail = exerciseDetail[exercise.id] || exerciseDetail.bench
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
