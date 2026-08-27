const { bodyParts, trainingSummary } = require("../../utils/mock")
const { getWorkoutRecommendation, getWorkoutSessions } = require("../../utils/api")

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

Page({
  data: {
    bodyParts,
    summary: buildFallbackSummary(),
    recentExerciseId: "bench"
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
          recentExerciseId: String((recentSet && recentSet.exercise_id) || (recommendationExercises[0] && recommendationExercises[0].exercise_id) || "bench")
        })
        return
      }

      if (recommendation) {
        const nextExerciseId = recommendationExercises[0] && recommendationExercises[0].exercise_id || "bench"
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
          recentExerciseId: String(nextExerciseId)
        })
        return
      }

      this.setData({
        summary: buildFallbackSummary(),
        recentExerciseId: "bench"
      })
    }).catch(() => {
      this.setData({
        summary: buildFallbackSummary(),
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

  onBottomNav(event) {
    wx.redirectTo({
      url: event.detail.route
    })
  }
})
