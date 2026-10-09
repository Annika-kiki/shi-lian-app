const { recordWorkout } = require("../../utils/mock")
const { ensureLogin, request, showApiError } = require("../../utils/api")
const { navigationBehavior } = require("../../utils/navigation")

Page({
  behaviors: [navigationBehavior],
  data: {
    workout: recordWorkout,
    sets: [],
    exerciseId: 1,
    startedAtMs: 0
  },

  async onLoad(query) {
    const exerciseId = Number(query.id || 1)
    this.setData({
      exerciseId,
      startedAtMs: Date.now(),
      sets: recordWorkout.sets.map((item) => ({ ...item }))
    })
    try {
      const exercise = await request(`/api/exercises/${exerciseId}`)
      this.setData({ workout: { ...recordWorkout, name: exercise.name, part: exercise.body_part } })
    } catch (error) { showApiError(error) }
  },

  toggleDone(event) {
    const index = event.currentTarget.dataset.index
    const sets = this.data.sets.slice()
    sets[index].done = !sets[index].done
    this.setData({ sets })
  },

  addSet() {
    const sets = this.data.sets.slice()
    sets.push({
      group: sets.length + 1,
      weight: 20,
      reps: 8,
      done: false
    })
    this.setData({ sets })
  },

  async finishWorkout() {
    wx.showLoading({ title: "保存训练" })
    try {
      await ensureLogin()
      const duration = Math.max(1, Math.round((Date.now() - this.data.startedAtMs) / 60000))
      const session = await request("/api/workouts/sessions", { method: "POST", data: { title: this.data.workout.name, duration_min: duration } })
      for (const item of this.data.sets) {
        await request(`/api/workouts/sessions/${session.id}/sets`, { method: "POST", data: { exercise_id: this.data.exerciseId, set_no: item.group, weight_kg: Number(item.weight), reps: Number(item.reps), completed: item.done } })
      }
      await request(`/api/workouts/sessions/${session.id}/complete`, { method: "POST" })
      wx.showToast({ title: "训练已完成", icon: "success" })
      setTimeout(() => wx.redirectTo({ url: "/pages/training/home" }), 300)
    } catch (error) { showApiError(error) }
    finally { wx.hideLoading() }
  },

  onBottomNav(event) {
    wx.redirectTo({
      url: event.detail.route
    })
  }
})
