const { recordWorkout } = require("../../utils/mock")
const { getExercise, createWorkoutSession, addWorkoutSet, completeWorkoutSession } = require("../../utils/api")
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


function cloneSets(sets) {
  return sets.map((item) => ({ ...item }))
}

function formatDuration(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`
}

function buildWorkoutFromExercise(exercise) {
  return {
    name: exercise && exercise.title || recordWorkout.name,
    part: exercise && exercise.detail && exercise.detail.main || exercise && exercise.muscle || recordWorkout.part,
    startedAt: new Date().toTimeString().slice(0, 5),
    kcal: exercise && exercise.kcal || recordWorkout.kcal
  }
}

Page({
  data: {
    workout: recordWorkout,
    sets: cloneSets(recordWorkout.sets),
    exercise: null,
    exerciseId: "",
    startedAtMs: 0,
    elapsedText: "00:00",
    completedCount: 2,
    progressPercent: 50,
    restSeconds: 0,
    restText: "01:00"
  },

  onLoad(query) {
    this.setData({ startedAtMs: Date.now() })
    this.sessionTimer = setInterval(() => {
      const seconds = Math.max(0, Math.floor((Date.now() - this.data.startedAtMs) / 1000))
      this.setData({ elapsedText: formatDuration(seconds) })
    }, 1000)
    const stored = wx.getStorageSync("currentWorkoutExercise") || {}
    const exerciseId = String(query.id || stored.id || "")
    if (!exerciseId || exerciseId === "bench") {
      this.setData({
        workout: recordWorkout,
        sets: cloneSets(recordWorkout.sets),
        exerciseId: exerciseId || ""
      })
      return
    }

    this.setData({ exerciseId })
    getExercise(exerciseId)
      .then((exercise) => {
        this.setData({
          exercise,
          workout: buildWorkoutFromExercise(exercise),
          sets: [
            { group: 1, weight: 20, reps: 12, done: true },
            { group: 2, weight: 25, reps: 10, done: true },
            { group: 3, weight: 25, reps: 10, done: false },
            { group: 4, weight: 25, reps: 8, done: false }
          ]
        })
      })
      .catch(() => {
        this.setData({
          workout: recordWorkout,
          sets: cloneSets(recordWorkout.sets)
        })
      })
  },

  onUnload() {
    clearInterval(this.sessionTimer)
    clearInterval(this.restTimer)
  },

  goBack() {
    if (this.data.completedCount < this.data.sets.length) {
      wx.showModal({
        title: "结束当前训练？",
        content: "未完成的训练数据不会保存。",
        confirmText: "退出",
        confirmColor: "#b44b32",
        success: (result) => {
          if (result.confirm) navigateBackOrRedirect("/pages/training/detail?id=" + (this.data.exerciseId || "bench"))
        }
      })
      return
    }
    navigateBackOrRedirect("/pages/training/detail?id=" + (this.data.exerciseId || "bench"))
  },

  toggleDone(event) {
    const index = event.currentTarget.dataset.index
    const sets = cloneSets(this.data.sets)
    sets[index].done = !sets[index].done
    this.updateSets(sets)
    if (sets[index].done) this.startRestTimer(60)
  },

  onWeightInput(event) {
    const sets = cloneSets(this.data.sets)
    sets[event.currentTarget.dataset.index].weight = event.detail.value
    this.updateSets(sets)
  },

  onRepsInput(event) {
    const sets = cloneSets(this.data.sets)
    sets[event.currentTarget.dataset.index].reps = event.detail.value
    this.updateSets(sets)
  },

  updateSets(sets) {
    const completedCount = sets.filter((item) => item.done).length
    const progressPercent = sets.length ? Math.round(completedCount / sets.length * 100) : 0
    this.setData({ sets, completedCount, progressPercent })
  },

  addSet() {
    const sets = cloneSets(this.data.sets)
    sets.push({
      group: sets.length + 1,
      weight: sets.length >= 2 ? sets[sets.length - 1].weight : 20,
      reps: 8,
      done: false
    })
    this.updateSets(sets)
  },

  startRestTimer(seconds) {
    clearInterval(this.restTimer)
    this.setData({ restSeconds: seconds, restText: formatDuration(seconds) })
    this.restTimer = setInterval(() => {
      const next = this.data.restSeconds - 1
      if (next <= 0) {
        clearInterval(this.restTimer)
        this.setData({ restSeconds: 0, restText: "01:00" })
        wx.vibrateShort({ type: "medium" })
        wx.showToast({ title: "休息结束", icon: "none" })
        return
      }
      this.setData({ restSeconds: next, restText: formatDuration(next) })
    }, 1000)
  },

  toggleRestTimer() {
    if (this.data.restSeconds) {
      clearInterval(this.restTimer)
      this.setData({ restSeconds: 0, restText: "01:00" })
      return
    }
    this.startRestTimer(60)
  },

  async finishWorkout() {
    const exercise = this.data.exercise
    if (!exercise) {
      wx.showToast({
        title: "后端未启动，已保留页面数据",
        icon: "none"
      })
      return
    }

    wx.showLoading({ title: "保存中" })
    try {
      const session = await createWorkoutSession({
        title: this.data.workout.name || exercise.title,
        duration_min: Math.max(1, Math.round((Date.now() - this.data.startedAtMs) / 60000))
      })

      for (const item of this.data.sets) {
        await addWorkoutSet(session.id, {
          exercise_id: Number(exercise.id),
          set_no: Number(item.group),
          weight_kg: Number(item.weight),
          reps: Number(item.reps),
          completed: !!item.done
        })
      }

      await completeWorkoutSession(session.id)
      wx.showToast({
        title: "训练已保存",
        icon: "success"
      })
      setTimeout(() => wx.redirectTo({ url: "/pages/training/home" }), 500)
    } catch (error) {
      wx.showToast({
        title: "后端未启动，已保留页面数据",
        icon: "none"
      })
    } finally {
      wx.hideLoading()
    }
  },

  onBottomNav(event) {
    wx.redirectTo({
      url: event.detail.route
    })
  }
})
