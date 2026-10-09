const { bodyParts, trainingSummary } = require("../../utils/mock")
const { ensureLogin, request, showApiError } = require("../../utils/api")
const { catalog } = require("../../utils/exercises")
const { navigationBehavior } = require("../../utils/navigation")

Page({
  behaviors: [navigationBehavior],
  data: {
    bodyParts,
    summary: {
      ...trainingSummary,
      recentDate: trainingSummary.recent.date
    },
    recommendedExerciseId: "barbell-bench-press"
  },

  async onShow() {
    try {
      await ensureLogin()
      const [recommendation, sessions] = await Promise.all([request("/api/workouts/recommendation"), request("/api/workouts/sessions")])
      const recent = sessions[0]
      this.setData({
        recommendedExerciseId: recommendation.exercises[0] ? ((catalog.find((item) => item.name === recommendation.exercises[0].name) || {}).slug || recommendation.exercises[0].exercise_id) : "barbell-bench-press",
        summary: {
          ...this.data.summary,
          focus: recommendation.title,
          moves: recommendation.exercises.length,
          minutes: recommendation.estimated_duration_min,
          recent: recent ? { title: recent.title, detail: `${recent.duration_min || 0} 分钟 · ${recent.status}` } : { title: "暂无训练记录", detail: "完成第一次训练吧" },
          recentDate: recent ? String(recent.workout_date).slice(5) : ""
        }
      })
    } catch (error) { showApiError(error) }
  },

  openList(event) {
    const part = event.currentTarget.dataset.part || "chest"
    wx.navigateTo({
      url: `/pages/training/list?part=${part}`
    })
  },

  openRecent() {
    wx.navigateTo({
      url: `/pages/training/detail?id=${this.data.recommendedExerciseId}`
    })
  },

  onBottomNav(event) {
    wx.redirectTo({
      url: event.detail.route
    })
  }
})
