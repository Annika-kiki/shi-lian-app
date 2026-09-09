const { bodyParts } = require("../../utils/mock")
const { getWorkoutRecommendation, getWorkoutSessions } = require("../../utils/api")

function formatDate(dateValue) {
  if (!dateValue) return ""
  const text = String(dateValue)
  const match = text.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  return match ? `${Number(match[2])} 月 ${Number(match[3])} 日` : text
}

Page({
  data: {
    bodyParts,
    recommendation: null,
    recent: null,
    startExerciseId: "",
    loading: true,
    loadError: false
  },

  onShow() {
    this.loadSummary()
  },

  loadSummary() {
    this.setData({ loading: true, loadError: false })
    Promise.all([getWorkoutRecommendation(), getWorkoutSessions()])
      .then(([recommendation, sessions]) => {
        const exercises = recommendation.exercises || []
        const latest = Array.isArray(sessions) && sessions.length ? sessions[0] : null
        const latestSet = latest && latest.sets && latest.sets[0]
        this.setData({
          recommendation: {
            focus: recommendation.title || "今日训练建议",
            moves: exercises.length,
            minutes: recommendation.estimated_duration_min || 0
          },
          recent: latest ? {
            title: latest.title || "训练记录",
            date: formatDate(latest.workout_date),
            detail: `${latest.sets ? latest.sets.length : 0} 组 · ${latest.duration_min || 0} 分钟 · ${Math.round(latest.calories_kcal || 0)} kcal`
          } : null,
          startExerciseId: String((exercises[0] && exercises[0].exercise_id) || (latestSet && latestSet.exercise_id) || ""),
          loading: false
        })
      })
      .catch((error) => {
        this.setData({ recommendation: null, recent: null, loading: false, loadError: true })
        wx.showToast({ title: error.message || "训练数据加载失败", icon: "none" })
      })
  },

  openList(event) {
    const part = event.currentTarget.dataset.part || "chest"
    wx.navigateTo({ url: `/pages/training/list?part=${part}` })
  },

  startRecommendation() {
    if (!this.data.startExerciseId) {
      wx.showToast({ title: "暂无可用训练动作", icon: "none" })
      return
    }
    wx.navigateTo({ url: `/pages/training/detail?id=${this.data.startExerciseId}` })
  },

  onBottomNav(event) {
    wx.redirectTo({ url: event.detail.route })
  }
})
